"""Storage contracts for Release Trust evidence."""

from .object_store import ObjectStore, ObjectStoreError, ObjectNotFoundError, ObjectAlreadyExistsError
from .local_object_store import LocalObjectStore

_default_object_store: ObjectStore | None = None


def get_default_object_store() -> ObjectStore:
    """Application composition point; replace here/configuration for S3."""
    global _default_object_store
    if _default_object_store is None:
        _default_object_store = LocalObjectStore()
    return _default_object_store

__all__ = ["ObjectStore", "ObjectStoreError", "ObjectNotFoundError", "ObjectAlreadyExistsError", "get_default_object_store"]
