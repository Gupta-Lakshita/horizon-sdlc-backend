"""Storage contracts for Release Trust evidence."""

from .object_store import ObjectStore, ObjectStoreError, ObjectNotFoundError, ObjectAlreadyExistsError
from .local_object_store import LocalObjectStore
import os

_active_object_store: ObjectStore | None = None


def create_object_store(provider: str | None = None) -> ObjectStore:
    """Central provider factory; services only ever receive ObjectStore.

    New providers register a constructor here, without any Release Trust
    service/router changes.
    """
    selected = (provider or os.getenv("OBJECT_STORE_PROVIDER", "local")).strip().lower()
    providers = {"local": LocalObjectStore}
    try:
        return providers[selected]()
    except KeyError as exc:
        raise RuntimeError(f"unsupported ObjectStore provider: {selected}") from exc


def initialize_object_store(provider: str | None = None) -> ObjectStore:
    """Application-startup composition point; called exactly once by main."""
    global _active_object_store
    if _active_object_store is None:
        _active_object_store = create_object_store(provider)
    return _active_object_store


def get_default_object_store() -> ObjectStore:
    """Deprecated compatibility accessor; startup must initialize storage."""
    if _active_object_store is None:
        raise RuntimeError("ObjectStore has not been initialized")
    return _active_object_store

__all__ = ["ObjectStore", "ObjectStoreError", "ObjectNotFoundError", "ObjectAlreadyExistsError", "create_object_store", "initialize_object_store", "get_default_object_store"]
