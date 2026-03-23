from django.urls import path

from . import views

urlpatterns = [
    path('my-tickets/', views.UserTicketListView.as_view(), name='user-tickets'),
    path('checkout/', views.checkout, name='checkout'),
]
