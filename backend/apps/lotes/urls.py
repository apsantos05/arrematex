from django.urls import include, path
from rest_framework.routers import DefaultRouter
from apps.lotes.views import CategoriaSerializer, EventoViewSet, LoteViewSet, VendedorSerializer
from rest_framework.viewsets import ModelViewSet
from apps.lotes.models import Categoria, Vendedor
from rest_framework.permissions import IsAuthenticated


class CategoriaViewSet(ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [IsAuthenticated]


class VendedorViewSet(ModelViewSet):
    queryset = Vendedor.objects.all()
    serializer_class = VendedorSerializer
    permission_classes = [IsAuthenticated]


router = DefaultRouter()
router.register("eventos", EventoViewSet, basename="evento")
router.register("lotes", LoteViewSet, basename="lote")
router.register("categorias", CategoriaViewSet, basename="categoria")
router.register("vendedores", VendedorViewSet, basename="vendedor")

urlpatterns = [path("", include(router.urls))]
