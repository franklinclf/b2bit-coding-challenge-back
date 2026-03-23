from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from users.views import MyPortalView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('portal/', MyPortalView.as_view(), name='portal-web'),
    path('api/auth/', include('users.urls')),
    path('api/movies/', include('movies.urls')),
    path('api/sessions/', include('showings.urls')),
    path('api/tickets/', include('tickets.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
