"""
Comando administrativo para restaurar un respaldo de la base de datos generado con backup_db.
Permite restaurar los datos del sistema desde un archivo .json ubicado en backups/ o ruta personalizada.

Uso:
  python manage.py restore_db --confirm
  python manage.py restore_db --file=backups/backup_uat_20260927_215500.json --confirm
"""

from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.conf import settings
from django.db import transaction


class Command(BaseCommand):
    help = "Restaura la base de datos a partir de un archivo de respaldo .json"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            help="Ruta al archivo de respaldo .json.",
        )
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Confirma explícitamente la restauración de la base de datos.",
        )

    def handle(self, *args, **options):
        confirm = options.get("confirm", False)
        base_dir = Path(settings.BASE_DIR).parent
        backup_dir = base_dir / "backups"

        file_arg = options.get("file")
        if file_arg:
            target_file = Path(file_arg)
        else:
            # Buscar el archivo más reciente en backups/
            json_files = sorted(backup_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            if not json_files:
                raise CommandError("No se encontraron archivos .json de respaldo en la carpeta backups/")
            target_file = json_files[0]

        if not target_file.exists():
            raise CommandError(f"El archivo de respaldo especificado no existe: {target_file}")

        self.stdout.write(self.style.WARNING("============================================================"))
        self.stdout.write(self.style.WARNING("ADVERTENCIA DE RESTAURACIÓN DE BASE DE DATOS"))
        self.stdout.write(self.style.WARNING(f"Archivo a cargar: {target_file}"))
        self.stdout.write(self.style.WARNING("============================================================"))

        if not confirm:
            confirmacion = input("¿Está seguro de restaurar los datos desde este archivo? (escriba 'SI' para continuar): ")
            if confirmacion.strip().upper() != "SI":
                self.stdout.write(self.style.NOTICE("Restauración cancelada."))
                return

        self.stdout.write("Cargando datos desde el respaldo...")

        try:
            with transaction.atomic():
                call_command("loaddata", str(target_file))

            self.stdout.write(
                self.style.SUCCESS(
                    f"\n[RESTAURACIÓN EXITOSA] La base de datos fue restaurada correctamente desde: {target_file.name}"
                )
            )

        except Exception as exc:
            raise CommandError(f"Error restaurando la base de datos: {exc}")
