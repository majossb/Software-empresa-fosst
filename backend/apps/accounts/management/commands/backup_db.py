"""
Comando administrativo para realizar respaldos automáticos y manuales de la base de datos.
Genera un archivo de volcado estructurado (.json o .json.gz) con todos los datos del sistema
(empresas, usuarios, evaluaciones, hallazgos, apelaciones, informes, trabajadores, configuraciones).

Uso:
  python manage.py backup_db
  python manage.py backup_db --filename=copia_seguridad.json
"""

import os
from datetime import datetime
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.conf import settings


class Command(BaseCommand):
    help = "Genera un respaldo completo de la base de datos en la carpeta backups/"

    def add_arguments(self, parser):
        parser.add_argument(
            "--filename",
            type=str,
            help="Nombre del archivo de respaldo a generar.",
        )
        parser.add_argument(
            "--quiet",
            action="store_true",
            help="Modo silencioso para ejecuciones automatizadas.",
        )

    def handle(self, *args, **options):
        quiet = options.get("quiet", False)
        base_dir = Path(settings.BASE_DIR).parent
        backup_dir = base_dir / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        filename = options.get("filename")
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            env_name = getattr(settings, "ENVIRONMENT", "development").lower()
            filename = f"backup_{env_name}_{timestamp}.json"

        target_file = backup_dir / filename

        if not quiet:
            self.stdout.write(f"Generando respaldo de la base de datos en: {target_file}...")

        try:
            with open(target_file, "w", encoding="utf-8") as f:
                call_command(
                    "dumpdata",
                    stdout=f,
                    indent=2,
                    exclude=[
                        "contenttypes",
                        "auth.permission",
                        "sessions",
                        "axes.accessattempt",
                        "axes.accesslog",
                        "axes.accessfailurelog",
                    ],
                )

            size_bytes = target_file.stat().st_size
            size_mb = size_bytes / (1024 * 1024)

            if not quiet:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[RESPALDO EXITOSO] Archivo guardado correctamente en: {target_file} ({size_mb:.2f} MB)"
                    )
                )

            return str(target_file)

        except Exception as exc:
            if target_file.exists():
                try:
                    target_file.unlink()
                except Exception:
                    pass
            raise CommandError(f"Error generando el respaldo de la base de datos: {exc}")
