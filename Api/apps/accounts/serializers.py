from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.empresas.models import Empresa
from .models import UserRole

Usuario = get_user_model()


class RegistroSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
    )

    empresa_nit = serializers.SlugRelatedField(
        source="empresa",
        slug_field="nit",
        queryset=Empresa.objects.filter(estado="activa"),
        write_only=True,
    )

    class Meta:
        model = Usuario
        fields = [
            "tipo_documento",
            "documento",
            "first_name",
            "last_name",
            "email",
            "telefono",
            "rol",
            "password",
            "empresa_nit",
        ]

    def validate_rol(self, rol):
        if rol == UserRole.ADMIN:
            raise serializers.ValidationError(
                "No es posible autoregistrarse como administrador."
            )
        return rol

    def create(self, validated_data):
        empresa = validated_data.pop("empresa")
        password = validated_data.pop("password")

        username = f"{validated_data['documento']}_{empresa.nit}"

        usuario = Usuario(
            username=username,
            empresa=empresa,
            is_active=False,
            email_verificado=False,
            **validated_data,
        )

        usuario.set_password(password)
        usuario.save()

        return usuario


class LoginSerializer(serializers.Serializer):
    nit = serializers.CharField()
    documento = serializers.CharField()
    password = serializers.CharField(write_only=True)
    rol = serializers.ChoiceField(choices=UserRole.choices, required=False)


class ActivarCuentaSerializer(serializers.Serializer):
    token = serializers.CharField(
        max_length=255,
        trim_whitespace=True,
        help_text="Token de activación enviado por correo electrónico."
    )


class VerificarOTPSerializer(serializers.Serializer):
    usuario_id = serializers.UUIDField()
    codigo = serializers.RegexField(
        regex=r"^\d{6}$",
        error_messages={
            "invalid": "El código debe contener exactamente 6 dígitos."
        },
    )


class SolicitarResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ConfirmarResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField()
    confirm_password = serializers.CharField(write_only=True, required=False)

    def validate_password(self, value):
        from .validators import validar_politica_password
        try:
            validar_politica_password(value)
        except Exception as e:
            raise serializers.ValidationError(str(e.message if hasattr(e, 'message') else e))
        return value

    def validate(self, attrs):
        pwd = attrs.get("password")
        pwd_confirm = attrs.get("confirm_password") or attrs.get("passwordConfirm")
        if pwd_confirm is not None and pwd != pwd_confirm:
            raise serializers.ValidationError({"confirm_password": "Las contraseñas no coinciden."})
        return attrs


class EmpresaResumenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = [
            "id",
            "nombre",
            "nit",
        ]


class UsuarioSerializer(serializers.ModelSerializer):
    nombre = serializers.SerializerMethodField()
    empresa = EmpresaResumenSerializer(read_only=True)

    class Meta:
        model = Usuario
        fields = [
            "id",
            "nombre",
            "first_name",
            "last_name",
            "tipo_documento",
            "documento",
            "email",
            "telefono",
            "rol",
            "empresa",
            "activo",
            "email_verificado",
            "otp_habilitado",
            "created_at",
        ]
        read_only_fields = fields

    def get_nombre(self, obj):
        return obj.get_full_name().strip() or obj.username