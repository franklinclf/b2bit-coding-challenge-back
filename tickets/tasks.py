from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from .models import Ticket


@shared_task
def send_ticket_confirmation_email_task(user_id, ticket_ids):
    tickets = Ticket.objects.filter(id__in=ticket_ids, user_id=user_id).select_related('session', 'seat')
    if not tickets.exists():
        return 'Nenhum ticket encontrado'

    user_email = tickets.first().user.email
    lines = ['Seus tickets CineReserve foram confirmados:', '']
    for ticket in tickets:
        lines.append(
            f"- Ticket {ticket.id} | Sessao {ticket.session.id} | Assento {ticket.seat.row}{ticket.seat.number}"
        )

    send_mail(
        subject='CineReserve - Confirmacao de Ticket',
        message='\n'.join(lines),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user_email],
        fail_silently=True,
    )
    return f'Email de confirmacao enviado para {user_email}'

