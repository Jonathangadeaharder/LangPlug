"""
Tests for Settings CORS origin parsing behavior.
"""
from __future__ import annotations

import os
import pytest

from core.config import Settings


@pytest.mark.timeout(30)
def test_Whencors_origins_parsing_csvCalled_ThenSucceeds():
    out = Settings.parse_cors_origins("http://a.com,http://b.com")
    assert out == ["http://a.com", "http://b.com"]


@pytest.mark.timeout(30)
def test_Whencors_origins_parsing_jsonCalled_ThenSucceeds():
    out = Settings.parse_cors_origins('["http://x", "http://y"]')
    assert out == ["http://x", "http://y"]
