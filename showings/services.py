import json
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .models import Seat


class SeatLockService:
    LOCK_TIMEOUT = settings.SEAT_LOCK_TIMEOUT_SECONDS
    
    @staticmethod
    def get_lock_key(session_id, seat_id):
        return f"seat_lock:{session_id}:{seat_id}"
    
    @staticmethod
    def get_reservation_key(reservation_id):
        return f"reservation:{reservation_id}"
    
    @classmethod
    def lock_seat(cls, session_id, seat_id, user_id):
        lock_key = cls.get_lock_key(session_id, seat_id)
        
        # Check if seat is already locked
        existing_lock = cache.get(lock_key)
        if existing_lock:
            lock_data = json.loads(existing_lock)
            if lock_data['user_id'] == user_id:
                return True, 'Assento ja reservado por este usuario'
            return False, 'Assento ja reservado por outro usuario'
        
        # Try to acquire lock
        lock_data = {
            'user_id': user_id,
            'locked_at': timezone.now().isoformat(),
            'expires_at': (timezone.now() + timedelta(seconds=cls.LOCK_TIMEOUT)).isoformat()
        }
        
        success = cache.add(lock_key, json.dumps(lock_data), cls.LOCK_TIMEOUT)
        
        if success:
            try:
                with transaction.atomic():
                    seat = Seat.objects.select_for_update().get(id=seat_id, session_id=session_id)
                    if seat.status == 'available':
                        seat.status = 'reserved'
                        seat.reserved_by_id = user_id
                        seat.reserved_at = timezone.now()
                        seat.save(update_fields=['status', 'reserved_by', 'reserved_at'])
                        return True, 'Assento reservado com sucesso'

                    cache.delete(lock_key)
                    return False, 'Assento indisponivel'
            except Seat.DoesNotExist:
                cache.delete(lock_key)
                return False, 'Assento nao encontrado'
        
        return False, 'Nao foi possivel adquirir o lock'
    
    @classmethod
    def release_seat_lock(cls, session_id, seat_id, user_id=None):
        lock_key = cls.get_lock_key(session_id, seat_id)
        
        if user_id:
            # Check if lock belongs to the user
            existing_lock = cache.get(lock_key)
            if existing_lock:
                lock_data = json.loads(existing_lock)
                if lock_data['user_id'] != user_id:
                    return False, 'O lock pertence a outro usuario'
        
        # Remove lock from cache
        cache.delete(lock_key)
        
        try:
            with transaction.atomic():
                seat = Seat.objects.select_for_update().get(id=seat_id, session_id=session_id)
                if seat.status == 'reserved' and (user_id is None or seat.reserved_by_id == user_id):
                    seat.status = 'available'
                    seat.reserved_by = None
                    seat.reserved_at = None
                    seat.save(update_fields=['status', 'reserved_by', 'reserved_at'])
                    return True, 'Lock liberado com sucesso'
        except Seat.DoesNotExist:
            pass
        
        return True, 'Lock liberado'
    
    @classmethod
    def purchase_seat(cls, session_id, seat_id, user_id):
        lock_key = cls.get_lock_key(session_id, seat_id)
        
        # Check if user has lock on this seat
        existing_lock = cache.get(lock_key)
        if not existing_lock:
            return False, 'Nenhum lock encontrado para este assento'
        
        lock_data = json.loads(existing_lock)
        if lock_data['user_id'] != user_id:
            return False, 'O lock pertence a outro usuario'
        
        # Update seat status to purchased
        try:
            with transaction.atomic():
                seat = Seat.objects.select_for_update().select_related('session').get(id=seat_id, session_id=session_id)
                if seat.status == 'reserved' and seat.reserved_by_id == user_id:
                    seat.status = 'purchased'
                    seat.purchased_by_id = user_id
                    seat.purchased_at = timezone.now()
                    seat.save(update_fields=['status', 'purchased_by', 'purchased_at'])
                    seat.session.available_seats = F('available_seats') - 1
                    seat.session.save(update_fields=['available_seats'])

                    # Remove lock after successful purchase transition.
                    cache.delete(lock_key)
                    return True, 'Assento comprado com sucesso'

                return False, 'Assento nao esta no estado reservado'
        except Seat.DoesNotExist:
            return False, 'Assento nao encontrado'
    
    @classmethod
    def get_seat_status(cls, session_id, seat_id):
        lock_key = cls.get_lock_key(session_id, seat_id)
        
        try:
            seat = Seat.objects.get(id=seat_id, session_id=session_id)
            seat_status = seat.status
            
            # Check if there's an active lock
            lock_data = cache.get(lock_key)
            if lock_data:
                lock_info = json.loads(lock_data)
                return {
                    'status': seat_status,
                    'is_locked': True,
                    'locked_by': lock_info['user_id'],
                    'locked_at': lock_info['locked_at'],
                    'expires_at': lock_info['expires_at']
                }
            else:
                return {
                    'status': seat_status,
                    'is_locked': False
                }
        except Seat.DoesNotExist:
            return None
    
    @classmethod
    def cleanup_expired_locks(cls):
        # Reset seats stuck as reserved without an active Redis lock.
        reserved_seats = Seat.objects.filter(status='reserved').select_related('session')

        for seat in reserved_seats:
            lock_key = cls.get_lock_key(seat.session_id, seat.id)
            lock_data = cache.get(lock_key)

            if not lock_data:
                with transaction.atomic():
                    seat.status = 'available'
                    seat.reserved_by = None
                    seat.reserved_at = None
                    seat.save(update_fields=['status', 'reserved_by', 'reserved_at'])

    @classmethod
    def release_session_locks_for_user(cls, session_id, user_id):
        user_reserved_seats = Seat.objects.filter(
            session_id=session_id,
            status='reserved',
            reserved_by_id=user_id,
        ).values_list('id', flat=True)
        for seat_id in user_reserved_seats:
            cls.release_seat_lock(session_id=session_id, seat_id=seat_id, user_id=user_id)
