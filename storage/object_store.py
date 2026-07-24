"""Provider-neutral evidence object storage interface."""
from abc import ABC, abstractmethod
from typing import Any


class ObjectStoreError(Exception):
    """Base error raised by evidence storage providers."""


class ObjectNotFoundError(ObjectStoreError):
    """Raised when an evidence reference cannot be read."""


class ObjectAlreadyExistsError(ObjectStoreError):
    """Raised when an immutable evidence object already exists."""


class ObjectStore(ABC):
    """Contract used by Release Trust for JSON evidence objects.

    References are opaque provider-owned strings.  An S3 implementation can
    keep the same contract and return S3 keys/URIs without service changes.
    """

    @abstractmethod
    def upload_json(self, release_id: str, object_name: str, payload: Any) -> str:
        """Persist a JSON payload and return its stable reference."""

    @abstractmethod
    def download_json(self, reference: str) -> Any:
        """Return the JSON payload addressed by *reference*."""

    @abstractmethod
    def exists(self, reference: str) -> bool:
        """Return whether *reference* exists."""

    @abstractmethod
    def delete(self, reference: str) -> None:
        """Delete an object; deleting a missing object is permitted."""

    @abstractmethod
    def build_reference(self, release_id: str, object_name: str) -> str:
        """Build a provider-specific stable reference without writing."""
