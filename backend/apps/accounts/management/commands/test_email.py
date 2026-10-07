import smtplib
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.mail import send_mail, get_connection


class Command(BaseCommand):
    help = "Compara la configuración SMTP y envía un correo real de prueba al destinatario especificado sin exponer secretos."

    def add_arguments(self, parser):
        parser.add_argument("email", type=str, help="Correo electrónico destinatario para el test SMTP")

    def handle(self, *args, **options):
        destinatario = options["email"]

        self.stdout.write(self.style.MIGRATE_HEADING("=== DIAGNÓSTICO DE CONFIGURACIÓN SMTP ==="))

        # 1. Comprobar configuración
        backend_name = getattr(settings, "EMAIL_BACKEND", "")
        host = getattr(settings, "EMAIL_HOST", "")
        port = getattr(settings, "EMAIL_PORT", 587)
        use_tls = getattr(settings, "EMAIL_USE_TLS", True)
        use_ssl = getattr(settings, "EMAIL_USE_SSL", False)
        user = getattr(settings, "EMAIL_HOST_USER", "")
        has_password = bool(getattr(settings, "EMAIL_HOST_PASSWORD", ""))
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "")

        self.stdout.write(f"Backend: {backend_name}")
        self.stdout.write(f"Host SMTP: {host}:{port}")
        self.stdout.write(f"TLS: {use_tls} | SSL: {use_ssl}")
        self.stdout.write(f"Usuario SMTP: {user or '(sin autenticación)'}")
        self.stdout.write(f"Contraseña configurada: {'SÍ (********)' if has_password else 'NO'}")
        self.stdout.write(f"Remitente (FROM): {from_email}")
        self.stdout.write(f"Destinatario (TO): {destinatario}")

        if not host:
            self.stdout.write(self.style.ERROR("SMTP NO CONFIGURADO — EMAIL_HOST está vacío."))
            return

        self.stdout.write(self.style.SUCCESS("SMTP CONFIGURADO"))

        # 2 & 3. Comprobar conexión y autenticación
        try:
            connection = get_connection()
            self.stdout.write("Probando conexión al servidor SMTP...")
            connection.open()
            self.stdout.write(self.style.SUCCESS("CONEXIÓN EXITOSA"))
            if user and has_password:
                self.stdout.write(self.style.SUCCESS("AUTENTICACIÓN EXITOSA"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"ERROR DE CONEXIÓN / AUTENTICACIÓN SMTP: {str(e)}"))
            return

        # 4. Enviar correo de prueba
        try:
            self.stdout.write(f"Enviando correo de prueba a {destinatario}...")
            send_mail(
                subject="Prueba de Diagnóstico SMTP — FOSST V.I.D.A.",
                message=(
                    f"Este es un correo de prueba generado desde el comando de diagnóstico SMTP de FOSST V.I.D.A.\n\n"
                    f"Remitente: {from_email}\n"
                    f"Destinatario: {destinatario}\n"
                    f"Estado: MIGRACIÓN SMTP NATIVO COMPLETADA EXITOSAMENTE."
                ),
                from_email=from_email,
                recipient_list=[destinatario],
                fail_silently=False,
                connection=connection,
            )
            self.stdout.write(self.style.SUCCESS("CORREO ENVIADO"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"FALLO EN EL ENVÍO DEL CORREO: {str(e)}"))
        finally:
            try:
                connection.close()
            except Exception:
                pass
