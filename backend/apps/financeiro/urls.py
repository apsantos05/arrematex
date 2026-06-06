from django.urls import include, path
from rest_framework.routers import DefaultRouter
from apps.financeiro.views import EstornoView, RecebimentoViewSet, VendaViewSet

router = DefaultRouter()
router.register("vendas", VendaViewSet, basename="venda")
router.register("recebimentos", RecebimentoViewSet, basename="recebimento")

urlpatterns = [
    path("", include(router.urls)),
    path("recebimentos/<uuid:recebimento_id>/estornar/", EstornoView.as_view(), name="estorno"),
]
