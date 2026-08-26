"""Tests for the static bearer-token verifier used by the hosted server."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from auth import StaticTokenVerifier  # noqa: E402


def _verify(secret: str, presented: str):
    return asyncio.run(StaticTokenVerifier(secret).verify_token(presented))


def test_correct_token_is_accepted():
    result = _verify("s3cret", "s3cret")
    assert result is not None
    assert result.scopes == ["terrace:read"]


def test_wrong_token_is_rejected():
    assert _verify("s3cret", "nope") is None


def test_empty_presented_token_is_rejected():
    assert _verify("s3cret", "") is None


def test_empty_secret_is_refused_at_construction():
    with pytest.raises(ValueError):
        StaticTokenVerifier("")
