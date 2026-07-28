"""Small dependency-free HTTP client shared by reference adapters."""
import json
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class RunnerApiError(RuntimeError):
    pass


@dataclass
class RunnerApiClient:
    base_url: str
    authorization: Optional[str] = None
    timeout_seconds: float = 15
    retries: int = 3
    backoff_seconds: float = 1

    def _url(self, path: str) -> str:
        return f"{self.base_url.rstrip('/')}/release-trust/runner/v1{path}"

    def request(self, method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Any:
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {"Accept": "application/json"}
        if body is not None: headers["Content-Type"] = "application/json"
        if self.authorization: headers["Authorization"] = self.authorization
        attempts = max(0, self.retries) + 1
        for attempt in range(attempts):
            try:
                request = Request(self._url(path), data=body, headers=headers, method=method)
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    return json.loads(response.read().decode("utf-8") or "{}")
            except HTTPError as exc:
                transient = exc.code in {408, 429, 500, 502, 503, 504}
                detail = exc.read().decode("utf-8", errors="replace")[:1000]
                if not transient or attempt == attempts - 1:
                    raise RunnerApiError(f"Runner API {method} {path} failed: HTTP {exc.code}: {detail}") from exc
            except (URLError, TimeoutError, OSError) as exc:
                if attempt == attempts - 1:
                    raise RunnerApiError(f"Runner API {method} {path} failed after {attempts} attempts: {exc}") from exc
            time.sleep(self.backoff_seconds * (2 ** attempt))
        raise AssertionError("unreachable")

    def create_release(self, payload): return self.request("POST", "/releases", payload)
    def upload_evidence(self, release_id, payload): return self.request("POST", f"/releases/{release_id}/evidence", payload)
    def publish_event(self, release_id, payload): return self.request("POST", f"/releases/{release_id}/events", payload)
    def update_status(self, release_id, payload): return self.request("PATCH", f"/releases/{release_id}/status", payload)
    def get_status(self, release_id): return self.request("GET", f"/releases/{release_id}/status")
