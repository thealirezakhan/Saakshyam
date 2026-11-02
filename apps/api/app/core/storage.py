"""S3-compatible object storage (systemdesign 4: object storage).

Uses the `minio` Python SDK against any S3-compatible endpoint
(adobe/s3mock in dev, MinIO/AWS S3 in prod). Falls back to the local
filesystem when no S3_ENDPOINT is configured (unit tests / bare dev).
"""

import hashlib
import os

from .config import settings

ALLOWED_MIME = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg",
}

_MAGIC = [
    (b"%PDF", "application/pdf"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
]


def sniff_mime(data: bytes) -> str | None:
    for magic, mime in _MAGIC:
        if data.startswith(magic):
            return mime
    return None


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Storage:
    def __init__(self):
        self._client = None

    def _s3(self):
        if self._client is None:
            from minio import Minio
            self._client = Minio(
                settings.S3_ENDPOINT.removeprefix("http://").removeprefix("https://"),
                access_key=settings.S3_ACCESS_KEY,
                secret_key=settings.S3_SECRET_KEY,
                secure=settings.S3_SECURE,
            )
        return self._client

    def ensure_bucket(self) -> None:
        if not settings.s3_enabled:
            os.makedirs(settings.S3_BUCKET, exist_ok=True)
            return
        client = self._s3()
        if not client.bucket_exists(settings.S3_BUCKET):
            client.make_bucket(settings.S3_BUCKET)

    def put(self, key: str, data: bytes) -> str:
        checksum = sha256(data)
        path = f"{checksum[:2]}/{checksum}.bin"
        if settings.s3_enabled:
            import io
            client = self._s3()
            if not self._exists(path):
                client.put_object(settings.S3_BUCKET, path, io.BytesIO(data), len(data))
        else:
            full = os.path.join(settings.S3_BUCKET, path)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            if not os.path.exists(full):
                with open(full, "wb") as f:
                    f.write(data)
        return path

    def get(self, storage_path: str) -> bytes:
        if settings.s3_enabled:
            client = self._s3()
            resp = client.get_object(settings.S3_BUCKET, storage_path)
            try:
                return resp.read()
            finally:
                resp.close()
                resp.release_conn()
        with open(os.path.join(settings.S3_BUCKET, storage_path), "rb") as f:
            return f.read()

    def _exists(self, path: str) -> bool:
        if settings.s3_enabled:
            try:
                self._s3().stat_object(settings.S3_BUCKET, path)
                return True
            except Exception:  # noqa: BLE001
                return False
        return os.path.exists(os.path.join(settings.S3_BUCKET, path))


storage = Storage()
