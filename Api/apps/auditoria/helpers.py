from apps.auditoria.models import AuditLog


def registrar_audit_log(request, accion, tabla_afectada="", registro_id="", valores_anteriores=None, valores_nuevos=None):
    """
    Helper para registrar logs de auditoría en la BD.
    Réplica del auditLog helper de Express.
    """
    usuario = request.user if request and getattr(request, "user", None) and request.user.is_authenticated else None
    empresa = getattr(usuario, "empresa", None)
    ip = request.META.get("REMOTE_ADDR") if request else None
    metodo = getattr(request, "method", "")
    ruta = getattr(request, "path", "")

    return AuditLog.objects.create(
        usuario=usuario,
        empresa=empresa,
        accion=str(accion),
        tabla_afectada=tabla_afectada,
        registro_id=str(registro_id),
        valores_anteriores=valores_anteriores,
        valores_nuevos=valores_nuevos,
        ip=ip,
        metodo_http=metodo,
        ruta=ruta,
    )
