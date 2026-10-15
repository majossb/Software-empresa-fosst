from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.empresas.models import Empresa
from apps.accounts.models import Usuario, UserRole


class BrandingEmpresaTest(TestCase):
    """
    Suite de pruebas para el endpoint de Branding e Identidad Visual por Empresa (FASE 1).
    Prueba:
      1. Valores por defecto FOSST si la empresa no tiene branding.
      2. Actualización exitosa con valores hexadecimales válidos.
      3. Rechazo HTTP 400 ante colores HEX inválidos.
      4. Rechazo HTTP 400 ante claves no reconocidas.
      5. Aislamiento multi-tenant entre empresas.
      6. Permisos (GET autenticado, PUT corporativo).
    """

    def setUp(self):
        self.client_a = APIClient()
        self.client_b = APIClient()

        # Empresa A
        self.empresa_a = Empresa.objects.create(
            nombre="Empresa Alpha S.A.S.",
            nit="900111222",
            num_trabajadores=15,
            nivel_riesgo=3,
            capitulo_vigente="II",
            estado=Empresa.Estado.ACTIVA,
        )
        self.user_a_resp = Usuario.objects.create_user(
            username="resp_alpha",
            email="resp.alpha@empresa-a.com",
            password="Password123!",
            rol=UserRole.RESPONSABLE,
            empresa=self.empresa_a,
            activo=True,
            is_active=True,
        )
        self.user_a_auditor = Usuario.objects.create_user(
            username="auditor_alpha",
            email="auditor.alpha@empresa-a.com",
            password="Password123!",
            rol=UserRole.AUDITOR,
            empresa=self.empresa_a,
            activo=True,
            is_active=True,
        )

        # Empresa B
        self.empresa_b = Empresa.objects.create(
            nombre="Empresa Beta S.A.S.",
            nit="900333444",
            num_trabajadores=5,
            nivel_riesgo=1,
            capitulo_vigente="I",
            estado=Empresa.Estado.ACTIVA,
        )
        self.user_b_resp = Usuario.objects.create_user(
            username="resp_beta",
            email="resp.beta@empresa-b.com",
            password="Password123!",
            rol=UserRole.RESPONSABLE,
            empresa=self.empresa_b,
            activo=True,
            is_active=True,
        )

    # 1. GET sin branding previo -> valores por defecto FOSST
    def test_get_branding_default(self):
        self.client_a.force_authenticate(user=self.user_a_resp)
        res = self.client_a.get("/api/modulo0/branding")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["preset"], "azul_fosst")
        self.assertEqual(res.data["primario"], "#002D62")
        self.assertEqual(res.data["secundario"], "#0284C7")
        self.assertEqual(res.data["acento"], "#F5A800")
        self.assertIn("mapa_procesos", res.data)
        self.assertEqual(res.data["mapa_procesos"]["estrategico"], "#002D62")

    # 2. PUT con paleta hexadecimal válida
    def test_put_branding_valido(self):
        self.client_a.force_authenticate(user=self.user_a_resp)
        payload = {
            "preset": "oceano_profundo",
            "primario": "#0B3C5D",
            "secundario": "#1D7A8C",
            "acento": "#F2A541",
            "mapa_procesos": {
                "estrategico": "#0B3C5D",
                "misional": "#1D7A8C",
                "apoyo": "#4C8C6B",
                "fondo": "#F8FAFC",
                "texto_entradas": "Entradas personalizadas",
            }
        }
        res = self.client_a.put("/api/modulo0/branding", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["preset"], "oceano_profundo")
        self.assertEqual(res.data["primario"], "#0B3C5D")
        self.assertEqual(res.data["secundario"], "#1D7A8C")
        self.assertEqual(res.data["acento"], "#F2A541")
        self.assertEqual(res.data["mapa_procesos"]["texto_entradas"], "Entradas personalizadas")

        # Verificar persistencia en base de datos
        self.empresa_a.refresh_from_db()
        self.assertEqual(self.empresa_a.branding["primario"], "#0B3C5D")

    # 3. Rechazo HTTP 400 ante HEX inválido
    def test_put_branding_hex_invalido(self):
        self.client_a.force_authenticate(user=self.user_a_resp)
        payload_invalid = {
            "primario": "002D62",  # Falta #
            "secundario": "#XYZ123",  # Caracteres no hex
        }
        res = self.client_a.put("/api/modulo0/branding", payload_invalid, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data.get("code"), "INVALID_HEX_COLOR")

    # 4. Rechazo HTTP 400 ante claves no reconocidas
    def test_put_branding_claves_desconocidas(self):
        self.client_a.force_authenticate(user=self.user_a_resp)
        payload_unknown = {
            "primario": "#002D62",
            "clave_rara": "valor_no_permitido",
        }
        res = self.client_a.put("/api/modulo0/branding", payload_unknown, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data.get("code"), "UNKNOWN_KEYS")

    # 5. Aislamiento multi-tenant entre empresas
    def test_branding_multi_tenant_isolation(self):
        # Empresa A actualiza su branding
        self.client_a.force_authenticate(user=self.user_a_resp)
        self.client_a.put("/api/modulo0/branding", {"primario": "#1F4D3A"}, format="json")

        # Empresa B consulta su propio branding y debe seguir obteniendo defaults (no los de Empresa A)
        self.client_b.force_authenticate(user=self.user_b_resp)
        res_b = self.client_b.get("/api/modulo0/branding")
        self.assertEqual(res_b.status_code, status.HTTP_200_OK)
        self.assertEqual(res_b.data["primario"], "#002D62")  # Default FOSST

    # 6. Permisos (GET auth, PUT solo corporativo)
    def test_branding_permisos(self):
        # Usuario sin autenticar -> 401
        res_unauth = self.client.get("/api/modulo0/branding")
        self.assertEqual(res_unauth.status_code, status.HTTP_401_UNAUTHORIZED)

        # Auditor de Empresa A intenta PUT -> 403 Forbidden (Auditor no es EsCorporativo)
        self.client_a.force_authenticate(user=self.user_a_auditor)
        res_put_auditor = self.client_a.put("/api/modulo0/branding", {"primario": "#000000"}, format="json")
        self.assertEqual(res_put_auditor.status_code, status.HTTP_403_FORBIDDEN)

        # Auditor de Empresa A intenta GET -> 200 OK
        res_get_auditor = self.client_a.get("/api/modulo0/branding")
        self.assertEqual(res_get_auditor.status_code, status.HTTP_200_OK)
