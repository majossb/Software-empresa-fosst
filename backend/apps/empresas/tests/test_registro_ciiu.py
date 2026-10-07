from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.empresas.models import Empresa
from apps.accounts.models import Usuario


class RegistroEmpresaAuditoria400Test(TestCase):
    """
    Suite de pruebas para el BUG CRÍTICO — ERROR 400 AL REGISTRAR EMPRESA.
    Cubre las 8 pruebas solicitadas en la auditoría.
    """

    def setUp(self):
        self.client = APIClient()

    # ── PRUEBA 1: Registro exitoso ──────────────────────────────────
    def test_prueba_1_registro_exitoso(self):
        """Registro exitoso con payload completo Dec 768 + CIIU Rev 4."""
        payload = {
            "nombre": "Industrias Andinas de Seguridad S.A.S.",
            "nit": "9018456723",
            "num_trabajadores": 32,
            "nivel_riesgo": 5,
            "ciiu_768_principal": "5251101",
            "ciiu_codigo": "2511",
            "ciiu_descripcion": "FABRICACIÓN DE PRODUCTOS METÁLICOS PARA USO ESTRUCTURAL",
            "sector_economico": "INDUSTRIAS MANUFACTURERAS",
            "responsable_nombre": "María José Bonilla Quintero",
            "responsable_documento": "1077225528",
            "responsable_email": "majoboquintero.prueba1@gmail.com",
            "responsable_password": "Password123!",
        }
        res = self.client.post("/api/empresa/registro", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn("empresa", res.data)

        empresa = Empresa.objects.get(nit="9018456723")
        self.assertEqual(empresa.ciiu_768_principal, "5251101")
        self.assertEqual(empresa.ciiu_codigo, "2511")
        self.assertEqual(empresa.nivel_riesgo, 5)
        self.assertEqual(empresa.capitulo_vigente, "III")

    # ── PRUEBA 2: Duplicidad NIT ────────────────────────────────────
    def test_prueba_2_duplicidad_nit(self):
        """NIT duplicado devuelve 400 con error descriptivo en campo 'nit'."""
        self.test_prueba_1_registro_exitoso()

        payload_dup = {
            "nombre": "Otra empresa",
            "nit": "9018456723",
            "num_trabajadores": 10,
            "nivel_riesgo": 1,
            "responsable_nombre": "Carlos Perez",
            "responsable_documento": "1099887766",
            "responsable_email": "otroemail@gmail.com",
            "responsable_password": "Password123!",
        }
        res = self.client.post("/api/empresa/registro", payload_dup, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("nit", res.data)
        self.assertEqual(res.data["nit"][0], "Ya existe una empresa con ese NIT.")

    # ── PRUEBA 3: Duplicidad email ──────────────────────────────────
    def test_prueba_3_duplicidad_email(self):
        """Email duplicado devuelve 400 con error descriptivo en campo 'responsable_email'."""
        self.test_prueba_1_registro_exitoso()

        payload_dup = {
            "nombre": "Otra Empresa S.A.S.",
            "nit": "900999888",
            "num_trabajadores": 10,
            "nivel_riesgo": 1,
            "responsable_nombre": "María José Bonilla",
            "responsable_documento": "1077225528",
            "responsable_email": "majoboquintero.prueba1@gmail.com",
            "responsable_password": "Password123!",
        }
        res = self.client.post("/api/empresa/registro", payload_dup, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("responsable_email", res.data)
        self.assertEqual(
            res.data["responsable_email"][0],
            "Ya existe un usuario con ese correo.",
        )

    # ── PRUEBA 4: Actividad válida ──────────────────────────────────
    def test_prueba_4_actividad_valida(self):
        """Registro con actividad económica válida (Dec 768 5251101 + CIIU 2511)."""
        payload = {
            "nombre": "Metalúrgica Bogotá S.A.S.",
            "nit": "900444555",
            "num_trabajadores": 20,
            "nivel_riesgo": 5,
            "ciiu_768_principal": "5251101",
            "ciiu_codigo": "2511",
            "ciiu_descripcion": "FABRICACIÓN DE PRODUCTOS METÁLICOS",
            "responsable_nombre": "Juan Pérez",
            "responsable_documento": "5500001",
            "responsable_email": "jperez@metalurgica.com",
            "responsable_password": "Password123!",
        }
        res = self.client.post("/api/empresa/registro", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        empresa = Empresa.objects.get(nit="900444555")
        self.assertEqual(empresa.ciiu_768_principal, "5251101")
        self.assertEqual(empresa.ciiu_codigo, "2511")

    # ── PRUEBA 5: Actividad inexistente (código vacío) ──────────────
    def test_prueba_5_sin_actividad(self):
        """Registro sin actividad económica también es válido (campos opcionales)."""
        payload = {
            "nombre": "Empresa Sin CIIU S.A.S.",
            "nit": "900777666",
            "num_trabajadores": 5,
            "nivel_riesgo": 1,
            "responsable_nombre": "Laura García",
            "responsable_documento": "12345678",
            "responsable_email": "laura@sinciiu.com",
            "responsable_password": "Password123!",
        }
        res = self.client.post("/api/empresa/registro", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    # ── PRUEBA 6: Campos obligatorios vacíos ────────────────────────
    def test_prueba_6_campos_obligatorios(self):
        """Campos obligatorios faltantes devuelven 400 con errores por campo."""
        payload = {
            "nombre": "",
            "nit": "900555666",
            "num_trabajadores": 0,
            "nivel_riesgo": 6,
            "responsable_nombre": "Test",
            "responsable_documento": "123456",
            "responsable_email": "invalido@test.com",
            "responsable_password": "123",
        }
        res = self.client.post("/api/empresa/registro", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("nombre", res.data)
        self.assertIn("num_trabajadores", res.data)
        self.assertIn("nivel_riesgo", res.data)

    # ── PRUEBA 7: Asociación empresa-usuario ────────────────────────
    def test_prueba_7_asociacion_empresa_usuario(self):
        """El usuario creado queda asociado a la empresa con rol RESPONSABLE."""
        payload = {
            "nombre": "Empresa Asociación S.A.S.",
            "nit": "901999111",
            "num_trabajadores": 15,
            "nivel_riesgo": 2,
            "responsable_nombre": "Laura Rodríguez",
            "responsable_documento": "52888999",
            "responsable_email": "laura@asociacion.com",
            "responsable_password": "Password123!",
        }
        res = self.client.post("/api/empresa/registro", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        empresa = Empresa.objects.get(nit="901999111")
        usuario = Usuario.objects.get(email="laura@asociacion.com")

        self.assertEqual(usuario.empresa_id, empresa.id)
        self.assertEqual(usuario.rol, "RESPONSABLE")
        self.assertTrue(usuario.check_password("Password123!"))

    # ── PRUEBA 8: Login del usuario creado ──────────────────────────
    def test_prueba_8_login_usuario_creado(self):
        """Login con el usuario creado en el registro produce OTP."""
        self.test_prueba_7_asociacion_empresa_usuario()

        # El LoginView requiere nit + documento + password
        res_login = self.client.post(
            "/api/auth/login/",
            {
                "nit": "901999111",
                "documento": "52888999",
                "password": "Password123!",
            },
            format="json",
        )
        self.assertEqual(res_login.status_code, status.HTTP_200_OK)
        self.assertIn("usuario_id", res_login.data)
