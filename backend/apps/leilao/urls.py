from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LeilaoViewSet, SessaoLeilaoViewSet

router = DefaultRouter()
router.register("eventos-leilao", LeilaoViewSet, basename="leilao")
router.register("sessoes", SessaoLeilaoViewSet, basename="sessao")

urlpatterns = [
    path("", include(router.urls)),
]
