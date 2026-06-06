from django.urls import path
from .views import ResumoView, VendasRelatorioView, LotesRelatorioView

urlpatterns = [
    path("resumo/",          ResumoView.as_view(),          name="resumo"),
    path("vendas/",          VendasRelatorioView.as_view(),  name="relatorio-vendas"),
    path("lotes/",           LotesRelatorioView.as_view(),   name="relatorio-lotes"),
]
