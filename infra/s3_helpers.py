"""S3 utilities for listing and downloading documents."""
import boto3
from infra.config import Config

def get_s3_client():
    return boto3.client("s3", region_name=Config.AWS_REGION)

def list_documents(prefix: str = "documents/") -> list[str]:
    """List all PDF keys under prefix."""
    client = get_s3_client()
    resp = client.list_objects_v2(Bucket=Config.S3_BUCKET, Prefix=prefix)
    return [obj["Key"] for obj in resp.get("Contents", []) if obj["Key"].endswith(".pdf")]

def download_document(key: str) -> bytes:
    """Download a single document as bytes."""
    client = get_s3_client()
    resp = client.get_object(Bucket=Config.S3_BUCKET, Key=key)
    return resp["Body"].read()
