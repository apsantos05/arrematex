"""
Management command to bootstrap the development environment.
Creates the public tenant + an initial tenant for testing.
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Bootstrap dev: create public tenant, run migrations, create superuser"

    def handle(self, *args, **options):
        from apps.tenants.models import Tenant, Domain

        # Create public tenant if it doesn't exist
        if not Tenant.objects.filter(schema_name="public").exists():
            self.stdout.write("Creating public tenant...")
            public = Tenant(
                schema_name="public",
                nome="Arrematex Platform",
                slug="public",
                plano="enterprise",
                ativo=True,
            )
            public.save(verbosity=0)
            Domain.objects.get_or_create(
                domain="localhost",
                defaults={"tenant": public, "is_primary": True},
            )
            self.stdout.write(self.style.SUCCESS("Public tenant created."))
        else:
            self.stdout.write("Public tenant already exists.")

        # Create a demo tenant for testing
        if not Tenant.objects.filter(schema_name="demo").exists():
            self.stdout.write("Creating demo tenant...")
            demo = Tenant(
                schema_name="demo",
                nome="Demo Leilões",
                slug="demo",
                plano="professional",
                ativo=True,
            )
            demo.save(verbosity=0)
            Domain.objects.get_or_create(
                domain="demo.localhost",
                defaults={"tenant": demo, "is_primary": True},
            )
            self.stdout.write(self.style.SUCCESS("Demo tenant created."))
        else:
            self.stdout.write("Demo tenant already exists.")

        self.stdout.write(self.style.SUCCESS("setup_dev complete."))
