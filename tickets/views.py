from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from showings.models import Seat, MovieSession
from showings.services import SeatLockService
from .models import Ticket
from .serializers import TicketSerializer, CheckoutSerializer
from .tasks import send_ticket_confirmation_email_task


def _apply_scope(request, scope_name):
    request.throttle_scope = scope_name
    throttle = ScopedRateThrottle()
    if not throttle.allow_request(request, None):
        wait = throttle.wait() or 60
        return Response(
            {'detail': 'Muitas requisicoes. Tente novamente em instantes.'},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
            headers={'Retry-After': str(int(wait))}
        )
    return None


@extend_schema(tags=['Tickets'], summary='Listar meus tickets (ativos ou historico)')
class UserTicketListView(generics.ListAPIView):
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Ticket.objects.filter(user=self.request.user).select_related('session', 'seat', 'user')
        ticket_type = self.request.query_params.get('type', '').lower()
        now = timezone.now()

        if ticket_type == 'active':
            queryset = queryset.filter(session__start_time__gte=now)
        elif ticket_type == 'history':
            queryset = queryset.filter(session__start_time__lt=now)
        return queryset


@extend_schema(
    tags=['Tickets'],
    summary='Finalizar reserva e gerar tickets',
    request=CheckoutSerializer,
    responses={201: OpenApiResponse(description='Compra concluida com sucesso')},
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def checkout(request):
    throttled_response = _apply_scope(request, 'checkout')
    if throttled_response:
        return throttled_response

    serializer = CheckoutSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    session_id = serializer.validated_data['session_id']
    seat_ids = serializer.validated_data['seat_ids']
    
    try:
        with transaction.atomic():
            session = get_object_or_404(MovieSession.objects.select_for_update(), id=session_id)
            tickets = []
            
            for seat_id in seat_ids:
                seat = get_object_or_404(Seat.objects.select_for_update(), id=seat_id, session=session)

                if Ticket.objects.filter(seat=seat).exists():
                    return Response(
                        {'error': f'O assento {seat_id} ja possui ticket associado.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Purchase the seat using the lock service
                success, message = SeatLockService.purchase_seat(
                    session_id=session_id,
                    seat_id=seat_id,
                    user_id=request.user.id
                )
                
                if not success:
                    return Response(
                        {'error': f'Falha ao comprar assento {seat_id}: {message}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Create ticket
                ticket = Ticket.objects.create(
                    user=request.user,
                    session=session,
                    seat=seat
                )
                tickets.append(ticket)

            # Dispatch only after commit so worker can query committed tickets.
            purchased_ticket_ids = [str(ticket.id) for ticket in tickets]
            transaction.on_commit(
                lambda: send_ticket_confirmation_email_task.delay(request.user.id, purchased_ticket_ids)
            )
            
            # Serialize and return tickets
            ticket_serializer = TicketSerializer(tickets, many=True)
            return Response({
                'message': 'Compra finalizada com sucesso',
                'tickets': ticket_serializer.data
            }, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
