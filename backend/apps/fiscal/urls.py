from django.urls import include, path
from rest_framework.routers import DefaultRouter
from apps.fiscal.views import CancelarNFeView, EmitirNFeView, NotaFiscalViewSet, UploadCertificadoView

router = DefaultRouter()
router.register("notas", NotaFiscalViewSet, basename="nota-fiscal")

urlpatterns = [
    path("", include(router.urls)),
    path("certificados/upload/", UploadCertificadoView.as_view(), name="upload-certificado"),
    path("notas/<uuid:nota_id>/cancelar/", CancelarNFeView.as_view(), name="cancelar-nfe"),
    path("emitir/<uuid:venda_id>/", EmitirNFeView.as_view(), name="emitir-nfe"),
]
