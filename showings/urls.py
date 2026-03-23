from django.urls import path

from . import views

urlpatterns = [
    path('', views.MovieSessionListView.as_view(), name='session-list'),
    path('<int:pk>/', views.MovieSessionDetailView.as_view(), name='session-detail'),
    path('<int:session_id>/seat-map/', views.seat_map, name='seat-map'),
    path('<int:session_id>/seats/<int:seat_id>/reserve/', views.reserve_seat, name='reserve-seat'),
    path('<int:session_id>/seats/<int:seat_id>/release/', views.release_seat, name='release-seat'),
]
