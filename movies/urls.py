from django.urls import path

from . import views

urlpatterns = [
    path('', views.MovieListView.as_view(), name='movie-list'),
    path('<int:movie_id>/sessions/', views.MovieSessionListView.as_view(), name='movie-sessions'),
]
