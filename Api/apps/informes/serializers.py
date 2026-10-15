from rest_framework import serializers
from .models import Informe


class InformeSerializer(serializers.ModelSerializer):
    evaluacion_anio = serializers.IntegerField(source="evaluacion.anio", read_only=True)
    evaluacion_capitulo = serializers.CharField(source="evaluacion.capitulo", read_only=True)

    class Meta:
        model = Informe
        fields = "__all__"
        read_only_fields = ["id", "fecha_elaboracion", "deleted_at"]
