from rest_framework import serializers
from apps.planes.models import Plan, Suscripcion
from apps.accounts.models import Usuario
from .models import Empresa, AuditorEmpresa, SolicitudEliminacion


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = "__all__"


class SuscripcionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)

    class Meta:
        model = Suscripcion
        fields = "__all__"


class EmpresaSerializer(serializers.ModelSerializer):
    suscripciones = serializers.SerializerMethodField()
    _count = serializers.SerializerMethodField()

    class Meta:
        model = Empresa
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "deleted_at"]

    def get_suscripciones(self, obj):
        active_subs = obj.suscripciones.filter(estado="activa")[:1]
        return SuscripcionSerializer(active_subs, many=True).data

    def get__count(self, obj):
        # Conteo de sedes activas, procesos activos y organigrama activo
        return {
            "sedes": obj.sedes.filter(activa=True).count(),
            "procesos": obj.procesos.filter(activo=True).count(),
            "organigrama": obj.organigrama.filter(activo=True).count(),
        }


class RegistroEmpresaSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=255)
    nit = serializers.CharField(max_length=30)
    num_trabajadores = serializers.IntegerField(min_value=1)
    nivel_riesgo = serializers.IntegerField(min_value=1, max_value=5)
    representante_legal = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    arl = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    sector_economico = serializers.CharField(max_length=150, required=False, allow_blank=True, allow_null=True)
    ciudad = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    ciiu_codigo = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    ciiu_768_principal = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    ciiu_descripcion = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    responsable_nombre = serializers.CharField(max_length=255)
    responsable_documento = serializers.CharField(max_length=30)
    responsable_email = serializers.EmailField()
    responsable_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True, required=False)

    def validate_nit(self, value):
        # Strip non-digits so "900.123.456-7" and "900123456" son equivalentes
        clean_nit = ''.join(filter(str.isdigit, value))
        if Empresa.objects.filter(nit=clean_nit).exists():
            raise serializers.ValidationError(
                "Este NIT ya está registrado. Verifica el número ingresado o utiliza la empresa existente.",
                code="NIT_ALREADY_EXISTS",
            )
        return clean_nit

    def validate_responsable_email(self, value):
        if Usuario.objects.filter(email=value.lower().strip()).exists():
            raise serializers.ValidationError(
                "Este correo ya está registrado. Si ya tienes una cuenta, puedes iniciar sesión o recuperar tu contraseña.",
                code="EMAIL_ALREADY_EXISTS",
            )
        return value.lower().strip()

    def validate_responsable_documento(self, value):
        clean_doc = ''.join(filter(str.isdigit, value))
        if not clean_doc:
            raise serializers.ValidationError(
                "El documento debe contener únicamente números.",
                code="INVALID_DOCUMENT",
            )
        return clean_doc

    def validate_responsable_nombre(self, value):
        from apps.accounts.validators import validar_nombre_persona
        try:
            validar_nombre_persona(value, field_name="Nombre del responsable")
        except Exception as e:
            raise serializers.ValidationError(
                str(e.message if hasattr(e, 'message') else e),
                code="INVALID_NAME",
            )
        return value

    def validate_responsable_password(self, value):
        from apps.accounts.validators import validar_politica_password
        try:
            validar_politica_password(value)
        except Exception as e:
            raise serializers.ValidationError(
                str(e.message if hasattr(e, 'message') else e),
                code="INVALID_PASSWORD",
            )
        return value

    def validate(self, attrs):
        pwd = attrs.get("responsable_password")
        pwd_confirm = attrs.get("confirm_password") or attrs.get("responsable_confirm_password") or attrs.get("confirmPassword")
        if pwd_confirm is not None and pwd != pwd_confirm:
            raise serializers.ValidationError(
                {"confirm_password": "Las contraseñas no coinciden."},
            )
        return attrs

