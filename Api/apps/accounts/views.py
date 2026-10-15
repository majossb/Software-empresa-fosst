import secrets
from datetime import timedelta

from django.contrib.auth import authenticate, get_user_model
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings 
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema

from apps.auditoria.models import AuditLog
from apps.seguridad.models import EventoRiesgo
from .models import CodigoOTP, TokenActivacion, TokenRecuperacion
from .serializers import (
    ActivarCuentaSerializer,
    ConfirmarResetPasswordSerializer,
    LoginSerializer,
    RegistroSerializer,
    SolicitarResetPasswordSerializer,
    UsuarioSerializer,
    VerificarOTPSerializer,
)
from .tasks import enviar_email_task


Usuario = get_user_model()


def _tokens_para(usuario):
    refresh = RefreshToken.for_user(usuario)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


def _ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    return xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR")



class RegistroView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "register"

    @extend_schema(
        request=RegistroSerializer,
        responses={
            201: {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string"
                    }
                }
            }
        },
    )
    def post(self, request):
        serializer = RegistroSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            usuario = serializer.save()

            token = TokenActivacion.objects.create(
                usuario=usuario,
                token=secrets.token_urlsafe(32),
                expira_en=timezone.now()
                + timedelta(hours=settings.ACTIVATION_TOKEN_EXPIRATION_HOURS),
            )

            AuditLog.objects.create(
                usuario=usuario,
                empresa=usuario.empresa,
                accion=AuditLog.Accion.REGISTRO,
                ip=_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )

        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173").rstrip("/")
        enlace = f"{frontend_url}/activar-cuenta?token={token.token}"

        cuerpo = render_to_string(
            "emails/activacion_cuenta.txt",
            {
                "usuario": usuario,
                "enlace": enlace,
            },
        )

        enviar_email_task.delay(
            "Activa tu cuenta en DiagnostISST",
            cuerpo,
            usuario.email,
        )

        return Response(
            {
                "message": "Registro exitoso. Revisa tu correo para activar la cuenta."
            },
            status=status.HTTP_201_CREATED,
        )
    
class ActivarCuentaView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=ActivarCuentaSerializer,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string"
                    }
                }
            }
        },
    )
    def post(self, request):
        token_str = request.data.get("token")

        token = (
            TokenActivacion.objects
            .filter(token=token_str)
            .select_related("usuario")
            .first()
        )

        if not token or not token.esta_vigente():
            return Response(
                {
                    "success": False,
                    "code": "INVALID_ACTIVATION_TOKEN",
                    "message": "El enlace de activación es inválido o ha expirado.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        usuario = token.usuario

        with transaction.atomic():
            usuario.activo = True
            usuario.is_active = True
            usuario.email_verificado = True
            usuario.save(update_fields=["activo", "is_active", "email_verificado"])

            token.usado = True
            token.save(update_fields=["usado"])

            AuditLog.objects.create(
                usuario=usuario,
                empresa=usuario.empresa,
                accion=AuditLog.Accion.ACTIVACION_CUENTA,
                ip=_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )

        return Response(
            {
                "success": True,
                "message": "Cuenta activada correctamente. Ya puedes iniciar sesión.",
            },
            status=status.HTTP_200_OK,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    @extend_schema(request=LoginSerializer, responses={200: None})
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        rol = data.get("rol")
        if not rol:
            usuario_temp = Usuario.objects.filter(
                empresa__nit=data["nit"],
                documento=data["documento"],
                deleted_at__isnull=True,
            ).first()
            if usuario_temp:
                rol = usuario_temp.rol
            else:
                return self._fallo(request, None)

        usuario = Usuario.objects.filter(
            empresa__nit=data["nit"],
            documento=data["documento"],
            rol=rol,
            deleted_at__isnull=True,
        ).first()

        if not usuario:
            # Igual se llama a authenticate con un username inexistente para que
            # django-axes registre el intento también por IP, aunque no exista el usuario.
            authenticate(
                request=request,
                username=f"{data['documento']}_{data['nit']}",
                password=data["password"],
            )
            return self._fallo(request, None)

        usuario_autenticado = authenticate(
            request=request,
            username=usuario.username,
            password=data["password"],
        )

        if usuario_autenticado is None:
            if usuario and usuario.check_password(data["password"]) and (not usuario.activo or not usuario.is_active):
                return Response(
                    {
                        "success": False,
                        "code": "ACCOUNT_NOT_ACTIVATED",
                        "message": "Tu cuenta aún no ha sido activada. Revisa tu correo electrónico para activarla.",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
            return self._fallo(request, usuario)

        if not usuario.activo or not usuario.is_active:
            return Response(
                {
                    "success": False,
                    "code": "ACCOUNT_NOT_ACTIVATED",
                    "message": "Tu cuenta aún no ha sido activada. Revisa tu correo electrónico para activarla.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        otp = CodigoOTP.crear_para(
            usuario,
            CodigoOTP.Proposito.LOGIN,
        )

        cuerpo = render_to_string(
            "emails/codigo_otp.txt",
            {
                "usuario": usuario,
                "codigo": otp.codigo,
            },
        )

        enviar_email_task.delay(
            "Tu código de verificación DiagnostISST",
            cuerpo,
            usuario.email,
        )

        return Response(
            {
                "success": True,
                "message": "Credenciales válidas. Se envió un código de verificación a tu correo.",
                "usuario_id": str(usuario.id),
                "otp_expira_en_minutos": settings.OTP_EXPIRATION_MINUTES,
                "expires_at": otp.expira_en.isoformat(),
            }
        )

    def _fallo(self, request, usuario):
        if usuario:
            EventoRiesgo.objects.create(
                usuario=usuario,
                tipo=EventoRiesgo.Tipo.MULTIPLES_FALLOS,
                ip=_ip(request),
            )

            AuditLog.objects.create(
                usuario=usuario,
                empresa=usuario.empresa,
                accion=AuditLog.Accion.LOGIN_FALLIDO,
                ip=_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                ruta=request.path,
                metodo_http=request.method,
            )

        return Response(
            {
                "success": False,
                "code": "INVALID_CREDENTIALS",
                "message": "Credenciales incorrectas.",
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )

class VerificarOTPView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp"

    @extend_schema(
        request=VerificarOTPSerializer,
        responses={200: None},
    )

    def post(self, request):
        serializer = VerificarOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        MENSAJE_GENERICO = "El código ingresado no es válido o ha expirado."

        otp = CodigoOTP.objects.filter(
            usuario_id=data["usuario_id"], proposito=CodigoOTP.Proposito.LOGIN,
            usado=False,
        ).order_by("-created_at").first()

        if not otp or not otp.esta_vigente():
            return Response(
                {
                    "success": False,
                    "code": "INVALID_OTP",
                    "message": MENSAJE_GENERICO,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not otp.verificar_codigo(data["codigo"]):
            otp.intentos += 1
            if otp.intentos >= CodigoOTP.MAX_INTENTOS:
                otp.usado = True  # Invalidar tras máximos intentos
                EventoRiesgo.objects.create(
                    usuario=otp.usuario,
                    tipo=EventoRiesgo.Tipo.OTP_FALLIDO_REPETIDO,
                    ip=_ip(request),
                )
            otp.save(update_fields=["intentos", "usado"])
            return Response(
                {
                    "success": False,
                    "code": "INVALID_OTP",
                    "message": MENSAJE_GENERICO,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


        otp.usado = True
        otp.save(update_fields=["usado"])

        usuario = otp.usuario
        tokens = _tokens_para(usuario)

        AuditLog.objects.create(usuario=usuario, empresa=usuario.empresa,
                                 accion=AuditLog.Accion.LOGIN, ip=_ip(request),
                                 user_agent=request.META.get("HTTP_USER_AGENT", ""))
        request.login_exitoso = True
        request.user = usuario

        return Response({**tokens, "user": UsuarioSerializer(usuario).data})


class LogoutView(APIView):
    def post(self, request):
        refresh = request.data.get("refresh")

        if refresh:
            try:
                RefreshToken(refresh).blacklist()
            except Exception:
                pass

        AuditLog.objects.create(
            usuario=request.user,
            empresa=request.user.empresa,
            accion=AuditLog.Accion.LOGOUT,
            ip=_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            ruta=request.path,
            metodo_http=request.method,
        )

        return Response({"message": "Sesión cerrada."})


class MeView(APIView):
    def get(self, request):
        return Response(UsuarioSerializer(request.user).data)


class SolicitarResetPasswordView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset"

    @extend_schema(
        request=SolicitarResetPasswordSerializer,
        responses={200: None},
    )

    def post(self, request):
        serializer = SolicitarResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        usuario = Usuario.objects.filter(
            email=serializer.validated_data["email"],
            activo=True,
        ).first()

        if usuario:
            token = TokenRecuperacion.objects.create(
                usuario=usuario,
                token=secrets.token_urlsafe(32),
                expira_en=timezone.now()
                + timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRATION_HOURS),
            )

            frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173").rstrip("/")
            enlace = f"{frontend_url}/reset-password?token={token.token}"

            cuerpo = render_to_string(
                "emails/reset_password.txt",
                {
                    "usuario": usuario,
                    "enlace": enlace,
                },
            )

            enviar_email_task.delay(
                "Recupera tu contraseña - DiagnostISST",
                cuerpo,
                usuario.email,
            )

        return Response(
            {
                "message": (
                    "Si el correo existe, se enviaron instrucciones "
                    "de recuperación."
                )
            }
        )


class ConfirmarResetPasswordView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=ConfirmarResetPasswordSerializer,
        responses={200: None},
    )

    def post(self, request):
        serializer = ConfirmarResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        token = (
            TokenRecuperacion.objects.filter(token=data["token"])
            .select_related("usuario")
            .first()
        )

        if not token or not token.esta_vigente():
            return Response(
                {
                    "message": (
                        "El enlace de recuperación es inválido "
                        "o ha expirado."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        usuario = token.usuario

        usuario.set_password(data["password"])
        usuario.save(update_fields=["password"])

        token.usado = True
        token.save(update_fields=["usado"])

        AuditLog.objects.create(
            usuario=usuario,
            empresa=usuario.empresa,
            accion=AuditLog.Accion.CAMBIO_PASSWORD,
            ip=_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            ruta=request.path,
            metodo_http=request.method,
        )

        return Response(
            {
                "message": "Contraseña actualizada correctamente."
            }
        )