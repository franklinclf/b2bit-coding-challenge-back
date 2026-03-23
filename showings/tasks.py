from celery import shared_task

from .services import SeatLockService


@shared_task
def cleanup_expired_seat_locks_task():
    SeatLockService.cleanup_expired_locks()
    return 'Limpeza de locks expirados concluida'

