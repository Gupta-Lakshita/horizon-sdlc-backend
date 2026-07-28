"""S3-compatible immutable JSON evidence provider (AWS S3 and MinIO)."""
import json
import os
from typing import Any

import boto3

from .object_store import ObjectAlreadyExistsError, ObjectNotFoundError, ObjectStore, ObjectStoreError


class S3ObjectStore(ObjectStore):
    def __init__(self, *, endpoint_url: str | None = None) -> None:
        self.bucket = os.getenv("OBJECT_STORE_BUCKET", "").strip()
        if not self.bucket:
            raise ObjectStoreError("OBJECT_STORE_BUCKET is required for S3-compatible storage")
        self.prefix = os.getenv("OBJECT_STORE_PREFIX", "release-trust").strip("/")
        self.client = boto3.client("s3", endpoint_url=endpoint_url or os.getenv("OBJECT_STORE_ENDPOINT_URL") or None)

    def build_reference(self, release_id: str, object_name: str) -> str:
        if not release_id or "/" in release_id or not object_name.replace("_", "").isalnum():
            raise ObjectStoreError("invalid evidence reference")
        return f"{self.prefix}/{release_id}/{object_name.removesuffix('.json')}.json"

    def upload_json(self, release_id: str, object_name: str, payload: Any) -> str:
        reference = self.build_reference(release_id, object_name)
        try:
            self.client.put_object(Bucket=self.bucket, Key=reference, Body=json.dumps(payload).encode("utf-8"),
                                   ContentType="application/json", IfNoneMatch="*")
            return reference
        except Exception as exc:
            error_code = getattr(exc, "response", {}).get("Error", {}).get("Code")
            if error_code in {"PreconditionFailed", "412"}:
                raise ObjectAlreadyExistsError("evidence object already exists") from exc
            raise ObjectStoreError("unable to store evidence") from exc

    def download_json(self, reference: str) -> Any:
        try:
            return json.loads(self.client.get_object(Bucket=self.bucket, Key=reference)["Body"].read())
        except Exception as exc:
            error_code = getattr(exc, "response", {}).get("Error", {}).get("Code")
            if error_code in {"NoSuchKey", "404", "NotFound"}:
                raise ObjectNotFoundError("evidence object not found") from exc
            raise ObjectStoreError("unable to read evidence") from exc

    def exists(self, reference: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=reference); return True
        except Exception:
            return False

    def delete(self, reference: str) -> None:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=reference)
        except Exception as exc:
            raise ObjectStoreError("unable to delete evidence") from exc
