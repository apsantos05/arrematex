from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenBlacklistView

from apps.accounts.views import CustomTokenObtainPairView, UserMeView, UserListCreateView

urlpatterns = [
    path("login/", CustomTokenObtainPairView.as_view(), name="token-obtain"),
    path("refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("logout/", TokenBlacklistView.as_view(), name="token-blacklist"),
    path("me/", UserMeView.as_view(), name="user-me"),
    path("users/", UserListCreateView.as_view(), name="user-list"),
]
