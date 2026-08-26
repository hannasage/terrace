"""Tests for the API-key middleware that gates the hosted server."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from api_key_auth import ApiKeyMiddleware  # noqa: E402


class _FakeApp:
    """A downstream ASGI app that records whether it was reached."""

    def __init__(self) -> None:
        self.reached = False

    async def __call__(self, scope, receive, send) -> None:
        self.reached = True
        if scope["type"] == "http":
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"ok"})


def _run(headers: list[tuple[bytes, bytes]]) -> tuple[bool, int | None]:
    app = _FakeApp()
    middleware = ApiKeyMiddleware(app, "s3cret")
    scope = {"type": "http", "headers": headers}
    responses: list[dict] = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        responses.append(message)

    asyncio.run(middleware(scope, receive, send))
    status = next(
        (r["status"] for r in responses if r["type"] == "http.response.start"), None
    )
    return app.reached, status


def test_no_header_is_rejected():
    reached, status = _run([])
    assert not reached and status == 401


def test_bearer_is_accepted():
    reached, status = _run([(b"authorization", b"Bearer s3cret")])
    assert reached and status == 200


def test_x_api_key_is_accepted():
    reached, status = _run([(b"x-api-key", b"s3cret")])
    assert reached and status == 200


def test_wrong_key_is_rejected():
    reached, status = _run([(b"authorization", b"Bearer nope")])
    assert not reached and status == 401


def test_empty_key_is_refused_at_construction():
    with pytest.raises(ValueError):
        ApiKeyMiddleware(_FakeApp(), "")


def test_non_http_scope_passes_through():
    app = _FakeApp()
    middleware = ApiKeyMiddleware(app, "s3cret")

    async def noop():
        return {}

    asyncio.run(middleware({"type": "lifespan"}, noop, noop))
    assert app.reached  # lifespan reaches the app without an auth check
