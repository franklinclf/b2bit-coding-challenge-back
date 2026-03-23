from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from movies.models import Movie
from showings.models import MovieSession, Seat
from showings.services import SeatLockService

User = get_user_model()


class SeatLockServiceTestCase(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(email='locker@example.com', username='locker', password='StrongPass123!')
		self.movie = Movie.objects.create(
			title='Interstellar',
			description='Sci-fi',
			duration_minutes=169,
			genre='Sci-Fi',
			rating='PG-13',
			release_date=timezone.now().date(),
		)
		self.session = MovieSession.objects.create(
			movie=self.movie,
			screen_number=1,
			start_time=timezone.now() + timedelta(hours=2),
			end_time=timezone.now() + timedelta(hours=5),
			total_seats=2,
			available_seats=2,
		)
		self.seat = Seat.objects.create(session=self.session, row='A', number=1)

	def test_lock_and_release_seat(self):
		success, _ = SeatLockService.lock_seat(self.session.id, self.seat.id, self.user.id)
		self.assertTrue(success)
		self.seat.refresh_from_db()
		self.assertEqual(self.seat.status, 'reserved')

		released, _ = SeatLockService.release_seat_lock(self.session.id, self.seat.id, self.user.id)
		self.assertTrue(released)
		self.seat.refresh_from_db()
		self.assertEqual(self.seat.status, 'available')

	def test_cleanup_expired_locks_resets_stale_reserved_seat(self):
		self.seat.status = 'reserved'
		self.seat.reserved_by = self.user
		self.seat.reserved_at = timezone.now()
		self.seat.save(update_fields=['status', 'reserved_by', 'reserved_at'])

		SeatLockService.cleanup_expired_locks()
		self.seat.refresh_from_db()
		self.assertEqual(self.seat.status, 'available')
		self.assertIsNone(self.seat.reserved_by)


class ShowingsAPITestCase(APITestCase):
	def setUp(self):
		self.user = User.objects.create_user(email='apiuser@example.com', username='apiuser', password='StrongPass123!')
		refresh = RefreshToken.for_user(self.user)
		self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

		self.movie = Movie.objects.create(
			title='Dune',
			description='Epic sci-fi',
			duration_minutes=155,
			genre='Sci-Fi',
			rating='PG-13',
			release_date=timezone.now().date(),
		)
		self.session = MovieSession.objects.create(
			movie=self.movie,
			screen_number=2,
			start_time=timezone.now() + timedelta(hours=3),
			end_time=timezone.now() + timedelta(hours=6),
			total_seats=3,
			available_seats=3,
		)
		self.seat = Seat.objects.create(session=self.session, row='B', number=4)

	def test_seat_map_endpoint(self):
		response = self.client.get(f'/api/sessions/{self.session.id}/seat-map/')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['id'], self.session.id)
		self.assertEqual(len(response.data['seats']), 1)

	def test_reserve_and_release_seat_endpoint(self):
		reserve_response = self.client.post(f'/api/sessions/{self.session.id}/seats/{self.seat.id}/reserve/')
		self.assertEqual(reserve_response.status_code, status.HTTP_200_OK)

		release_response = self.client.delete(f'/api/sessions/{self.session.id}/seats/{self.seat.id}/release/')
		self.assertEqual(release_response.status_code, status.HTTP_200_OK)
