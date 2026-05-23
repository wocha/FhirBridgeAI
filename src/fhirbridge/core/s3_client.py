import logging
from pathlib import Path

import aioboto3
from botocore.exceptions import ClientError

from fhirbridge.core.config import get_settings

logger = logging.getLogger(__name__)


class AsyncS3Client:
    """
    Singleton-like async S3 client for claim-check storage.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            settings = get_settings()
            access_key, secret_key = settings.require_minio_credentials()
            cls._instance.endpoint_url = settings.minio_url
            cls._instance.access_key = access_key
            cls._instance.secret_key = secret_key
            cls._instance.session = aioboto3.Session()
        return cls._instance

    async def upload_file(self, file_path: Path, bucket_name: str, object_name: str | None = None) -> str:
        if not object_name:
            object_name = file_path.name

        try:
            async with self.session.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
            ) as s3:
                await s3.upload_file(str(file_path), bucket_name, object_name)

            payload_uri = f"{self.endpoint_url}/{bucket_name}/{object_name}"
            logger.info("Successfully uploaded %s to %s", object_name, bucket_name)
            return payload_uri

        except ClientError as exc:
            logger.error("S3 upload failed for %s: %s", object_name, exc)
            raise RuntimeError(f"S3 upload failed: {exc}") from exc
