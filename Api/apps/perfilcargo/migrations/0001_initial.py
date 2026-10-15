# Generated manually to resolve dependency loop during migration refresh
import uuid
import django.db.models.deletion
from django.db import migrations, models

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('empresas', '0001_initial'),
        ('organizacion', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PerfilCargo',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('codigo', models.CharField(max_length=255)),
                ('version_actual', models.IntegerField(default=1)),
                ('nombre_cargo', models.CharField(max_length=255)),
                ('area', models.CharField(blank=True, max_length=255, null=True)),
                ('nivel_riesgo', models.IntegerField(blank=True, null=True)),
                ('proposito', models.TextField(blank=True, null=True)),
                ('educacion', models.TextField(blank=True, null=True)),
                ('experiencia', models.TextField(blank=True, null=True)),
                ('formacion', models.TextField(blank=True, null=True)),
                ('habilidades', models.TextField(blank=True, null=True)),
                ('activo', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='perfiles_cargo', to='empresas.empresa')),
                ('sede', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='organizacion.sede')),
            ],
            options={
                'db_table': 'perfiles_cargo',
            },
        ),
    ]
