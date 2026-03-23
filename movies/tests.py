from datetime import date

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Movie


class MovieTestCase(TestCase):
    def test_create_movie(self):
        movie = Movie.objects.create(
            title='Test Movie',
            description='A test movie description',
            duration_minutes=120,
            genre='Action',
            rating='PG-13',
            release_date=date.today()
        )
        self.assertEqual(movie.title, 'Test Movie')
        self.assertEqual(movie.duration_minutes, 120)


class MovieAPITestCase(APITestCase):
    def setUp(self):
        self.movie = Movie.objects.create(
            title='Test Movie',
            description='A test movie description',
            duration_minutes=120,
            genre='Action',
            rating='PG-13',
            release_date=date.today()
        )

    def test_list_movies(self):
        response = self.client.get('/api/movies/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Test Movie')
