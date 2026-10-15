"""
Pruebas de integración de Endpoints REST (Fase D) — Reclutamiento y Selección FOSST V.I.D.A.
Cubre:
- Multi-tenancy en todos los ViewSets
- CRUD Banco de Talento y búsqueda
- Ciclo de vida de Vacante y Proceso de Selección
- Transiciones REST vía endpoints de acción de Postulacion (RN-R01 a RN-R09)
- Semáforo de etapas en respuestas
- Restricción estricta de estado read_only en Postulación
"""
import uuid
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status

from apps.empresas.models import Empresa
from apps.organizacion.models import Sede
from apps.perfilcargo.models import PerfilCargo
from apps.reclutamiento.models import (
    FuenteReclutamiento,
    Candidato,
    PerfilCandidato,
    Vacante,
    ProcesoSeleccion,
    Postulacion,
    PostulacionEvento,
    Entrevista,
    Evaluacion,
    ValidacionDocumental,
)

Usuario = get_user_model()


class FaseDEndpointsTestCase(APITestCase):
    def setUp(self):
        # Empresa A y usuarios
        self.empresa_a = Empresa.objects.create(
            nit="900111222-1",
            nombre="Empresa Alpha S.A.S.",
            num_trabajadores=50,
            nivel_riesgo=3,
            capitulo_vigente="II",
        )
        self.user_rh_a = Usuario.objects.create_user(
            username="rh_alpha",
            email="rh@alpha.com",
            password="Password123!",
            rol="responsable",
            empresa=self.empresa_a,
        )
        self.user_auditor_a = Usuario.objects.create_user(
            username="auditor_alpha",
            email="auditor@alpha.com",
            password="Password123!",
            rol="auditor",
            empresa=self.empresa_a,
        )

        # Empresa B y usuario (para prueba multi-tenant)
        self.empresa_b = Empresa.objects.create(
            nit="900999888-2",
            nombre="Empresa Beta S.A.S.",
            num_trabajadores=20,
            nivel_riesgo=2,
            capitulo_vigente="I",
        )
        self.user_rh_b = Usuario.objects.create_user(
            username="rh_beta",
            email="rh@beta.com",
            password="Password123!",
            rol="responsable",
            empresa=self.empresa_b,
        )

        # Configuración común
        self.sede_a = Sede.objects.create(
            empresa=self.empresa_a,
            nombre="Sede Central",
            ciudad="Bogota",
        )
        self.cargo_a = PerfilCargo.objects.create(
            empresa=self.empresa_a,
            nombre_cargo="Inspector SST",
            codigo="SST-001",
            area="Seguridad y Salud",
            educacion="Tecnologo SST",
            experiencia="2 anios",
        )

        self.fuente_a = FuenteReclutamiento.objects.create(
            empresa=self.empresa_a,
            nombre="LinkedIn",
        )

        self.client.force_authenticate(user=self.user_rh_a)

    def test_banco_talento_crud_y_busqueda(self):
        """Prueba creación, detalle y búsqueda de candidatos en Banco de Talento."""
        payload = {
            "tipo_documento": "CC",
            "documento": "1020304050",
            "nombres": "Camila",
            "apellidos": "Rojas",
            "email": "camila.rojas@email.com",
            "telefono": "3001234567",
            "ciudad": "Bogota",
            "autoriza_tratamiento_datos": True,
            "etiquetas": ["SST", "Alturas", "Auditor"],
            "perfil": {
                "titulo_profesional": "Ingeniera Ambiental y SST",
                "nivel_educativo": "universitario",
                "anios_experiencia": 3.5,
                "competencias": ["Liderazgo", "GTC 45"],
            },
        }

        # Crear candidato
        url_list = reverse("reclutamiento-candidato-list")
        res_create = self.client.post(url_list, payload, format="json")
        self.assertEqual(res_create.status_code, status.HTTP_201_CREATED)
        candidato_id = res_create.data["id"]

        # Recuperar detalle
        url_detail = reverse("reclutamiento-candidato-detail", kwargs={"pk": candidato_id})
        res_detail = self.client.get(url_detail)
        self.assertEqual(res_detail.status_code, status.HTTP_200_OK)
        self.assertEqual(res_detail.data["nombre_completo"], "Camila Rojas")
        self.assertEqual(res_detail.data["perfil"]["titulo_profesional"], "Ingeniera Ambiental y SST")

        # Búsqueda por texto libre
        res_search = self.client.get(f"{url_list}?search=Camila")
        self.assertEqual(res_search.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_search.data), 1)

        # Filtro por etiqueta
        res_tag = self.client.get(f"{url_list}?etiqueta=Alturas")
        self.assertEqual(res_tag.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_tag.data), 1)

    def test_aislamiento_multitenant_candidatos(self):
        """Un usuario de Empresa B no puede ver ni modificar candidatos de Empresa A."""
        candidato_a = Candidato.objects.create(
            empresa=self.empresa_a,
            tipo_documento="CC",
            documento="77889900",
            nombres="Pedro",
            apellidos="Perez",
            email="pedro@empresa.com",
        )

        # Autenticar como RH Empresa B
        self.client.force_authenticate(user=self.user_rh_b)

        # Intentar listar
        url_list = reverse("reclutamiento-candidato-list")
        res_list = self.client.get(url_list)
        self.assertEqual(len(res_list.data), 0)

        # Intentar detalle
        url_detail = reverse("reclutamiento-candidato-detail", kwargs={"pk": candidato_a.id})
        res_detail = self.client.get(url_detail)
        self.assertEqual(res_detail.status_code, status.HTTP_404_NOT_FOUND)

    def test_vacante_creacion_y_cambios_estado(self):
        """Prueba creación de vacante con auto_crear_proceso y acciones de estado."""
        payload = {
            "perfil_cargo": str(self.cargo_a.id),
            "sede": str(self.sede_a.id),
            "titulo": "Vacante Inspector SST Obra",
            "descripcion_publica": "Requerimos profesional con licencia SST vigente.",
            "numero_cupos": 2,
            "tipo_contrato": "Obra o Labor",
            "modalidad": "presencial",
            "rango_salarial_min": "2500000.00",
            "rango_salarial_max": "3000000.00",
            "auto_crear_proceso": True,
        }

        url_list = reverse("reclutamiento-vacante-list")
        res_create = self.client.post(url_list, payload, format="json")
        self.assertEqual(res_create.status_code, status.HTTP_201_CREATED)
        vacante_id = res_create.data["id"]

        vacante = Vacante.objects.get(id=vacante_id)
        self.assertTrue(hasattr(vacante, "proceso_seleccion"))
        self.assertEqual(vacante.estado, Vacante.Estado.BORRADOR)

        # Publicar vacante
        url_pub = reverse("reclutamiento-vacante-publicar", kwargs={"pk": vacante_id})
        res_pub = self.client.post(url_pub)
        self.assertEqual(res_pub.status_code, status.HTTP_200_OK)
        self.assertEqual(res_pub.data["estado"], "abierta")
        self.assertTrue(res_pub.data["publicada_en_portal"])

        # Pausar vacante
        url_pause = reverse("reclutamiento-vacante-pausar", kwargs={"pk": vacante_id})
        res_pause = self.client.post(url_pause)
        self.assertEqual(res_pause.status_code, status.HTTP_200_OK)
        self.assertEqual(res_pause.data["estado"], "pausada")

    def test_flujo_completo_postulacion_via_endpoints(self):
        """
        Prueba el flujo integral de selección vía API REST:
        1. Crear candidato y vacante con proceso.
        2. Postular candidato.
        3. Preseleccionar (RN-R02).
        4. Registrar y calificar entrevista.
        5. Registrar y calificar prueba técnica.
        6. Registrar y validar antecedentes.
        7. Verificar semáforo de etapas.
        8. Seleccionar candidato (RN-R06).
        9. Comprobar auditoría y eventos inmutables.
        """
        # 1. Candidato y Vacante
        candidato = Candidato.objects.create(
            empresa=self.empresa_a,
            tipo_documento="CC",
            documento="111222333",
            nombres="Julian",
            apellidos="Alvarez",
            email="julian@email.com",
        )
        vacante = Vacante.objects.create(
            empresa=self.empresa_a,
            perfil_cargo=self.cargo_a,
            sede=self.sede_a,
            titulo="Inspector SST Proyecto",
            numero_cupos=1,
            estado=Vacante.Estado.ABIERTA,
        )
        proceso = ProcesoSeleccion.objects.create(
            empresa=self.empresa_a,
            vacante=vacante,
            requiere_entrevista=True,
            requiere_evaluacion=True,
            requiere_validacion_documental=True,
        )

        # 2. Postular
        url_postular = reverse("reclutamiento-proceso-postular", kwargs={"pk": proceso.id})
        res_post = self.client.post(url_postular, {"candidato_id": str(candidato.id)}, format="json")
        self.assertEqual(res_post.status_code, status.HTTP_201_CREATED)
        postulacion_id = res_post.data["id"]

        # Verificar estado inicial POSTULADO
        self.assertEqual(res_post.data["estado"], "postulado")

        # RN-R01: Intentar cambiar 'estado' por PATCH directo debe no tener efecto
        url_postulacion_detail = reverse("reclutamiento-postulacion-detail", kwargs={"pk": postulacion_id})
        self.client.patch(url_postulacion_detail, {"estado": "seleccionado"}, format="json")
        post_check = Postulacion.objects.get(id=postulacion_id)
        self.assertEqual(post_check.estado, Postulacion.Estado.POSTULADO)

        # 3. Preseleccionar (RN-R02)
        url_pre = reverse("reclutamiento-postulacion-preseleccionar", kwargs={"pk": postulacion_id})
        res_pre = self.client.post(
            url_pre,
            {
                "calificacion_requisitos": {"experiencia_2_anios": True, "licencia_sst": True},
                "puntuacion": 95.0,
            },
            format="json",
        )
        self.assertEqual(res_pre.status_code, status.HTTP_200_OK)
        self.assertEqual(res_pre.data["estado"], "preseleccionado")

        # 4. Registrar Entrevista
        url_entrevista = reverse("reclutamiento-postulacion-registrar-entrevista", kwargs={"pk": postulacion_id})
        res_ent = self.client.post(
            url_entrevista,
            {
                "tipo_entrevista": "tecnica",
                "modalidad": "virtual",
                "fecha_programada": timezone.now().isoformat(),
                "calificacion": 88.0,
                "concepto": "favorable",
                "observaciones": "Demuestra solidez en normativa SST",
            },
            format="json",
        )
        self.assertEqual(res_ent.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_ent.data["postulacion"]["estado"], "en_entrevista")

        # 5. Registrar Evaluación
        url_eval = reverse("reclutamiento-postulacion-registrar-evaluacion", kwargs={"pk": postulacion_id})
        res_eval = self.client.post(
            url_eval,
            {
                "tipo_evaluacion": "tecnica",
                "nombre_prueba": "Prueba Conocimientos GTC 45 y Decreto 1072",
                "puntaje_obtenido": "85.00",
                "puntaje_maximo": "100.00",
                "porcentaje_aprobacion": "70.00",
                "concepto": "Aprobado con honores",
            },
            format="json",
        )
        self.assertEqual(res_eval.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_eval.data["postulacion"]["estado"], "en_evaluacion")

        # 6. Registrar Validación Documental
        url_val = reverse("reclutamiento-postulacion-registrar-validacion", kwargs={"pk": postulacion_id})
        res_val = self.client.post(
            url_val,
            {
                "tipo_verificacion": "antecedentes",
                "entidad_o_contacto": "Policia Nacional y Procuraduria",
                "estado": "verificado_conforme",
                "detalles_verificacion": "Sin antecedentes judiciales ni fiscales",
            },
            format="json",
        )
        self.assertEqual(res_val.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_val.data["postulacion"]["estado"], "en_validacion")

        # 7. Verificar Semáforo de Etapas
        res_detail = self.client.get(url_postulacion_detail)
        semaforo = res_detail.data["semaforo_etapas"]
        self.assertEqual(semaforo["entrevista"]["estado"], "completada")
        self.assertEqual(semaforo["evaluacion"]["estado"], "completada")
        self.assertEqual(semaforo["validacion_documental"]["estado"], "completada")

        # 8. Seleccionar Candidato (RN-R06)
        url_sel = reverse("reclutamiento-postulacion-seleccionar", kwargs={"pk": postulacion_id})
        res_sel = self.client.post(url_sel, {"notas_finales": "Aprobado por el comité de contratación"}, format="json")
        self.assertEqual(res_sel.status_code, status.HTTP_200_OK)
        self.assertEqual(res_sel.data["estado"], "seleccionado")

        # Verificar que la vacante quedó cubierta
        vacante.refresh_from_db()
        self.assertEqual(vacante.estado, Vacante.Estado.CUBIERTA)
        self.assertEqual(vacante.numero_seleccionados, 1)

        # 9. Comprobar Trazabilidad (Eventos)
        res_final = self.client.get(url_postulacion_detail)
        eventos = res_final.data["eventos"]
        self.assertGreaterEqual(len(eventos), 5)
        tipos = [e["tipo_evento"] for e in eventos]
        self.assertIn("postulacion_registrada", tipos)
        self.assertIn("decision_seleccion", tipos)

    def test_cierre_y_reapertura_excepcional_endpoints(self):
        """Prueba endpoints de cierre (RN-R04) y reapertura excepcional (RN-R07/RN-R09)."""
        candidato = Candidato.objects.create(
            empresa=self.empresa_a,
            tipo_documento="CC",
            documento="99887766",
            nombres="Mariana",
            apellidos="Lopez",
            email="mariana@email.com",
        )
        vacante = Vacante.objects.create(
            empresa=self.empresa_a,
            perfil_cargo=self.cargo_a,
            titulo="Vacante Mariana",
            numero_cupos=1,
            estado=Vacante.Estado.ABIERTA,
        )
        proceso = ProcesoSeleccion.objects.create(
            empresa=self.empresa_a,
            vacante=vacante,
        )
        postulacion = Postulacion.objects.create(
            empresa=self.empresa_a,
            candidato=candidato,
            proceso_seleccion=proceso,
            estado=Postulacion.Estado.POSTULADO,
        )

        # Cierre sin motivo -> 400 Bad Request
        url_cerrar = reverse("reclutamiento-postulacion-cerrar", kwargs={"pk": postulacion.id})
        res_fail = self.client.post(
            url_cerrar,
            {"nuevo_estado": "no_seleccionado", "motivo": ""},
            format="json",
        )
        self.assertEqual(res_fail.status_code, status.HTTP_400_BAD_REQUEST)

        # Cierre exitoso con motivo
        res_cerrar = self.client.post(
            url_cerrar,
            {"nuevo_estado": "no_seleccionado", "motivo": "No cumple con la experiencia requerida"},
            format="json",
        )
        self.assertEqual(res_cerrar.status_code, status.HTTP_200_OK)
        self.assertEqual(res_cerrar.data["estado"], "no_seleccionado")

        # Reapertura sin justificación -> 400 Bad Request
        url_reabrir = reverse("reclutamiento-postulacion-reabrir", kwargs={"pk": postulacion.id})
        res_reabrir_fail = self.client.post(
            url_reabrir,
            {"justificacion": ""},
            format="json",
        )
        self.assertEqual(res_reabrir_fail.status_code, status.HTTP_400_BAD_REQUEST)

        # Reapertura exitosa con justificación (RN-R07)
        res_reabrir_ok = self.client.post(
            url_reabrir,
            {"justificacion": "Aclaracion de certificacion laboral aportada por el candidato"},
            format="json",
        )
        self.assertEqual(res_reabrir_ok.status_code, status.HTTP_200_OK)
        self.assertEqual(res_reabrir_ok.data["estado"], "en_revision")
        self.assertTrue(res_reabrir_ok.data["es_excepcion"])
