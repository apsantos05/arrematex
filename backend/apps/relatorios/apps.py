"""
App de relatórios — sem models próprios, só views de agregação.
"""
from django.apps import AppConfig


class RelatoriosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.relatorios"
