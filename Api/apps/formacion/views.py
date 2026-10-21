from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Avg, Count, Max, Q

from apps.accounts.models import UserRole
from apps.common.mixins import EmpresaScopedViewSet
from apps.common.competencias import parse_nivel, obtener_nombre_nivel
from apps.capacitaciones.models import Trabajador
from apps.perfilcargo.models import PerfilCargo, CargoCompetencia
from .models import EvaluacionCompetencia
from .serializers import EvaluacionCompetenciaSerializer
from .permissions import (
    es_jefe_inmediato,
    obtener_subordinados_de_usuario,
    verificar_permiso_evaluar
)


class EvaluacionCompetenciaViewSet(EmpresaScopedViewSet):
    """
    ViewSet para la gestión de evaluaciones de competencias del cargo (MCC).
    """
    queryset = EvaluacionCompetencia.objects.all()
    serializer_class = EvaluacionCompetenciaSerializer
    empresa_field = "trabajador__empresa"
    filterset_fields = ["trabajador", "cargo_competencia", "metodo", "rol_evaluador"]

    def get_queryset(self):
        qs = super().get_queryset().select_related(
            "trabajador", "cargo_competencia", "evaluado_por", "trabajador__empresa", "cargo_competencia__perfil_cargo"
        )
        user = self.request.user
        if not user or not user.is_authenticated:
            return qs.none()

        # Gestión Humana / Admin / Auditor / Alta Dirección ven todas las evaluaciones de la empresa
        if getattr(user, "rol", None) in [UserRole.RESPONSABLE, UserRole.ADMIN, UserRole.AUDITOR, UserRole.ALTA_DIRECCION] or user.is_staff:
            return qs

        # Jefe inmediato solo ve trabajadores a su cargo (y sus propias evaluaciones)
        subordinados = obtener_subordinados_de_usuario(user)
        return qs.filter(
            Q(trabajador__in=subordinados) | Q(evaluado_por=user)
        )

    def perform_create(self, serializer):
        trabajador = serializer.validated_data.get("trabajador")
        metodo = serializer.validated_data.get("metodo", EvaluacionCompetencia.MetodoEvaluacion.EVALUACION_360)

        rol_evaluador = verificar_permiso_evaluar(self.request.user, trabajador, metodo)

        serializer.save(
            evaluado_por=self.request.user,
            rol_evaluador=rol_evaluador
        )

    @action(detail=False, methods=["get"], url_path="matriz-trabajador/(?P<trabajador_id>[^/.]+)")
    def matriz_trabajador(self, request, trabajador_id=None):
        """
        Devuelve la matriz de competencias del trabajador con todas las competencias
        de su cargo actual, nivel requerido, última evaluación, nivel alcanzado y brecha.
        """
        empresa = request.user.empresa
        try:
            trabajador = Trabajador.objects.select_related("perfil_cargo").get(pk=trabajador_id, empresa=empresa)
        except Trabajador.DoesNotExist:
            return Response({"error": "Trabajador no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        es_gh = getattr(user, "rol", None) in [UserRole.RESPONSABLE, UserRole.ADMIN, UserRole.AUDITOR, UserRole.ALTA_DIRECCION] or user.is_staff
        es_jefe = es_jefe_inmediato(user, trabajador)
        usuario_trabajador = trabajador.resolver_usuario()
        es_propio = (usuario_trabajador and usuario_trabajador.id == user.id) or (trabajador.documento == user.documento)

        if not (es_gh or es_jefe or es_propio):
            return Response(
                {"error": "No tiene autorización para consultar las competencias de este trabajador."},
                status=status.HTTP_403_FORBIDDEN
            )

        if not trabajador.perfil_cargo:
            return Response({"error": "El trabajador no tiene perfil de cargo asignado"}, status=status.HTTP_400_BAD_REQUEST)

        competencias = CargoCompetencia.objects.filter(perfil_cargo=trabajador.perfil_cargo)
        matriz = []

        for comp in competencias:
            req = parse_nivel(comp.nivel_requerido or comp.nivel, default=3)
            evals = EvaluacionCompetencia.objects.filter(
                trabajador=trabajador, cargo_competencia=comp
            ).order_by("-fecha_evaluacion", "-created_at")

            ultima_eval = evals.first()
            ultima_eval_oficial = evals.exclude(metodo=EvaluacionCompetencia.MetodoEvaluacion.AUTOEVALUACION).first()

            alcanzado = ultima_eval.nivel_alcanzado if ultima_eval else 0
            brecha = max(0, req - alcanzado) if ultima_eval else req

            # Autoevaluación no cuenta como cumplimiento por sí sola
            cumple = False
            if ultima_eval_oficial and ultima_eval_oficial.nivel_alcanzado >= req:
                cumple = True

            matriz.append({
                "competencia_id": comp.id,
                "nombre": comp.nombre,
                "tipo": comp.tipo or "tecnica",
                "tipo_display": comp.get_tipo_display() if hasattr(comp, 'get_tipo_display') else comp.tipo,
                "descripcion": comp.descripcion or "",
                "nivel_requerido": req,
                "nivel_requerido_nombre": obtener_nombre_nivel(req),
                "nivel_alcanzado": alcanzado,
                "nivel_alcanzado_nombre": obtener_nombre_nivel(alcanzado) if alcanzado else "Sin evaluar",
                "brecha": brecha,
                "cumple": cumple,
                "solo_autoevaluado": (ultima_eval is not None and ultima_eval_oficial is None and ultima_eval.metodo == EvaluacionCompetencia.MetodoEvaluacion.AUTOEVALUACION),
                "ultima_evaluacion": EvaluacionCompetenciaSerializer(ultima_eval).data if ultima_eval else None,
            })

        return Response({
            "trabajador": {
                "id": str(trabajador.id),
                "nombre": trabajador.nombre,
                "documento": trabajador.documento,
                "cargo": trabajador.perfil_cargo.nombre_cargo,
                "perfil_cargo_id": str(trabajador.perfil_cargo.id),
            },
            "competencias": matriz,
        })

    @action(detail=False, methods=["get"], url_path="resumen")
    def resumen(self, request):
        """Resumen consolidado de competencias de la empresa."""
        qs = self.get_queryset()
        total_evaluaciones = qs.count()
        con_brecha = qs.filter(brecha_calculada__gt=0).count()
        promedio_brecha = qs.aggregate(avg=Avg("brecha_calculada"))["avg"] or 0.0

        return Response({
            "total_evaluaciones": total_evaluaciones,
            "evaluaciones_con_brecha": con_brecha,
            "evaluaciones_optimas": total_evaluaciones - con_brecha,
            "promedio_brecha": round(promedio_brecha, 2),
        })


class CursoFormacionViewSet(EmpresaScopedViewSet):
    """
    Catálogo de cursos y certificaciones de formación por empresa.
    Incluye semilla automática para empresas que aún no posean catálogo.
    """
    from .models import CursoFormacion
    from .serializers import CursoFormacionSerializer
    queryset = CursoFormacion.objects.all()
    serializer_class = CursoFormacionSerializer
    empresa_field = "empresa"
    filterset_fields = ["categoria", "activo", "requiere_certificado"]
    search_fields = ["nombre", "descripcion"]

    def get_queryset(self):
        user = self.request.user
        if user and user.is_authenticated and hasattr(user, "empresa") and user.empresa:
            from .models import CursoFormacion, poblar_catalogo_formacion_semilla
            if not CursoFormacion.objects.filter(empresa=user.empresa).exists():
                poblar_catalogo_formacion_semilla(user.empresa)
        return super().get_queryset()

    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.empresa)


class CargoRequisitoFormacionViewSet(EmpresaScopedViewSet):
    """
    Requisitos de formación y certificaciones exigidos por el Perfil del Cargo.
    """
    from .models import CargoRequisitoFormacion
    from .serializers import CargoRequisitoFormacionSerializer
    queryset = CargoRequisitoFormacion.objects.all()
    serializer_class = CargoRequisitoFormacionSerializer
    empresa_field = "perfil_cargo__empresa"
    filterset_fields = ["perfil_cargo", "curso", "obligatorio", "grupo_alternativo"]


class RegistroFormacionViewSet(EmpresaScopedViewSet):
    """
    Registros de cursos y certificaciones realizados por los trabajadores.
    Soporta filtros por trabajador, cargo, curso y estado derivado (vigente/por_vencer/vencido).
    """
    from .models import RegistroFormacion
    from .serializers import RegistroFormacionSerializer
    queryset = RegistroFormacion.objects.all()
    serializer_class = RegistroFormacionSerializer
    empresa_field = "trabajador__empresa"
    filterset_fields = ["trabajador", "curso", "origen"]

    def get_queryset(self):
        from datetime import timedelta
        from django.utils import timezone
        qs = super().get_queryset().select_related("trabajador", "curso", "soporte", "trabajador__perfil_cargo")

        cargo = self.request.query_params.get("cargo")
        if cargo:
            qs = qs.filter(Q(trabajador__perfil_cargo_id=cargo) | Q(trabajador__cargo__icontains=cargo))

        estado = self.request.query_params.get("estado")
        if estado:
            today = timezone.now().date()
            limite_por_vencer = today + timedelta(days=30)
            if estado == "vigente":
                qs = qs.filter(Q(fecha_vencimiento__isnull=True) | Q(fecha_vencimiento__gt=limite_por_vencer))
            elif estado == "por_vencer":
                qs = qs.filter(fecha_vencimiento__gte=today, fecha_vencimiento__lte=limite_por_vencer)
            elif estado == "vencido":
                qs = qs.filter(fecha_vencimiento__lt=today)

        return qs

    @action(detail=False, methods=["get"], url_path="matriz-trabajador/(?P<trabajador_id>[^/.]+)")
    def matriz_trabajador(self, request, trabajador_id=None):
        """
        Calcula la matriz de formación completa del trabajador:
        cursos exigidos por su cargo, estado de vigencia, alternativas cumplidas y faltantes.
        """
        empresa = request.user.empresa
        try:
            trabajador = Trabajador.objects.select_related("perfil_cargo").get(pk=trabajador_id, empresa=empresa)
        except Trabajador.DoesNotExist:
            return Response({"error": "Trabajador no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        from .services import calcular_matriz_formacion_trabajador
        data = calcular_matriz_formacion_trabajador(trabajador)
        return Response(data)

    @action(detail=False, methods=["get"], url_path="resumen")
    def resumen(self, request):
        """Resumen global de estados de formación en la empresa."""
        from datetime import timedelta
        from django.utils import timezone
        qs = self.get_queryset()
        today = timezone.now().date()
        limite_por_vencer = today + timedelta(days=30)

        total = qs.count()
        vencidos = qs.filter(fecha_vencimiento__lt=today).count()
        por_vencer = qs.filter(fecha_vencimiento__gte=today, fecha_vencimiento__lte=limite_por_vencer).count()
        vigentes = qs.filter(Q(fecha_vencimiento__isnull=True) | Q(fecha_vencimiento__gt=limite_por_vencer)).count()

        return Response({
            "total_registros": total,
            "vigentes": vigentes,
            "por_vencer": por_vencer,
            "vencidos": vencidos,
        })

