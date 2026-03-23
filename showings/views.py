from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from rest_framework import generics, permissions, status
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from .models import MovieSession
from .serializers import MovieSessionSerializer, SeatMapSerializer
from .services import SeatLockService


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


@method_decorator(cache_page(settings.SESSIONS_LIST_CACHE_TTL), name='dispatch')
@extend_schema(tags=['Sessoes'], summary='Listar sessoes de filmes')
class MovieSessionListView(generics.ListAPIView):
    serializer_class = MovieSessionSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        movie_id = self.kwargs.get('movie_id')
        if movie_id:
            return MovieSession.objects.filter(movie_id=movie_id)
        return MovieSession.objects.all()


@extend_schema(tags=['Sessoes'], summary='Detalhar sessao')
class MovieSessionDetailView(generics.RetrieveAPIView):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer
    permission_classes = [permissions.AllowAny]


@extend_schema(
    tags=['Sessoes'],
    summary='Visualizar mapa de assentos da sessao',
    responses={200: SeatMapSerializer},
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def seat_map(request, session_id):
    session = get_object_or_404(MovieSession, id=session_id)
    serializer = SeatMapSerializer(session)
    return Response(serializer.data)


@extend_schema(
    tags=['Reservas'],
    summary='Reservar assento (lock temporario)',
    request=None,
    responses={
        200: inline_serializer(
            name='SeatReserveSuccessResponse',
            fields={'message': serializers.CharField()},
        )
    },
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def reserve_seat(request, session_id, seat_id):
    throttled_response = _apply_scope(request, 'seat_reservation')
    if throttled_response:
        return throttled_response

    success, message = SeatLockService.lock_seat(
        session_id=session_id,
        seat_id=seat_id,
        user_id=request.user.id
    )
    
    if success:
        return Response({'message': message}, status=status.HTTP_200_OK)
    else:
        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Reservas'],
    summary='Liberar assento reservado',
    request=None,
    responses={
        200: inline_serializer(
            name='SeatReleaseSuccessResponse',
            fields={'message': serializers.CharField()},
        )
    },
)
@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def release_seat(request, session_id, seat_id):
    throttled_response = _apply_scope(request, 'seat_reservation')
    if throttled_response:
        return throttled_response

    success, message = SeatLockService.release_seat_lock(
        session_id=session_id,
        seat_id=seat_id,
        user_id=request.user.id
    )
    
    if success:
        return Response({'message': message}, status=status.HTTP_200_OK)
    else:
        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)
