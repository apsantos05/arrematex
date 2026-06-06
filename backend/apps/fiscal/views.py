"""Views fiscais — upload de certificado, emissão e consulta de NF-e."""
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.fiscal.models import CertificadoDigital, ConfiguracaoFiscal, NotaFiscal
from apps.auditoria.utils import registrar_log


class NotaFiscalSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotaFiscal
        fields = "__all__"
        read_only_fields = [f.name for f in NotaFiscal._meta.get_fields()]


class NotaFiscalViewSet(ReadOnlyModelViewSet):
    queryset = NotaFiscal.objects.all()
    serializer_class = NotaFiscalSerializer
    permission_classes = [IsAuthenticated]


class UploadCertificadoView(APIView):
    """Upload seguro de certificado A1 (.pfx)."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.can_manage_fiscal:
            return Response(status=status.HTTP_403_FORBIDDEN)

        arquivo = request.FILES.get("arquivo")
        senha = request.data.get("senha")
        nome = request.data.get("nome", "Certificado A1")

        if not arquivo or not senha:
            return Response(
                {"detail": "Arquivo .pfx e senha são obrigatórios."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.fiscal.services.certificate_service import CertificateService
        try:
            cert = CertificateService.salvar_certificado(
                pfx_bytes=arquivo.read(),
                senha=senha,
                usuario=request.user,
                nome=nome,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        registrar_log(request.user, "enviar_cert", "CertificadoDigital", str(cert.id), cert.cnpj)
        return Response({
            "id": str(cert.id),
            "cnpj": cert.cnpj,
            "razao_social": cert.razao_social,
            "validade": cert.validade.isoformat(),
            "dias_para_vencer": cert.dias_para_vencer,
        }, status=status.HTTP_201_CREATED)


class EmitirNFeView(APIView):
    """Dispara emissão de NF-e para uma venda específica."""
    permission_classes = [IsAuthenticated]

    def post(self, request, venda_id):
        if not request.user.can_manage_fiscal:
            return Response(status=status.HTTP_403_FORBIDDEN)

        from apps.financeiro.models import Venda
        try:
            venda = Venda.objects.get(id=venda_id)
        except Venda.DoesNotExist:
            return Response({"detail": "Venda não encontrada."}, status=status.HTTP_404_NOT_FOUND)

        if venda.nfe_emitida:
            return Response({"detail": "NF-e já emitida para esta venda."}, status=status.HTTP_400_BAD_REQUEST)

        config = ConfiguracaoFiscal.objects.first()
        if not config or not config.certificado:
            return Response(
                {"detail": "Configuração fiscal ou certificado não encontrado."},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        from apps.fiscal.services.nfe_service import NFeService
        nota = NFeService(config).emitir_nfe_para_venda(venda, request.user)
        return Response(NotaFiscalSerializer(nota).data, status=status.HTTP_201_CREATED)


class CancelarNFeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, nota_id):
        if not request.user.can_manage_fiscal:
            return Response(status=status.HTTP_403_FORBIDDEN)

        try:
            nota = NotaFiscal.objects.get(id=nota_id, status=NotaFiscal.STATUS_AUTORIZADA)
        except NotaFiscal.DoesNotExist:
            return Response({"detail": "Nota não encontrada ou não está autorizada."}, status=status.HTTP_404_NOT_FOUND)

        justificativa = request.data.get("justificativa", "")
        if len(justificativa) < 15:
            return Response({"detail": "Justificativa deve ter no mínimo 15 caracteres."}, status=status.HTTP_400_BAD_REQUEST)

        nota.status = NotaFiscal.STATUS_CANCELADA
        nota.save(update_fields=["status"])
        registrar_log(request.user, "cancelar_nf", "NotaFiscal", str(nota.id), justificativa)
        return Response({"detail": "NF-e cancelada."})
