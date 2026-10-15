from rest_framework import serializers
from .models import Archivo, Evidencia


class ArchivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Archivo
        fields = "__all__"


class EvidenciaSerializer(serializers.ModelSerializer):
    archivo = ArchivoSerializer(read_only=True)
    estandar_codigo = serializers.CharField(source="respuesta.estandar.codigo", read_only=True)
    estandar_nombre = serializers.CharField(source="respuesta.estandar.nombre", read_only=True)
    estado_estandar = serializers.CharField(source="respuesta.estado", read_only=True)

    class Meta:
        model = Evidencia
        fields = "__all__"
