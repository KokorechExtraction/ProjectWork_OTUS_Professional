from app.core.security import create_access_token, decode_access_token


def test_create_and_decode_access_token() -> None:
    token = create_access_token("123")
    payload = decode_access_token(token)

    assert payload["sub"] == "123"
    assert "exp" in payload
