"""
URLs acessíveis dentro do schema de cada tenant.
"""
from django.urls import include, path

urlpatterns = [
    path("auth/", include("apps.accounts.urls")),
    path("lotes/", include("apps.lotes.urls")),
    path("leilao/", include("apps.leilao.urls")),
    path("financeiro/", include("apps.financeiro.urls")),
    path("fiscal/", include("apps.fiscal.urls")),
    path("balanca/", include("apps.balanca.urls")),
    path("relatorios/", include("apps.relatorios.urls")),
    path("auditoria/", include("apps.auditoria.urls")),
]
