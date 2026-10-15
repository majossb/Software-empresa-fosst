from datetime import datetime

from django.core.cache import cache
from django.db.models import Sum, Count, Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsRol
from apps.estandares.models import Estandar, Evaluacion, Respuesta
from apps.hallazgos.models import Hallazgo, PlanMejora
from apps.informes.views import calcular_phva


CACHE_TTL = 300  # 5 minutos


# ── GET /api/dashboard/alta-direccion ─────────────────────────────
class DashboardAltaDireccionView(APIView):
    """Dashboard para la alta dirección con KPIs, PHVA, sanciones y tendencias."""
    permission_classes = [IsAuthenticated, IsRol.de("alta_direccion")]

    def get(self, request):
        empresa = request.user.empresa
        if not empresa:
            return Response({"message": "Sin empresa asociada."}, status=400)

        anio_actual = datetime.now().year
        cache_key = f"dashboard_ad_{empresa.id}_{anio_actual}"
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        capitulo = empresa.capitulo_vigente or "II"

        # Estándares (cacheable por capítulo)
        est_cache_key = f"estandares_{capitulo}"
        estandares = cache.get(est_cache_key)
        if not estandares:
            estandares = list(Estandar.objects.filter(capitulo=capitulo).order_by("ciclo_phva", "codigo"))
            cache.set(est_cache_key, estandares, CACHE_TTL)

        # Evaluación actual
        evaluacion = Evaluacion.objects.filter(
            empresa=empresa, anio=anio_actual
        ).prefetch_related("respuestas").first()

        respuestas = list(evaluacion.respuestas.all()) if evaluacion else []

        # PHVA
        phva = calcular_phva(respuestas, estandares)

        # Cumplimiento global
        puntaje_maximo = sum(float(e.puntaje_maximo) for e in estandares)
        puntaje_obtenido = sum(float(r.puntaje or 0) for r in respuestas)
        cumplimiento_global = round((puntaje_obtenido / puntaje_maximo) * 100) if puntaje_maximo > 0 else 0

        # Estándares críticos
        estandares_criticos = []
        for est in estandares:
            resp = next((r for r in respuestas if r.estandar_id == est.id), None)
            puntaje_est = float(resp.puntaje or 0) if resp else 0
            max_est = float(est.puntaje_maximo)
            porcentaje = round((puntaje_est / max_est) * 100) if max_est > 0 else 0
            estado_est = resp.estado if resp else "no_cumple"

            if estado_est == "no_cumple" or porcentaje < 30:
                estandares_criticos.append({
                    "codigo": est.codigo,
                    "nombre": est.nombre,
                    "ciclo": est.ciclo_phva,
                    "puntaje_maximo": max_est,
                    "puntaje_obtenido": puntaje_est,
                    "estado": estado_est,
                    "porcentaje": porcentaje,
                })

        estandares_criticos.sort(key=lambda x: x["porcentaje"])
        estandares_criticos = estandares_criticos[:8]

        # Conteos
        total_estandares = len(estandares)
        cumplidos = sum(1 for r in respuestas if r.estado == "cumple")
        no_cumple = sum(1 for r in respuestas if r.estado == "no_cumple")
        parciales = sum(1 for r in respuestas if r.estado == "parcial")

        # Sanción potencial (500 SMMLV × proporción incumplimiento)
        SMMLV = 1_423_500  # 2025
        sancion_maxima = 500 * SMMLV
        factor_incumplimiento = (no_cumple / total_estandares) if total_estandares > 0 else 0
        sancion_potencial = round(sancion_maxima * factor_incumplimiento)
        multas_evitadas = sancion_maxima - sancion_potencial

        # Plan mejora
        plan_mejora = list(
            PlanMejora.objects.filter(empresa=empresa, deleted_at__isnull=True)
            .values("estado")
            .annotate(_count=Count("id"))
        )

        # Historial de evaluaciones
        historial = list(
            Evaluacion.objects.filter(empresa=empresa)
            .order_by("anio")
            .values("anio", "puntaje_total", "estado")[:6]
        )

        result = {
            "empresa": {
                "nombre": empresa.nombre,
                "nit": empresa.nit,
                "capitulo_vigente": capitulo,
                "num_trabajadores": empresa.num_trabajadores,
                "nivel_riesgo": empresa.nivel_riesgo,
            },
            "cumplimiento": {
                "global": cumplimiento_global,
                "puntaje_obtenido": round(puntaje_obtenido, 2),
                "puntaje_maximo": round(puntaje_maximo, 2),
                "total_estandares": total_estandares,
                "cumplidos": cumplidos,
                "no_cumple": no_cumple,
                "parciales": parciales,
            },
            "phva": phva,
            "estandares_criticos": estandares_criticos,
            "sancion": {
                "potencial": sancion_potencial,
                "evitada": multas_evitadas,
                "smmlv": SMMLV,
                "factor": round(factor_incumplimiento * 100),
            },
            "plan_mejora": plan_mejora,
            "historial": historial,
            "evaluacion_id": str(evaluacion.id) if evaluacion else None,
        }

        cache.set(cache_key, result, CACHE_TTL)
        return Response(result)


# ── GET /api/dashboard/responsable ────────────────────────────────
class DashboardResponsableView(APIView):
    """Dashboard para el responsable SST con KPIs operativos."""
    permission_classes = [IsAuthenticated, IsRol.de("responsable")]

    def get(self, request):
        empresa = request.user.empresa
        if not empresa:
            return Response({"message": "Sin empresa asociada."}, status=400)

        anio_actual = datetime.now().year
        capitulo = empresa.capitulo_vigente or "II"

        # Planes urgentes y capacitaciones próximas en paralelo
        planes_urgentes = list(
            PlanMejora.objects.filter(
                empresa=empresa,
                estado__in=["pendiente", "en_progreso"],
                deleted_at__isnull=True,
            ).order_by("fecha_limite")[:5].values()
        )

        # Import inline para evitar circular
        from apps.capacitaciones.models import Capacitacion
        capacitaciones = list(
            Capacitacion.objects.filter(
                empresa=empresa,
                estado="programada",
                deleted_at__isnull=True,
            ).order_by("fecha")[:5].values()
        )

        # Evaluación actual
        evaluacion, _ = Evaluacion.objects.get_or_create(
            empresa=empresa,
            anio=anio_actual,
            defaults={"capitulo": capitulo},
        )

        estandares = list(Estandar.objects.filter(capitulo=capitulo).order_by("ciclo_phva", "codigo"))
        respuestas = list(
            Respuesta.objects.filter(evaluacion=evaluacion)
            .select_related("estandar")
            .prefetch_related("evidencias")
        )

        resp_map = {r.estandar_id: r for r in respuestas}

        estandares_con_respuesta = []
        total_evidencias = 0
        for est in estandares:
            resp = resp_map.get(est.id)
            evidencias_count = resp.evidencias.count() if resp and hasattr(resp, "evidencias") else 0
            total_evidencias += evidencias_count
            puntaje_est = float(resp.puntaje or 0) if resp else 0
            max_est = float(est.puntaje_maximo)

            estandares_con_respuesta.append({
                "id": str(est.id),
                "codigo": est.codigo,
                "nombre": est.nombre,
                "ciclo_phva": est.ciclo_phva,
                "puntaje_maximo": max_est,
                "respuesta_id": str(resp.id) if resp else None,
                "estado": resp.estado if resp else "no_cumple",
                "puntaje": puntaje_est,
                "observacion": resp.observacion if resp else "",
                "evidencias": evidencias_count,
                "porcentaje": round((puntaje_est / max_est) * 100) if max_est > 0 else 0,
            })

        total_estandares = len(estandares)
        cumplidos = sum(1 for e in estandares_con_respuesta if e["estado"] == "cumple")
        urgentes = sum(1 for e in estandares_con_respuesta if e["estado"] == "no_cumple")

        puntaje_maximo = sum(float(e.puntaje_maximo) for e in estandares)
        puntaje_obtenido = sum(e["puntaje"] for e in estandares_con_respuesta)
        avance_global = round((puntaje_obtenido / puntaje_maximo) * 100) if puntaje_maximo > 0 else 0

        return Response({
            "empresa": {"nombre": empresa.nombre, "capitulo_vigente": capitulo},
            "evaluacion_id": str(evaluacion.id),
            "kpis": {
                "avance_global": avance_global,
                "cumplidos": cumplidos,
                "total_estandares": total_estandares,
                "urgentes": urgentes,
                "evidencias_cargadas": total_evidencias,
            },
            "estandares": estandares_con_respuesta,
            "planes_urgentes": planes_urgentes,
            "capacitaciones_proximas": capacitaciones,
        })


# ── GET /api/dashboard/auditor ────────────────────────────────────
class DashboardAuditorView(APIView):
    """Dashboard para auditores con tabla de verificación y hallazgos."""
    permission_classes = [IsAuthenticated, IsRol.de("auditor")]

    def get(self, request):
        empresa = request.user.empresa
        if not empresa:
            return Response({"message": "Sin empresa asociada."}, status=400)

        anio_actual = datetime.now().year
        capitulo = empresa.capitulo_vigente or "II"

        evaluacion = Evaluacion.objects.filter(
            empresa=empresa, anio=anio_actual
        ).prefetch_related(
            "respuestas__evidencias",
            "hallazgos__auditor",
        ).first()

        estandares = list(Estandar.objects.filter(capitulo=capitulo).order_by("ciclo_phva", "codigo"))
        respuestas = list(evaluacion.respuestas.all()) if evaluacion else []
        hallazgos = list(evaluacion.hallazgos.all()) if evaluacion else []

        resp_map = {r.estandar_id: r for r in respuestas}

        # Tabla de verificación
        tabla_verificacion = []
        total_evidencias = 0
        for est in estandares:
            resp = resp_map.get(est.id)
            evidencias_count = resp.evidencias.count() if resp and hasattr(resp, "evidencias") else 0
            total_evidencias += evidencias_count

            hallazgo_est = next(
                (h for h in hallazgos if est.codigo in h.descripcion),
                None,
            )

            tabla_verificacion.append({
                "codigo": est.codigo,
                "nombre": est.nombre,
                "ciclo_phva": est.ciclo_phva,
                "puntaje_maximo": float(est.puntaje_maximo),
                "estado_empresa": resp.estado if resp else "sin_respuesta",
                "puntaje": float(resp.puntaje or 0) if resp else 0,
                "documentos": evidencias_count,
                "hallazgo_id": str(hallazgo_est.id) if hallazgo_est else None,
            })

        # Resumen hallazgos
        resumen_hallazgos = {
            "total": len(hallazgos),
            "no_conformidad": sum(1 for h in hallazgos if "no_conformidad" in h.tipo),
            "observacion": sum(1 for h in hallazgos if h.tipo == "observacion"),
            "oportunidad": sum(1 for h in hallazgos if h.tipo == "oportunidad_mejora"),
            "fortaleza": sum(1 for h in hallazgos if h.tipo == "fortaleza"),
        }

        puntaje_maximo = sum(float(e.puntaje_maximo) for e in estandares)
        puntaje_obtenido = sum(float(r.puntaje or 0) for r in respuestas)
        cumplimiento = round((puntaje_obtenido / puntaje_maximo) * 100) if puntaje_maximo > 0 else 0

        return Response({
            "empresa": {"nombre": empresa.nombre, "capitulo_vigente": capitulo},
            "evaluacion_id": str(evaluacion.id) if evaluacion else None,
            "kpis": {
                "cumplimiento_general": cumplimiento,
                "evidencias_revisadas": total_evidencias,
                "hallazgos": resumen_hallazgos,
            },
            "tabla_verificacion": tabla_verificacion,
            "hallazgos_detalle": [
                {
                    "id": str(h.id),
                    "tipo": h.tipo,
                    "descripcion": h.descripcion,
                    "auditor": (h.auditor.get_full_name() or h.auditor.username) if getattr(h, "auditor", None) else "Auditor",
                    "created_at": h.created_at.isoformat(),
                }
                for h in hallazgos
            ],
        })
