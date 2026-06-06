from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("lotes", "0002_alter_categoria_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="evento",
            name="hora_inicio",
            field=models.TimeField(blank=True, null=True, verbose_name="Hora de Início"),
        ),
    ]
