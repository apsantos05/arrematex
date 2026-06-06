"""Arrematex backend package — initialise Celery on import."""
from .celery import app as celery_app

__all__ = ("celery_app",)
