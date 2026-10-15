import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizacion', '0002_initial'),
        ('perfilcargo', '0002_cargocompetencia_cargoepp_cargofuncion_and_more'),
    ]

    operations = [
        # --- Campos nuevos en PerfilCargo (§4.1) ---
        migrations.AddField(
            model_name='perfilcargo',
            name='criticidad_sst',
            field=models.CharField(
                choices=[('bajo', 'Bajo'), ('medio', 'Medio'), ('alto', 'Alto'), ('critico', 'Crítico')],
                default='bajo', max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='perfilcargo',
            name='criticidad_operacional',
            field=models.CharField(
                choices=[('bajo', 'Bajo'), ('medio', 'Medio'), ('alto', 'Alto'), ('critico', 'Crítico')],
                default='bajo', max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='perfilcargo',
            name='criticidad_vial',
            field=models.CharField(
                choices=[('bajo', 'Bajo'), ('medio', 'Medio'), ('alto', 'Alto'), ('critico', 'Crítico')],
                default='bajo', max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='perfilcargo',
            name='criticidad_ambiental',
            field=models.CharField(
                choices=[('bajo', 'Bajo'), ('medio', 'Medio'), ('alto', 'Alto'), ('critico', 'Crítico')],
                default='bajo', max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='perfilcargo',
            name='criticidad_estrategica',
            field=models.CharField(
                choices=[('bajo', 'Bajo'), ('medio', 'Medio'), ('alto', 'Alto'), ('critico', 'Crítico')],
                default='bajo', max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='perfilcargo',
            name='requiere_suplencia',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='perfilcargo',
            name='impacto_descripcion',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='perfilcargo',
            name='naturaleza_descripcion',
            field=models.TextField(blank=True, null=True),
        ),

        # --- Extensión de CargoCompetencia (§4.1 / base de la MCC en §9) ---
        migrations.AddField(
            model_name='cargocompetencia',
            name='tipo',
            field=models.CharField(
                blank=True, null=True, max_length=20,
                choices=[('tecnica', 'Técnica'), ('blanda', 'Blanda'), ('organizacional', 'Organizacional')],
            ),
        ),
        migrations.AddField(
            model_name='cargocompetencia',
            name='nivel_requerido',
            field=models.PositiveSmallIntegerField(
                blank=True, null=True,
                help_text='1=Básico, 2=Intermedio, 3=Avanzado, 4=Experto',
            ),
        ),

        # --- Tablas nuevas ---
        migrations.CreateModel(
            name='CargoAptitud',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tipo', models.CharField(choices=[('fisica', 'Física'), ('psicologica', 'Psicológica')], max_length=20)),
                ('nombre', models.CharField(max_length=255)),
                ('requerida', models.BooleanField(default=True)),
                ('observacion', models.TextField(blank=True, null=True)),
                ('perfil_cargo', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, related_name='aptitudes',
                    to='perfilcargo.perfilcargo',
                )),
            ],
            options={'db_table': 'cargo_aptitudes'},
        ),
        migrations.CreateModel(
            name='CargoInteraccion',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('parte_interesada', models.CharField(max_length=255)),
                ('tipo', models.CharField(choices=[('interno', 'Interno'), ('externo', 'Externo')], max_length=20)),
                ('descripcion', models.TextField(blank=True, null=True)),
                ('perfil_cargo', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, related_name='interacciones',
                    to='perfilcargo.perfilcargo',
                )),
                ('proceso', models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name='interacciones_cargo', to='organizacion.proceso',
                )),
            ],
            options={'db_table': 'cargo_interacciones'},
        ),
        migrations.CreateModel(
            name='CargoRestriccion',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('descripcion', models.CharField(max_length=500)),
                ('activa', models.BooleanField(default=True)),
                ('perfil_cargo', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, related_name='restricciones',
                    to='perfilcargo.perfilcargo',
                )),
            ],
            options={'db_table': 'cargo_restricciones'},
        ),
        migrations.CreateModel(
            name='CargoSuplente',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('orden_prioridad', models.PositiveSmallIntegerField(default=1)),
                ('cargo_suplente', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, related_name='suple_a',
                    to='perfilcargo.perfilcargo',
                )),
                ('perfil_cargo', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, related_name='suplentes',
                    to='perfilcargo.perfilcargo',
                )),
            ],
            options={
                'db_table': 'cargo_suplentes',
                'ordering': ['orden_prioridad'],
            },
        ),
        migrations.AddConstraint(
            model_name='cargosuplente',
            constraint=models.UniqueConstraint(
                fields=('perfil_cargo', 'cargo_suplente'), name='unique_cargo_suplente'
            ),
        ),
    ]
