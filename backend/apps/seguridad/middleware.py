import hashlib

from .models import DispositivoConocido, EventoRiesgo
from .notificaciones import notificar_acceso_inusual


class DispositivoMiddleware:
    """
    Tras un login exitoso (marcado por la vista de login con
    `request.login_exitoso = True`), registra el dispositivo/IP y,
    si es la primera vez que se ve esa combinación, dispara una
    notificación de "acceso inusual" al correo del usuario.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if getattr(request, "login_exitoso", False) and request.user.is_authenticated:
            ip = _get_client_ip(request)
            user_agent = request.META.get("HTTP_USER_AGENT", "")
            fingerprint = hashlib.sha256(f"{user_agent}|{ip}".encode()).hexdigest()

            dispositivo, creado = DispositivoConocido.objects.get_or_create(
                usuario=request.user,
                fingerprint=fingerprint,
                defaults={"user_agent": user_agent, "ip": ip},
            )
            if not creado:
                dispositivo.save(update_fields=["ultima_vez"])
            else:
                EventoRiesgo.objects.create(
                    usuario=request.user,
                    tipo=EventoRiesgo.Tipo.LOGIN_NUEVO_DISPOSITIVO,
                    ip=ip,
                    detalle={"user_agent": user_agent},
                )
                notificar_acceso_inusual(request.user, ip, user_agent)

        return response


def _get_client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
