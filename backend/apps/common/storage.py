import hashlib
import os
from typing import Dict, Any, Optional, Union
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import UploadedFile
from rest_framework.exceptions import ValidationError

def validate_and_process_file(
    file_obj: Union[UploadedFile, ContentFile, bytes],
    folder: str = "general",
    filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Procesa, valida metadatos (tamaño, MIME), calcula SHA-256 y guarda el archivo
    mediante el backend de almacenamiento configurado (S3/MinIO via django-storages).
    
    Retorna un diccionario con los metadatos completos para ser persistidos en PostgreSQL.
    """
    if isinstance(file_obj, bytes):
        content = file_obj
        original_name = filename or "file.bin"
        mime_type = "application/octet-stream"
        size_bytes = len(content)
    elif isinstance(file_obj, ContentFile):
        content = file_obj.read()
        file_obj.seek(0)
        original_name = filename or getattr(file_obj, "name", "file.bin")
        mime_type = getattr(file_obj, "content_type", "application/octet-stream")
        size_bytes = len(content)
    else:  # UploadedFile (InMemoryUploadedFile / TemporaryUploadedFile)
        content = file_obj.read()
        file_obj.seek(0)
        original_name = filename or file_obj.name
        mime_type = getattr(file_obj, "content_type", "application/octet-stream")
        size_bytes = file_obj.size

    # Validar tamaño máximo
    max_bytes = getattr(settings, "MAX_UPLOAD_SIZE_MB", 20) * 1024 * 1024
    if size_bytes > max_bytes:
        raise ValidationError(
            f"El archivo supera el tamaño máximo permitido de {settings.MAX_UPLOAD_SIZE_MB}MB."
        )

    # Validar tipo MIME
    allowed_mimes = getattr(
        settings,
        "ALLOWED_UPLOAD_MIME_TYPES",
        [
            "application/pdf",
            "image/jpeg",
            "image/png",
            "image/webp",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/csv",
        ]
    )
    if mime_type not in allowed_mimes:
        raise ValidationError(
            f"El tipo de archivo '{mime_type}' no está permitido."
        )

    # Calcular SHA-256 hash del contenido binario
    sha256_hash = hashlib.sha256(content).hexdigest()

    # Construir ruta/clave en el storage
    safe_name = os.path.basename(original_name).replace(" ", "_")
    storage_path = f"{folder}/{sha256_hash[:10]}_{safe_name}"

    # Guardar mediante default_storage (S3/MinIO/FileSystem)
    from django.core.files.storage import default_storage
    saved_path = default_storage.save(storage_path, ContentFile(content))

    return {
        "storage_key": saved_path,
        "original_name": original_name,
        "mime_type": mime_type,
        "size_bytes": size_bytes,
        "sha256_hash": sha256_hash,
        "url": default_storage.url(saved_path) if hasattr(default_storage, "url") else saved_path
    }

def verify_file_integrity(storage_key: str, expected_hash: str) -> bool:
    """
    Lee el contenido desde el storage y verifica si su SHA-256 coincide con el hash almacenado.
    Soporta claves relativas de almacenamiento o URLs relativas de media (ej: '/media/evidencias/...').
    """
    from django.core.files.storage import default_storage
    clean_key = storage_key.lstrip('/')
    if clean_key.startswith('media/'):
        clean_key = clean_key[6:]

    target_key = clean_key if default_storage.exists(clean_key) else storage_key

    if not default_storage.exists(target_key):
        return False
    with default_storage.open(target_key, "rb") as f:
        content = f.read()
    current_hash = hashlib.sha256(content).hexdigest()
    return current_hash.lower() == expected_hash.lower()
