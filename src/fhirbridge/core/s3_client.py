import os
from pathlib import Path
import logging
import aioboto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class AsyncS3Client:
    """
    Singleton-ähnlicher asynchroner S3 Client für das Claim-Check Pattern.
    Nutzt aioboto3 für echte, nicht-blockierende asynchrone Uploads/Downloads.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AsyncS3Client, cls).__new__(cls)
            # Init config on first creation
            cls._instance.endpoint_url = os.getenv("MINIO_URL", "http://localhost:9000")
            cls._instance.access_key = os.getenv("MINIO_ROOT_USER", "admin")
            cls._instance.secret_key = os.getenv("MINIO_ROOT_PASSWORD", "admin123")
            # aioboto3 erfordert zwingend eine Session für asynchrone Vorgänge
            cls._instance.session = aioboto3.Session()
        return cls._instance

    async def upload_file(self, file_path: Path, bucket_name: str, object_name: str = None) -> str:
        """
        Lädt eine Datei asynchron in den S3/MinIO Speicher hoch.
        Blockiert NICHT den Event-Loop.
        
        Gibt die Pseudo-URI (Claim-Check) des Dokuments zurück.
        """
        if not object_name:
            object_name = file_path.name
            
        try:
            # Das async with Pattern ist bei aioboto3 ZWINGEND erforderlich
            async with self.session.client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key
            ) as s3:
                
                await s3.upload_file(str(file_path), bucket_name, object_name)
                
            # Rückgabe ist der Payload-Zeiger für RabbitMQ (Claim-Check Pattern)
            payload_uri = f"{self.endpoint_url}/{bucket_name}/{object_name}"
            logger.info(f"Successfully uploaded {object_name} to {bucket_name}")
            return payload_uri
            
        except ClientError as e:
            logger.error(f"S3 ClientError beim Upload von {object_name}: {str(e)}")
            raise Exception(f"S3 Upload failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unerwarteter Fehler beim S3 Upload von {object_name}: {str(e)}")
            raise
