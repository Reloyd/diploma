from minio import Minio
from minio.error import S3Error
from app.config import settings
import io

client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_SECURE,
)


def ensure_buckets():
    for bucket in [settings.MINIO_BUCKET_AUDIO, settings.MINIO_BUCKET_COVERS]:
        try:
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)
        except S3Error as e:
            print(f"MinIO bucket error: {e}")


def get_presigned_url(bucket: str, object_name: str, expires_hours: int = 24) -> str:
    from datetime import timedelta
    try:
        url = client.presigned_get_object(bucket, object_name, expires=timedelta(hours=expires_hours))
        return url
    except S3Error:
        return ""


def upload_file(bucket: str, object_name: str, data: bytes, content_type: str = "audio/mpeg") -> bool:
    try:
        client.put_object(
            bucket,
            object_name,
            io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        return True
    except S3Error as e:
        print(f"MinIO upload error: {e}")
        return False
