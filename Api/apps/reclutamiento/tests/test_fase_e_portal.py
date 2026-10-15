"""
Pruebas para el Portal Público del Candidato (Fase E) — Reclutamiento y Selección FOSST V.I.D.A.
Cubre:
- Listado y detalle público de ofertas laborales
- Postulación anónima con consentimiento obligatorio de Habeas Data (Ley 1581)
- Unificación en Banco de Talento de la empresa
- Autenticación Passwordless (OTP y Bearer token)
- Autoconsulta de postulaciones activas
- Retiro voluntario de postulación por parte del candidato
"""
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from apps.empresas.models import Empresa
from apps.organizacion.models import Sede
from apps.perfilcargo.models import PerfilCargo
from apps.reclutamiento.models import (
    Vacante,
    ProcesoSeleccion,
    Candidato,
    Postulacion,
    TokenAccesoCandidato,
)
from apps.reclutamiento.services.portal import generar_token_acceso_candidato


class FaseEPortalCandidatoTestCase(APITestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(
            nit="900333444-5",
            nombre="Constructora Andina S.A.S.",
            num_trabajadores=100,
            nivel_riesgo=5,
            capitulo_vigente="III",
        )
        self.sede = Sede.objects.create(
            empresa=self.empresa,
            nombre="Sede Principal",
            ciudad="Medellin",
        )
        self.cargo = PerfilCargo.objects.create(
            empresa=self.empresa,
            nombre_cargo="Coordinador de Alturas SST",
            codigo="SST-ALT-01",
            area="Operaciones SST",
            educacion="Profesional SST",
            experiencia="3 anios",
        )

        # Vacante pública abierta
        self.vacante_abierta = Vacante.objects.create(
            empresa=self.empresa,
            perfil_cargo=self.cargo,
            sede=self.sede,
            titulo="Coordinador de Trabajo Seguro en Alturas",
            descripcion_publica="Buscamos profesional con licencia SST y certificado de coordinador de alturas.",
            numero_cupos=2,
            estado=Vacante.Estado.ABIERTA,
            publicada_en_portal=True,
            mostrar_salario_publico=True,
            rango_salarial_min=3500000.0,
            rango_salarial_max=4500000.0,
        )
        self.proceso_abierto = ProcesoSeleccion.objects.create(
            empresa=self.empresa,
            vacante=self.vacante_abierta,
            requisitos_obligatorios=["Licencia SST vigente", "Coordinador de alturas 80h"],
        )

        # Vacante interna/borrador (no debe salir en el portal público)
        self.vacante_borrador = Vacante.objects.create(
            empresa=self.empresa,
            perfil_cargo=self.cargo,
            titulo="Vacante Confidencial Borrador",
            numero_cupos=1,
            estado=Vacante.Estado.BORRADOR,
            publicada_en_portal=False,
        )

    def test_listado_y_detalle_vacantes_publicas(self):
        """Solo se listan vacantes ABIERTAS y marcadas como publicada_en_portal."""
        url_list = reverse("portal-vacantes-list")
        res_list = self.client.get(url_list)

        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_list.data), 1)
        self.assertEqual(res_list.data[0]["codigo"], self.vacante_abierta.codigo)
        self.assertIn("Constructora Andina", res_list.data[0]["empresa_nombre"])

        # Detalle público por ID y por Slug
        url_detail_id = reverse("portal-vacantes-detail", kwargs={"slug_or_id": str(self.vacante_abierta.id)})
        res_detail_id = self.client.get(url_detail_id)
        self.assertEqual(res_detail_id.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_detail_id.data["requisitos_obligatorios"]), 2)

        url_detail_slug = reverse("portal-vacantes-detail", kwargs={"slug_or_id": self.vacante_abierta.slug})
        res_detail_slug = self.client.get(url_detail_slug)
        self.assertEqual(res_detail_slug.status_code, status.HTTP_200_OK)

        # Detalle de vacante borrador -> 404 Not Found
        url_borrador = reverse("portal-vacantes-detail", kwargs={"slug_or_id": str(self.vacante_borrador.id)})
        res_borrador = self.client.get(url_borrador)
        self.assertEqual(res_borrador.status_code, status.HTTP_404_NOT_FOUND)

    def test_postulacion_publica_habeas_data_exigido(self):
        """Rechaza postulación si el candidato no autoriza Habeas Data (Ley 1581 de 2012)."""
        url_postular = reverse("portal-vacantes-postular", kwargs={"slug_or_id": str(self.vacante_abierta.id)})
        payload_sin_habeas = {
            "tipo_documento": "CC",
            "documento": "1030405060",
            "nombres": "Ana",
            "apellidos": "Gomez",
            "email": "ana.gomez@email.com",
            "autoriza_tratamiento_datos": False,
        }
        res_fail = self.client.post(url_postular, payload_sin_habeas, format="json")
        self.assertEqual(res_fail.status_code, status.HTTP_400_BAD_REQUEST)

    def test_postulacion_publica_exitosa_y_unificacion_banco_talento(self):
        """Postulación pública exitosa registra en Banco de Talento y entrega credenciales OTP."""
        url_postular = reverse("portal-vacantes-postular", kwargs={"slug_or_id": str(self.vacante_abierta.id)})
        payload = {
            "tipo_documento": "CC",
            "documento": "1030405060",
            "nombres": "Ana Maria",
            "apellidos": "Gomez Perez",
            "email": "ana.gomez@email.com",
            "telefono": "3109876543",
            "ciudad": "Medellin",
            "autoriza_tratamiento_datos": True,
            "titulo_profesional": "Especialista SST",
            "nivel_educativo": "especializacion",
            "anios_experiencia": 4.0,
            "aspiracion_salarial": "4000000.00",
        }

        res_post = self.client.post(url_postular, payload, format="json")
        self.assertEqual(res_post.status_code, status.HTTP_201_CREATED)
        self.assertIn("postulacion_id", res_post.data)
        self.assertIn("token_acceso", res_post.data)
        self.assertIn("codigo_otp", res_post.data)

        # Verificar candidato en BD
        candidato = Candidato.objects.get(empresa=self.empresa, documento="1030405060")
        self.assertEqual(candidato.nombre_completo, "Ana Maria Gomez Perez")
        self.assertTrue(candidato.autoriza_tratamiento_datos)
        self.assertEqual(candidato.perfil.titulo_profesional, "Especialista SST")

        # Verificar postulación en estado inicial POSTULADO
        postulacion = Postulacion.objects.get(id=res_post.data["postulacion_id"])
        self.assertEqual(postulacion.estado, Postulacion.Estado.POSTULADO)

        # Si se postula de nuevo a la misma vacante, no duplica postulación
        res_post_repetida = self.client.post(url_postular, payload, format="json")
        self.assertEqual(res_post_repetida.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_post_repetida.data["postulacion_id"], str(postulacion.id))
        self.assertEqual(Postulacion.objects.filter(candidato=candidato).count(), 1)

    def test_flujo_autenticacion_otp_y_autoconsulta(self):
        """Flujo completo de solicitud de OTP, verificación y autoconsulta de postulaciones."""
        candidato = Candidato.objects.create(
            empresa=self.empresa,
            tipo_documento="CC",
            documento="55667788",
            nombres="Esteban",
            apellidos="Morales",
            email="esteban@email.com",
            autoriza_tratamiento_datos=True,
        )
        postulacion = Postulacion.objects.create(
            empresa=self.empresa,
            candidato=candidato,
            proceso_seleccion=self.proceso_abierto,
            estado=Postulacion.Estado.PRESELECCIONADO,
        )

        # 1. Solicitar OTP
        url_solicitar = reverse("portal-solicitar-acceso")
        res_sol = self.client.post(url_solicitar, {"email": "esteban@email.com"}, format="json")
        self.assertEqual(res_sol.status_code, status.HTTP_200_OK)
        codigo_otp = res_sol.data["codigo_otp"]

        # 2. Verificar OTP inválido -> 400
        url_verificar = reverse("portal-verificar-otp")
        res_otp_fail = self.client.post(
            url_verificar,
            {"email": "esteban@email.com", "codigo_otp": "000000"},
            format="json",
        )
        self.assertEqual(res_otp_fail.status_code, status.HTTP_400_BAD_REQUEST)

        # 3. Verificar OTP correcto -> 200 con Token de Sesión
        res_otp_ok = self.client.post(
            url_verificar,
            {"email": "esteban@email.com", "codigo_otp": codigo_otp},
            format="json",
        )
        self.assertEqual(res_otp_ok.status_code, status.HTTP_200_OK)
        session_token = res_otp_ok.data["token"]

        # 4. Consultar 'mis-postulaciones' sin token -> 401 Unauthorized / 403 Forbidden
        url_mis_post = reverse("portal-mis-postulaciones")
        res_unauth = self.client.get(url_mis_post)
        self.assertIn(res_unauth.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


        # 5. Consultar 'mis-postulaciones' con Bearer token -> 200 OK
        res_auth = self.client.get(url_mis_post, HTTP_AUTHORIZATION=f"Bearer {session_token}")
        self.assertEqual(res_auth.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_auth.data), 1)
        self.assertEqual(res_auth.data[0]["estado_publico"], "Preseleccionado")
        self.assertEqual(res_auth.data[0]["vacante_codigo"], self.vacante_abierta.codigo)

    def test_retiro_voluntario_de_candidatura(self):
        """Un candidato autenticado puede retirar voluntariamente su candidatura."""
        candidato = Candidato.objects.create(
            empresa=self.empresa,
            tipo_documento="CC",
            documento="33445566",
            nombres="Laura",
            apellidos="Restrepo",
            email="laura@email.com",
            autoriza_tratamiento_datos=True,
        )
        postulacion = Postulacion.objects.create(
            empresa=self.empresa,
            candidato=candidato,
            proceso_seleccion=self.proceso_abierto,
            estado=Postulacion.Estado.EN_ENTREVISTA,
        )

        token_sesion = generar_token_acceso_candidato(candidato=candidato)

        url_retirar = reverse("portal-retirar-postulacion", kwargs={"pk": postulacion.id})
        res_ret = self.client.post(
            url_retirar,
            {"motivo": "He aceptado otra oferta laboral"},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {token_sesion.token}",
        )

        self.assertEqual(res_ret.status_code, status.HTTP_200_OK)
        self.assertEqual(res_ret.data["postulacion"]["estado_publico"], "Candidatura Retirada")

        postulacion.refresh_from_db()
        self.assertEqual(postulacion.estado, Postulacion.Estado.RETIRO_CANDIDATURA)
        self.assertEqual(postulacion.motivo_cierre, "He aceptado otra oferta laboral")
