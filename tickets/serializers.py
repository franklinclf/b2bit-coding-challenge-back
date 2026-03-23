from rest_framework import serializers

from showings.serializers import MovieSessionSerializer, SeatSerializer
from users.serializers import UserSerializer
from .models import Ticket, Reservation


class TicketSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    session = MovieSessionSerializer(read_only=True)
    seat = SeatSerializer(read_only=True)
    
    class Meta:
        model = Ticket
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class ReservationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    session = MovieSessionSerializer(read_only=True)
    seats = SeatSerializer(many=True, read_only=True)
    
    class Meta:
        model = Reservation
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class CheckoutSerializer(serializers.Serializer):
    session_id = serializers.IntegerField()
    seat_ids = serializers.ListField(child=serializers.IntegerField())
