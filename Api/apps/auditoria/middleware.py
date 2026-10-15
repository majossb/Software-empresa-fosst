from .models import AuditLog

# Rutas que no queremos auditar (estáticos, docs, health-check)
RUTAS_EXCLUIDAS = ("/static/", "/media/", "/api/docs", "/api/health")


class AuditoriaMiddleware:
    """
    Registra automáticamente cada operación de escritura (POST/PUT/PATCH/DELETE)
    hecha por un usuario autenticado, sin que cada vista tenga que hacerlo a mano.
    Las vistas de auth (login, activación, reset) crean su propio AuditLog más
    detallado directamente, así que este middleware evita duplicarlos.
    """
    METODOS_AUDITABLES = ("POST", "PUT", "PATCH", "DELETE")
    RUTAS_CON_AUDITORIA_PROPIA = ("/api/auth/", "/api/reclutamiento/portal/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if (
            request.path.startswith(RUTAS_EXCLUIDAS)
            or request.path.startswith(self.RUTAS_CON_AUDITORIA_PROPIA)
            or request.method not in self.METODOS_AUDITABLES
            or not getattr(request, "user", None)
            or not request.user.is_authenticated
            or not hasattr(request.user, "rol")
            or response.status_code >= 400
        ):
            return response

        accion = {
            "POST": AuditLog.Accion.CREACION,
            "PUT": AuditLog.Accion.ACTUALIZACION,
            "PATCH": AuditLog.Accion.ACTUALIZACION,
            "DELETE": AuditLog.Accion.ELIMINACION,
        }[request.method]

        AuditLog.objects.create(
            usuario=request.user,
            empresa=getattr(request.user, "empresa", None),
            accion=accion,
            ruta=request.path,
            metodo_http=request.method,
            ip=_get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
        return response


def _get_client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
