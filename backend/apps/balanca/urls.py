from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BalancaViewSet, PesagemViewSet

router = DefaultRouter()
router.register("providers", BalancaViewSet, basename="balanca")
router.register("pesagens", PesagemViewSet, basename="pesagem")

urlpatterns = [
    path("", include(router.urls)),
]
