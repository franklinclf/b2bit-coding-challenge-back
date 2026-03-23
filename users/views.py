from django.views.generic import TemplateView
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, inline_serializer
from rest_framework import serializers
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import UserRegistrationSerializer, UserLoginSerializer, UserSerializer


def _apply_scope(request, scope_name):
    request.throttle_scope = scope_name
    throttle = ScopedRateThrottle()
    if not throttle.allow_request(request, None):
        wait = throttle.wait() or 60
        return Response(
            {'detail': 'Muitas requisicoes. Tente novamente em instantes.'},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
            headers={'Retry-After': str(int(wait))}
        )
    return None


@extend_schema(
    tags=['Autenticacao'],
    summary='Registrar usuario',
    request=UserRegistrationSerializer,
    responses={201: OpenApiResponse(description='Usuario criado com sucesso')},
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register(request):
    throttled_response = _apply_scope(request, 'register')
    if throttled_response:
        return throttled_response

    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Autenticacao'],
    summary='Login com JWT',
    request=UserLoginSerializer,
    responses={200: OpenApiResponse(description='Login realizado com sucesso')},
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login(request):
    throttled_response = _apply_scope(request, 'login')
    if throttled_response:
        return throttled_response

    serializer = UserLoginSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Autenticacao'],
    summary='Logout (blacklist do refresh token)',
    request=inline_serializer(
        name='LogoutRequest',
        fields={'refresh': serializers.CharField(required=True)},
    ),
    responses={205: OpenApiResponse(description='Sessao encerrada com sucesso')},
)
@api_view(['POST'])
def logout(request):
    try:
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'refresh token e obrigatorio'}, status=status.HTTP_400_BAD_REQUEST)

        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response(status=status.HTTP_205_RESET_CONTENT)
    except Exception as exc:
        return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    get=extend_schema(tags=['Autenticacao'], summary='Obter perfil do usuario autenticado'),
    put=extend_schema(tags=['Autenticacao'], summary='Atualizar perfil do usuario autenticado'),
    patch=extend_schema(tags=['Autenticacao'], summary='Atualizar parcialmente o perfil do usuario autenticado'),
)
class UserProfileView(RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class MyPortalView(TemplateView):
    template_name = 'users/my_portal.html'


