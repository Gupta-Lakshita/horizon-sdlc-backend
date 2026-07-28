"""Optional Azure Blob JSON evidence provider; dependency is loaded only when selected."""
import json
import os
from typing import Any

from .object_store import ObjectAlreadyExistsError, ObjectNotFoundError, ObjectStore, ObjectStoreError


class AzureBlobObjectStore(ObjectStore):
    def __init__(self) -> None:
        try:
            from azure.storage.blob import BlobServiceClient
        except ImportError as exc:
            raise ObjectStoreError("azure-storage-blob is required for azure ObjectStore") from exc
        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
        self.container = os.getenv("AZURE_STORAGE_CONTAINER", "").strip()
        if not connection_string or not self.container:
            raise ObjectStoreError("AZURE_STORAGE_CONNECTION_STRING and AZURE_STORAGE_CONTAINER are required")
        self.container_client = BlobServiceClient.from_connection_string(connection_string).get_container_client(self.container)

    def build_reference(self, release_id: str, object_name: str) -> str:
        if not release_id or "/" in release_id:
            raise ObjectStoreError("invalid evidence reference")
        return f"release-trust/{release_id}/{object_name.removesuffix('.json')}.json"

    def upload_json(self, release_id: str, object_name: str, payload: Any) -> str:
        reference = self.build_reference(release_id, object_name)
        try:
            self.container_client.upload_blob(reference, json.dumps(payload).encode("utf-8"), overwrite=False)
            return reference
        except Exception as exc:
            if "BlobAlreadyExists" in type(exc).__name__:
                raise ObjectAlreadyExistsError("evidence object already exists") from exc
            raise ObjectStoreError("unable to store evidence") from exc

    def download_json(self, reference: str) -> Any:
        try:
            return json.loads(self.container_client.download_blob(reference).readall())
        except Exception as exc:
            if "ResourceNotFound" in type(exc).__name__:
                raise ObjectNotFoundError("evidence object not found") from exc
            raise ObjectStoreError("unable to read evidence") from exc

    def exists(self, reference: str) -> bool:
        try: return self.container_client.get_blob_client(reference).exists()
        except Exception: return False

    def delete(self, reference: str) -> None:
        try: self.container_client.delete_blob(reference)
        except Exception as exc: raise ObjectStoreError("unable to delete evidence") from exc
