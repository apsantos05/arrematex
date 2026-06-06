"""Serializers e views de autenticação — JWT com dados do tenant."""
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.models import User
from apps.auditoria.utils import registrar_log


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Adiciona dados do usuário no payload do token."""

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        data["user"] = {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "mfa_enabled": user.mfa_enabled,
        }
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    throttle_scope = "login"

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            # Registra IP do login bem-sucedido
            email = request.data.get("email", "")
            try:
                user = User.objects.get(email=email)
                user.last_login_ip = _get_client_ip(request)
                user.save(update_fields=["last_login_ip"])
                registrar_log(None, "login", user_email=email, ip=_get_client_ip(request))
            except User.DoesNotExist:
                pass
        else:
            registrar_log(None, "login_fail", ip=_get_client_ip(request))
        return response


class UserMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "mfa_enabled": user.mfa_enabled,
            "avatar": request.build_absolute_uri(user.avatar.url) if user.avatar else None,
        })

    def patch(self, request):
        allowed = {"full_name", "phone", "timezone"}
        data = {k: v for k, v in request.data.items() if k in allowed}
        for field, value in data.items():
            setattr(request.user, field, value)
        request.user.save(update_fields=list(data.keys()))
        return Response({"detail": "Perfil atualizado."})


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "full_name", "role", "phone", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["email", "full_name", "role", "phone", "password"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_admin:
            return Response(status=status.HTTP_403_FORBIDDEN)
        users = User.objects.all()
        return Response(UserSerializer(users, many=True).data)

    def post(self, request):
        if not request.user.is_admin:
            return Response(status=status.HTTP_403_FORBIDDEN)
        ser = UserCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        registrar_log(request.user, "create", model_name="User", object_id=str(user.id),
                      object_repr=user.email, dados_depois={"email": user.email, "role": user.role})
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


def _get_client_ip(request) -> str:
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")
