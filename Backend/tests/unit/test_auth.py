"""Legacy live-HTTP auth tests are superseded by API contract coverage.

We keep this module as a placeholder so that historical references do not fail
imports, but the tests are intentionally skipped to avoid hitting external
services during the standard suite.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.skip(
    reason="Live HTTP auth smoke checks replaced by structured API contract tests."
)
