import pytest

from app.main import healthcheck


@pytest.mark.asyncio
async def test_healthcheck() -> None:
    assert await healthcheck() == {"status": "ok"}
