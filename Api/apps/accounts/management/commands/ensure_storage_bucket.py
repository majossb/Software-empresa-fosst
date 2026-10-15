"""
Comando de arranque: garantiza que el bucket de almacenamiento (S3/MinIO) exista.

MinIO/silo no crea buckets automáticamente, por lo que sin este paso cualquier
subida de archivos (evidencias, informes, logos) fallaría. Además, cuando la
generación de URLs no usa firmas (AWS_QUERYSTRING_AUTH=False), aplica una
política pública de lectura para que los archivos sean accesibles desde el navegador.

Uso:
  python manage.py ensure_storage_bucket
"""

import json

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crea el bucket S3/MinIO si no existe y aplica política pública de lectura cuando corresponde."

    def handle(self, *args, **options):
        storage_conf = settings.STORAGES.get("default", {})
        backend = str(storage_conf.get("BACKEND", "")).lower()
        opts = storage_conf.get("OPTIONS", {}) or {}

        if "s3" not in backend:
            self.stdout.write(
                f"[ensure_storage_bucket] Backend actual '{backend}' no es S3; se omite."
            )
            return

        import boto3
        from botocore.exceptions import ClientError

        bucket = opts.get("bucket_name") or "fosst-media"
        endpoint = opts.get("endpoint_url")
        region = opts.get("region_name", "us-east-1")
        querystring_auth = opts.get("querystring_auth", True)

        client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=opts.get("access_key"),
            aws_secret_access_key=opts.get("secret_key"),
            region_name=region,
        )

        try:
            client.head_bucket(Bucket=bucket)
            self.stdout.write(f"[ensure_storage_bucket] El bucket '{bucket}' ya existe.")
        except ClientError:
            client.create_bucket(Bucket=bucket)
            self.stdout.write(
                self.style.SUCCESS(f"[ensure_storage_bucket] Bucket '{bucket}' creado.")
            )

        if not querystring_auth:
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": ["*"]},
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{bucket}/*"],
                    }
                ],
            }
            try:
                client.put_bucket_policy(Bucket=bucket, Policy=json.dumps(policy))
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[ensure_storage_bucket] Política pública de lectura aplicada a '{bucket}'."
                    )
                )
            except ClientError as exc:
                self.stderr.write(
                    f"[ensure_storage_bucket] No se pudo aplicar la política pública: {exc}"
                )
