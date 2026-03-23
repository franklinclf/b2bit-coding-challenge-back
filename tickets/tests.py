from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from movies.models import Movie
from showings.models import MovieSession, Seat
from showings.services import SeatLockService
from .models import Ticket

User = get_user_model()


class TicketCheckoutAPITestCase(APITestCase):
	def setUp(self):
		self.user = User.objects.create_user(email='buyer@example.com', username='buyer', password='StrongPass123!')
		refresh = RefreshToken.for_user(self.user)
		self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

		self.movie = Movie.objects.create(
			title='The Matrix',
			description='Cyberpunk action',
			duration_minutes=136,
			genre='Sci-Fi',
			rating='R',
			release_date=timezone.now().date(),
		)
		self.session = MovieSession.objects.create(
			movie=self.movie,
			screen_number=5,
			start_time=timezone.now() + timedelta(hours=4),
			end_time=timezone.now() + timedelta(hours=6, minutes=30),
			total_seats=10,
			available_seats=10,
		)
		self.seat = Seat.objects.create(session=self.session, row='C', number=7)

	def test_checkout_creates_ticket(self):
		success, _ = SeatLockService.lock_seat(self.session.id, self.seat.id, self.user.id)
		self.assertTrue(success)

		response = self.client.post('/api/tickets/checkout/', {
			'session_id': self.session.id,
			'seat_ids': [self.seat.id],
		}, format='json')

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(Ticket.objects.filter(user=self.user, seat=self.seat).count(), 1)
		self.seat.refresh_from_db()
		self.assertEqual(self.seat.status, 'purchased')

	def test_my_tickets_filters_active_and_history(self):
		upcoming_session = self.session
		past_session = MovieSession.objects.create(
			movie=self.movie,
			screen_number=6,
			start_time=timezone.now() - timedelta(days=2),
			end_time=timezone.now() - timedelta(days=2, hours=-2),
			total_seats=10,
			available_seats=9,
		)
		seat_upcoming = self.seat
		seat_past = Seat.objects.create(session=past_session, row='D', number=1, status='purchased', purchased_by=self.user)

		Ticket.objects.create(user=self.user, session=upcoming_session, seat=seat_upcoming)
		Ticket.objects.create(user=self.user, session=past_session, seat=seat_past)

		active_response = self.client.get('/api/tickets/my-tickets/?type=active')
		history_response = self.client.get('/api/tickets/my-tickets/?type=history')

		self.assertEqual(active_response.status_code, status.HTTP_200_OK)
		self.assertEqual(history_response.status_code, status.HTTP_200_OK)
		self.assertEqual(active_response.data['count'], 1)
		self.assertEqual(history_response.data['count'], 1)
