"""Regression coverage for the Docker Compose local-auth bypass."""

import pytest
from fastapi import HTTPException

import main


def test_local_auth_bypasses_a_stale_frontend_bearer_token(monkeypatch):
    """The proxy forwards Authorization, so local auth must ignore it."""
    monkeypatch.setattr(main, "LOCAL_DEV_AUTH_ENABLED", True)

    principal = main.get_current_principal("Bearer stale-token-from-an-old-session")

    assert principal.username == "local-dev"
    assert main.ROLE_PLATFORM_ADMIN in principal.roles


def test_invalid_bearer_token_is_still_rejected_when_local_auth_is_disabled(monkeypatch):
    monkeypatch.setattr(main, "LOCAL_DEV_AUTH_ENABLED", False)

    with pytest.raises(HTTPException) as exc_info:
        main.get_current_principal("Bearer invalid-token")

    assert exc_info.value.status_code == 401
