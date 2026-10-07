from datetime import datetime
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.storage import validate_and_process_file, verify_file_integrity
from apps.estandares.models import Evaluacion, Respuesta
from .models import Archivo, Evidencia
from .serializers import EvidenciaSerializer


class EvidenciaListCreateView(APIView):
    """
    GET  /api/evidencias       → lista evidencias activas del año actual.
    POST /api/evidencias       → crea evidencia con archivo procesado en S3/MinIO y hash SHA-256.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        empresa = request.user.empresa
        if not empresa:
            return Response({"message": "Sin empresa asociada."}, status=status.HTTP_400_BAD_REQUEST)

        anio_actual = datetime.now().year

        try:
            evaluacion = Evaluacion.objects.get(empresa=empresa, anio=anio_actual)
        except Evaluacion.DoesNotExist:
            return Response({"evidencias": [], "total": 0})

        respuestas = Respuesta.objects.filter(
            evaluacion=evaluacion
        ).select_related("estandar").prefetch_related("evidencias__archivo")

        evidencias = []
        for resp in respuestas:
            for ev in resp.evidencias.filter(deleted_at__isnull=True):
                if ev.archivo and ev.archivo.deleted_at is not None:
                    continue
                evidencias.append({
                    "id": str(ev.id),
                    "descripcion": ev.descripcion,
                    "created_at": ev.created_at,
                    "estandar_codigo": resp.estandar.codigo,
                    "estandar_nombre": resp.estandar.nombre,
                    "respuesta_id": str(resp.id),
                    "estado_estandar": resp.estado,
                    "archivo": {
                        "id": str(ev.archivo.id),
                        "nombre": ev.archivo.nombre,
                        "url": ev.archivo.url,
                        "tipo_mime": ev.archivo.tipo_mime,
                        "tamanio_kb": ev.archivo.tamanio_kb,
                        "sha256_hash": ev.archivo.sha256_hash,
                    } if ev.archivo else None,
                    "fecha_ocurrencia": ev.fecha_ocurrencia,
                    "responsable": ev.responsable,
                    "firma": ev.firma,
                })

        return Response({
            "evidencias": evidencias,
            "total": len(evidencias),
            "evaluacion_id": str(evaluacion.id),
        })

    def post(self, request):
        empresa = request.user.empresa
        if not empresa:
            return Response({"message": "Sin empresa asociada."}, status=status.HTTP_400_BAD_REQUEST)

        respuesta_id = request.data.get("respuesta_id")
        nombre = request.data.get("nombre", "")
        descripcion = request.data.get("descripcion", "")
        url = request.data.get("url", "")
        tipo_mime = request.data.get("tipo_mime", "application/pdf")
        tamanio_kb = request.data.get("tamanio_kb", 0)
        fecha_ocurrencia = request.data.get("fecha_ocurrencia")
        responsable = request.data.get("responsable")
        firma = request.data.get("firma")

        try:
            respuesta = Respuesta.objects.select_related("evaluacion").get(id=respuesta_id)
        except Respuesta.DoesNotExist:
            return Response({"message": "Respuesta no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        if respuesta.evaluacion.empresa_id != empresa.id:
            return Response({"message": "No tiene permisos sobre esta respuesta."}, status=status.HTTP_403_FORBIDDEN)

        uploaded_file = request.FILES.get("archivo")
        if uploaded_file:
            # Procesamiento centralizado en storage (S3/MinIO + SHA-256 + validaciones)
            processed = validate_and_process_file(uploaded_file, folder="evidencias")
            final_url = processed["url"]
            final_mime = processed["mime_type"]
            final_size = round(processed["size_bytes"] / 1024)
            sha256_hash = processed["sha256_hash"]
            file_name = processed["original_name"]
        else:
            file_name = nombre or "archivo"
            final_url = url
            final_mime = tipo_mime
            final_size = int(tamanio_kb) if tamanio_kb else 0
            sha256_hash = request.data.get("sha256_hash")

        archivo = Archivo.objects.create(
            nombre=file_name,
            url=final_url,
            tipo_mime=final_mime,
            tamanio_kb=final_size,
            subido_por=str(request.user.id),
            sha256_hash=sha256_hash,
        )

        evidencia = Evidencia.objects.create(
            respuesta=respuesta,
            archivo=archivo,
            descripcion=descripcion,
            fecha_ocurrencia=fecha_ocurrencia,
            responsable=responsable,
            firma=firma,
        )

        serializer = EvidenciaSerializer(evidencia)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class EvidenciaDeleteView(APIView):
    """DELETE /api/evidencias/<id> → marcado lógico (soft-delete) de la evidencia."""
    permission_classes = [IsAuthenticated]

    def delete(self, request, evidencia_id):
        empresa = request.user.empresa
        if not empresa:
            return Response({"message": "Sin empresa asociada."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            evidencia = Evidencia.objects.select_related(
                "respuesta__evaluacion", "archivo"
            ).get(id=evidencia_id, deleted_at__isnull=True)
        except Evidencia.DoesNotExist:
            return Response({"message": "Evidencia no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        if evidencia.respuesta.evaluacion.empresa_id != empresa.id:
            return Response({"message": "No tiene permisos para eliminar esta evidencia."}, status=status.HTTP_403_FORBIDDEN)

        # Soft delete en lugar de borrado físico real
        evidencia.delete()
        if evidencia.archivo:
            evidencia.archivo.delete()

        return Response({"message": "Evidencia eliminada correctamente (marcado lógico)."})


class EvidenciaVerificarIntegridadView(APIView):
    """GET /api/evidencias/<id>/verificar-integridad → valida hash SHA-256."""
    permission_classes = [IsAuthenticated]

    def get(self, request, evidencia_id):
        try:
            evidencia = Evidencia.objects.select_related(
                "respuesta__evaluacion", "archivo"
            ).get(id=evidencia_id, deleted_at__isnull=True)
        except Evidencia.DoesNotExist:
            return Response({"message": "Evidencia no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        if evidencia.respuesta.evaluacion.empresa_id != request.user.empresa_id:
            return Response({"message": "Acceso denegado."}, status=status.HTTP_403_FORBIDDEN)

        archivo = evidencia.archivo
        if not archivo or not archivo.sha256_hash:
            return Response({
                "integro": False,
                "message": "La evidencia no cuenta con un hash registrado."
            })

        storage_key = archivo.url.lstrip('/')
        if storage_key.startswith('media/'):
            storage_key = storage_key[6:]

        is_valid = verify_file_integrity(storage_key, archivo.sha256_hash)
        return Response({
            "evidencia_id": str(evidencia.id),
            "sha256_hash": archivo.sha256_hash,
            "integro": is_valid,
            "message": "Verificación de integridad exitosa." if is_valid else "Advertencia: El hash del archivo no coincide."
        })
