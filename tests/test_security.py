from types import SimpleNamespace

import pytest

from app.core.security import create_access_token, decode_access_token
from app.schemas.auth import RegisterRequest


def test_create_and_decode_access_token() -> None:
    token_data = create_access_token(
        user=SimpleNamespace(id=123, username="tester", is_admin=False)
    )
    payload = decode_access_token(token_data["access_token"])

    assert payload["sub"] == "123"
    assert payload["username"] == "tester"
    assert payload["is_admin"] is False
    assert "exp" in payload


def test_register_request_rejects_passwords_over_bcrypt_limit() -> None:
    with pytest.raises(ValueError, match="72"):
        RegisterRequest(
            username="tester",
            email="tester@example.com",
            password="й" * 40,
        )
