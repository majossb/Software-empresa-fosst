from datetime import datetime

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.estandares.models import Estandar, Evaluacion
from apps.planes.mixins import PlanGatingMixin
from .models import Informe
from .serializers import InformeSerializer


def calcular_phva(respuestas, estandares):
    """Calcula puntaje por ciclo PHVA. Réplica exacta de helpers.ts."""
    ciclos = ["Planear", "Hacer", "Verificar", "Actuar"]
    resultado = {}

    for ciclo in ciclos:
        ests_ciclo = [e for e in estandares if e.ciclo_phva == ciclo]
        maximo = sum(float(e.puntaje_maximo) for e in ests_ciclo)

        obtenido = 0
        for est in ests_ciclo:
            resp = next((r for r in respuestas if r.estandar_id == est.id), None)
            if resp and resp.puntaje:
                obtenido += float(resp.puntaje)

        resultado[ciclo] = {
            "obtenido": round(obtenido, 2),
            "maximo": round(maximo, 2),
            "porcentaje": round((obtenido / maximo) * 100) if maximo > 0 else 0,
        }

    return resultado


def generar_recomendaciones(cumplimiento, respuestas, estandares):
    """Genera recomendaciones automáticas. Réplica de informe.controller.ts."""
    recomendaciones = []

    if cumplimiento < 60:
        recomendaciones.append(
            "Se recomienda implementar un plan de acción urgente para alcanzar al menos el 60% de cumplimiento."
        )

    no_cumple = [r for r in respuestas if r.estado == "no_cumple"]
    if no_cumple:
        recomendaciones.append(
            f"Existen {len(no_cumple)} estándares sin cumplir que requieren atención inmediata."
        )

    sin_evidencia = [
        r for r in respuestas
        if r.estado != "no_aplica" and (not hasattr(r, "evidencias") or r.evidencias.count() == 0)
    ]
    if sin_evidencia:
        recomendaciones.append(
            f"{len(sin_evidencia)} estándares carecen de evidencia documental. Se recomienda documentar el cumplimiento."
        )

    if cumplimiento >= 86:
        recomendaciones.append(
            "El nivel de cumplimiento es aceptable. Se recomienda mantener y mejorar continuamente."
        )

    return recomendaciones


class InformeListView(PlanGatingMixin, APIView):
    """GET /api/informes → lista informes de la empresa."""
    permission_classes = [IsAuthenticated]
    required_feature = "tiene_informes"

    def get(self, request):
        empresa = request.user.empresa
        if not empresa:
            return Response({"message": "Sin empresa asociada."}, status=400)

        evaluacion_ids = list(
            Evaluacion.objects.filter(empresa=empresa).values_list("id", flat=True)
        )

        informes = Informe.objects.filter(
            evaluacion_id__in=evaluacion_ids,
            deleted_at__isnull=True,
        ).select_related("evaluacion").order_by("-fecha_elaboracion")

        serializer = InformeSerializer(informes, many=True)
        return Response(serializer.data)


class InformeGenerarView(PlanGatingMixin, APIView):
    """POST /api/informes/generar → genera informe con cálculos PHVA."""
    permission_classes = [IsAuthenticated]
    required_feature = "tiene_informes"

    def post(self, request):
        empresa = request.user.empresa
        if not empresa:
            return Response({"message": "Sin empresa asociada."}, status=400)

        evaluacion_id = request.data.get("evaluacion_id")
        tipo = request.data.get("tipo")

        if not evaluacion_id or not tipo:
            return Response({"message": "evaluacion_id y tipo son requeridos."}, status=400)

        try:
            evaluacion = Evaluacion.objects.prefetch_related(
                "respuestas__estandar",
                "respuestas__evidencias",
                "hallazgos__auditor",
            ).get(id=evaluacion_id, empresa=empresa)
        except Evaluacion.DoesNotExist:
            return Response({"message": "Evaluación no encontrada."}, status=404)

        capitulo = empresa.capitulo_vigente or "II"
        estandares = list(Estandar.objects.filter(capitulo=capitulo))
        respuestas = list(evaluacion.respuestas.all())

        phva = calcular_phva(respuestas, estandares)

        puntaje_maximo = sum(float(e.puntaje_maximo) for e in estandares)
        puntaje_obtenido = sum(float(r.puntaje or 0) for r in respuestas)
        cumplimiento = round((puntaje_obtenido / puntaje_maximo) * 100) if puntaje_maximo > 0 else 0

        # Check existing appeals for this evaluation
        from apps.estandares.models import Apelacion
        apelaciones_qs = Apelacion.objects.filter(respuesta__evaluacion=evaluacion).select_related("respuesta__estandar", "solicitante")
        apelaciones_list = [
            {
                "id": str(ap.id),
                "estandar_codigo": ap.respuesta.estandar.codigo,
                "estandar_nombre": ap.respuesta.estandar.nombre,
                "motivo": ap.motivo,
                "estado": ap.estado,
                "respuesta_auditor": ap.respuesta_auditor or "",
                "solicitante": (ap.solicitante.get_full_name() or ap.solicitante.username) if ap.solicitante else "",
            }
            for ap in apelaciones_qs
        ]

        # Generar contenido estructurado del informe
        contenido = {
            "meta": {
                "tipo": tipo,
                "generado_en": datetime.now().isoformat(),
                "empresa": empresa.nombre,
                "nit": empresa.nit,
                "anio": evaluacion.anio,
                "capitulo": evaluacion.capitulo,
                "auditor_nombre": (request.user.get_full_name() or request.user.username) if request.user else "",
            },
            "estado": "BORRADOR",
            "resumen_ejecutivo": {
                "cumplimiento_global": cumplimiento,
                "puntaje_obtenido": round(puntaje_obtenido, 2),
                "puntaje_maximo": round(puntaje_maximo, 2),
                "total_estandares": len(estandares),
                "cumple": sum(1 for r in respuestas if r.estado == "cumple"),
                "no_cumple": sum(1 for r in respuestas if r.estado == "no_cumple"),
                "parcial": sum(1 for r in respuestas if r.estado == "parcial"),
            },
            "phva": phva,
            "estandares_detalle": [
                {
                    "codigo": r.estandar.codigo,
                    "nombre": r.estandar.nombre,
                    "ciclo": r.estandar.ciclo_phva,
                    "estado": r.estado,
                    "puntaje": float(r.puntaje or 0),
                    "puntaje_maximo": float(r.estandar.puntaje_maximo),
                    "observacion": r.observacion,
                    "evidencias": r.evidencias.count() if hasattr(r, "evidencias") else 0,
                }
                for r in respuestas
            ],
            "hallazgos": [
                {
                    "tipo": h.tipo,
                    "descripcion": h.descripcion,
                    "auditor": h.auditor.get_full_name() if hasattr(h.auditor, "get_full_name") and h.auditor.get_full_name() else str(h.auditor),
                    "fecha": h.created_at.isoformat(),
                    "estandar_codigo": h.estandar.codigo if h.estandar else None,
                }
                for h in evaluacion.hallazgos.select_related("auditor", "estandar").all()
            ],
            "apelaciones": apelaciones_list,
            "clasificacion": (
                "ACEPTABLE" if cumplimiento >= 86
                else "MODERADAMENTE ACEPTABLE" if cumplimiento >= 61
                else "CRÍTICO"
            ),
            "narrativa": {
                "conclusiones": "",
                "recomendaciones": "",
                "observaciones_finales": "",
            },
        }

        # UPSERT: reutilizar borrador existente para esta evaluación + tipo, evitar duplicados
        existing = Informe.objects.filter(
            evaluacion=evaluacion,
            tipo=tipo,
            deleted_at__isnull=True,
        ).exclude(contenido_json__estado="FINALIZADO").first()

        if existing:
            existing.contenido_json = contenido
            existing.save(update_fields=["contenido_json"])
            informe = existing
            accion_audit = "REGENERAR_INFORME_BORRADOR"
        else:
            informe = Informe.objects.create(
                evaluacion=evaluacion,
                tipo=tipo,
                contenido_json=contenido,
            )
            accion_audit = "GENERAR_INFORME"

        from apps.auditoria.helpers import registrar_audit_log
        registrar_audit_log(request, accion_audit, tabla_afectada="informes", registro_id=informe.id, valores_nuevos={"tipo": tipo})

        serializer = InformeSerializer(informe)
        return Response(serializer.data, status=200 if existing else 201)


class InformeGuardarBorradorView(PlanGatingMixin, APIView):
    """POST /api/informes/<id>/guardar-borrador → guarda campos narrativos editables por el Auditor."""
    permission_classes = [IsAuthenticated]
    required_feature = "tiene_informes"

    def post(self, request, informe_id):
        empresa = request.user.empresa
        if not empresa:
            return Response({"error": "Sin empresa asociada."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            informe = Informe.objects.select_related("evaluacion").get(id=informe_id)
        except Informe.DoesNotExist:
            return Response({"error": "Informe no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        if informe.evaluacion.empresa_id != empresa.id:
            return Response({"error": "No tiene permisos sobre este informe."}, status=status.HTTP_403_FORBIDDEN)

        contenido = informe.contenido_json or {}
        if contenido.get("estado") == "FINALIZADO":
            return Response(
                {"error": "El informe ya se encuentra finalizado y bloqueado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        narrativa = contenido.get("narrativa") or {}
        narrativa["conclusiones"] = str(request.data.get("conclusiones", narrativa.get("conclusiones", ""))).strip()
        narrativa["recomendaciones"] = str(request.data.get("recomendaciones", narrativa.get("recomendaciones", ""))).strip()
        narrativa["observaciones_finales"] = str(request.data.get("observaciones_finales", narrativa.get("observaciones_finales", ""))).strip()

        contenido["narrativa"] = narrativa
        informe.contenido_json = contenido
        informe.save(update_fields=["contenido_json"])

        serializer = InformeSerializer(informe)
        return Response({"success": True, "message": "El informe se guardó correctamente.", "data": serializer.data})


class InformeFinalizarView(PlanGatingMixin, APIView):
    """POST /api/informes/<id>/finalizar → finaliza el informe y bloquea ediciones narrativas."""
    permission_classes = [IsAuthenticated]
    required_feature = "tiene_informes"

    def post(self, request, informe_id):
        empresa = request.user.empresa
        if not empresa:
            return Response({"error": "Sin empresa asociada."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            informe = Informe.objects.select_related("evaluacion").get(id=informe_id)
        except Informe.DoesNotExist:
            return Response({"error": "Informe no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        if informe.evaluacion.empresa_id != empresa.id:
            return Response({"error": "No tiene permisos sobre este informe."}, status=status.HTTP_403_FORBIDDEN)

        contenido = informe.contenido_json or {}
        if contenido.get("estado") == "FINALIZADO":
            return Response(
                {"error": "El informe ya se encuentra finalizado y bloqueado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        narrativa = contenido.get("narrativa") or {}
        if "conclusiones" in request.data:
            narrativa["conclusiones"] = str(request.data.get("conclusiones")).strip()
        if "recomendaciones" in request.data:
            narrativa["recomendaciones"] = str(request.data.get("recomendaciones")).strip()
        if "observaciones_finales" in request.data:
            narrativa["observaciones_finales"] = str(request.data.get("observaciones_finales")).strip()

        contenido["narrativa"] = narrativa
        contenido["estado"] = "FINALIZADO"
        contenido["fecha_finalizacion"] = datetime.now().isoformat()
        contenido["auditor_finalizo"] = request.user.get_full_name() or request.user.username

        informe.contenido_json = contenido
        informe.save(update_fields=["contenido_json"])

        from apps.auditoria.helpers import registrar_audit_log
        registrar_audit_log(request, "FINALIZAR_INFORME", tabla_afectada="informes", registro_id=informe.id, valores_nuevos={"estado": "FINALIZADO"})

        serializer = InformeSerializer(informe)
        return Response({"success": True, "message": "El informe final se generó correctamente.", "data": serializer.data})


class InformeDescartarBorradorView(PlanGatingMixin, APIView):
    """
    DELETE /api/informes/<id>/descartar-borrador
    Descarta (soft-delete) un borrador de informe.
    NO elimina: evaluación, respuestas, hallazgos, apelaciones, notificaciones ni historial.
    Solo marca deleted_at en el registro Informe.
    Restringido a borradores (estado != FINALIZADO) y al Auditor/Admin de la misma empresa.
    """
    permission_classes = [IsAuthenticated]
    required_feature = "tiene_informes"

    def delete(self, request, informe_id):
        from django.utils import timezone as tz
        empresa = request.user.empresa
        if not empresa:
            return Response({"error": "Sin empresa asociada."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            informe = Informe.objects.select_related("evaluacion").get(
                id=informe_id,
                deleted_at__isnull=True,
            )
        except Informe.DoesNotExist:
            return Response({"error": "Informe no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        if informe.evaluacion.empresa_id != empresa.id:
            return Response({"error": "No tiene permisos sobre este informe."}, status=status.HTTP_403_FORBIDDEN)

        contenido = informe.contenido_json or {}
        if contenido.get("estado") == "FINALIZADO":
            return Response(
                {"error": "No se puede descartar un informe ya finalizado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        informe.deleted_at = tz.now()
        informe.save(update_fields=["deleted_at"])

        from apps.auditoria.helpers import registrar_audit_log
        registrar_audit_log(
            request,
            "DESCARTAR_BORRADOR_INFORME",
            tabla_afectada="informes",
            registro_id=informe.id,
            valores_nuevos={"deleted_at": informe.deleted_at.isoformat()},
        )

        return Response(
            {"success": True, "message": "El borrador fue descartado correctamente."},
            status=status.HTTP_200_OK,
        )


class InformeDetalleView(PlanGatingMixin, APIView):

    """GET /api/informes/<id> → detalle de un informe."""
    permission_classes = [IsAuthenticated]
    required_feature = "tiene_informes"

    def get(self, request, informe_id):
        empresa = request.user.empresa
        if not empresa:
            return Response({"message": "Sin empresa asociada."}, status=400)

        try:
            informe = Informe.objects.select_related("evaluacion").get(id=informe_id)
        except Informe.DoesNotExist:
            return Response({"message": "Informe no encontrado."}, status=404)

        if informe.evaluacion.empresa_id != empresa.id:
            return Response({"message": "Informe no encontrado."}, status=404)

        serializer = InformeSerializer(informe)
        return Response(serializer.data)


class InformeFirmarView(PlanGatingMixin, APIView):
    """
    POST /api/informes/<id>/firmar/
    Captura la firma gráfica en canvas (base64) del Responsable SST o Alta Dirección,
    sellando la trazabilidad de fecha/hora, usuario y hash SHA-256.
    """
    permission_classes = [IsAuthenticated]
    required_feature = "tiene_informes"

    def post(self, request, informe_id):
        empresa = request.user.empresa
        if not empresa:
            return Response({"error": "Sin empresa asociada."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            informe = Informe.objects.select_related("evaluacion").get(id=informe_id)
        except Informe.DoesNotExist:
            return Response({"error": "Informe no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        if informe.evaluacion.empresa_id != empresa.id:
            return Response({"error": "No tiene permisos sobre este informe."}, status=status.HTTP_403_FORBIDDEN)

        tipo_firma = request.data.get("tipo_firma", "responsable")  # 'responsable' o 'direccion'
        imagen_firma_base64 = request.data.get("firma_base64", "")

        now = datetime.now()
        if tipo_firma == "responsable":
            informe.firmado_responsable = True
            informe.firma_responsable_data = imagen_firma_base64
            informe.firma_responsable_fecha = now
            informe.firma_responsable_usuario = request.user
        elif tipo_firma == "direccion":
            informe.firmado_direccion = True
            informe.firma_direccion_data = imagen_firma_base64
            informe.firma_direccion_fecha = now
            informe.firma_direccion_usuario = request.user
        else:
            return Response({"error": "tipo_firma inválido (debe ser 'responsable' o 'direccion')."}, status=status.HTTP_400_BAD_REQUEST)

        import hashlib
        raw_hash_data = f"{informe.id}-{now.isoformat()}-{request.user.id}".encode("utf-8")
        informe.hash_documento = hashlib.sha256(raw_hash_data).hexdigest()
        informe.save()

        serializer = InformeSerializer(informe)
        return Response(serializer.data, status=status.HTTP_200_OK)


class InformeDescargarPDFView(PlanGatingMixin, APIView):
    """
    GET /api/informes/<id>/descargar-pdf/
    Genera y sirve el archivo PDF estampado del informe con sus firmas y código hash.
    """
    permission_classes = [IsAuthenticated]
    required_feature = "tiene_informes"

    def get(self, request, informe_id):
        from django.http import HttpResponse
        from .firmas import generar_pdf_informe_firmado

        try:
            informe = Informe.objects.select_related("evaluacion", "firma_responsable_usuario", "firma_direccion_usuario").get(id=informe_id)
        except Informe.DoesNotExist:
            return Response({"error": "Informe no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        if informe.evaluacion.empresa_id != request.user.empresa_id:
            return Response({"error": "No tiene permisos para acceder a este informe."}, status=status.HTTP_403_FORBIDDEN)

        pdf_bytes = generar_pdf_informe_firmado(informe)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="informe_{informe.tipo}_{informe.id}.pdf"'
        return response

