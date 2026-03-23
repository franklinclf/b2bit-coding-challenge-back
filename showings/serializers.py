from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from movies.serializers import MovieSerializer
from .models import MovieSession, Seat


class MovieSessionSerializer(serializers.ModelSerializer):
    movie = MovieSerializer(read_only=True)
    movie_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = MovieSession
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class SeatSerializer(serializers.ModelSerializer):
    seat_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Seat
        fields = ('id', 'row', 'number', 'status', 'seat_status')
    
    @extend_schema_field(serializers.JSONField)
    def get_seat_status(self, obj):
        from .services import SeatLockService
        status_info = SeatLockService.get_seat_status(obj.session_id, obj.id)
        if status_info:
            return {
                'status': status_info['status'],
                'is_locked': status_info['is_locked'],
                'locked_by': status_info.get('locked_by'),
                'expires_at': status_info.get('expires_at')
            }
        return {'status': obj.status, 'is_locked': False}


class SeatMapSerializer(serializers.ModelSerializer):
    seats = SeatSerializer(many=True, read_only=True)
    
    class Meta:
        model = MovieSession
        fields = ('id', 'movie', 'screen_number', 'start_time', 'end_time', 
                 'total_seats', 'available_seats', 'price', 'seats')
