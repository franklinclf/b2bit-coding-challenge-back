from django.conf import settings
from django.db import models

from movies.models import Movie


class MovieSession(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='sessions')
    screen_number = models.PositiveIntegerField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    total_seats = models.PositiveIntegerField()
    available_seats = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_time']

    def __str__(self):
        return f"{self.movie.title} - Screen {self.screen_number} at {self.start_time}"


class Seat(models.Model):
    session = models.ForeignKey(MovieSession, on_delete=models.CASCADE, related_name='seats')
    row = models.CharField(max_length=5)
    number = models.PositiveIntegerField()
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('reserved', 'Reserved'),
        ('purchased', 'Purchased'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='available')
    reserved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reserved_seats'
    )
    reserved_at = models.DateTimeField(null=True, blank=True)
    purchased_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='purchased_seats'
    )
    purchased_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['session', 'row', 'number']
        ordering = ['row', 'number']

    def __str__(self):
        return f"Seat {self.row}{self.number} - {self.session}"
