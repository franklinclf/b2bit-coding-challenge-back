import uuid

from django.conf import settings
from django.db import models

from showings.models import MovieSession, Seat


class Ticket(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tickets')
    session = models.ForeignKey(MovieSession, on_delete=models.CASCADE, related_name='tickets')
    seat = models.OneToOneField(Seat, on_delete=models.CASCADE, related_name='ticket')
    booking_time = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Ticket {self.id} - {self.user.email} - {self.session}"


class Reservation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reservations')
    session = models.ForeignKey(MovieSession, on_delete=models.CASCADE, related_name='reservations')
    seats = models.ManyToManyField(Seat, related_name='reservations')
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Reservation {self.id} - {self.user.email} - {self.session}"
