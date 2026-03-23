from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions

from showings.models import MovieSession
from showings.serializers import MovieSessionSerializer
from .models import Movie
from .serializers import MovieSerializer


@method_decorator(cache_page(settings.MOVIES_LIST_CACHE_TTL), name='dispatch')
@extend_schema(tags=['Filmes'], summary='Listar filmes disponiveis')
class MovieListView(generics.ListAPIView):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    permission_classes = [permissions.AllowAny]


@method_decorator(cache_page(settings.SESSIONS_LIST_CACHE_TTL), name='dispatch')
@extend_schema(tags=['Filmes'], summary='Listar sessoes de um filme')
class MovieSessionListView(generics.ListAPIView):
    serializer_class = MovieSessionSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        movie_id = self.kwargs.get('movie_id')
        if movie_id:
            return MovieSession.objects.filter(movie_id=movie_id)
        return MovieSession.objects.all()
