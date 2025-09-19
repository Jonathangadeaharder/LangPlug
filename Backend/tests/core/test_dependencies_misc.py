"""
Misc small tests for core.dependencies utilities.
"""
from __future__ import annotations

import pytest

from core.dependencies import get_task_progress_registry


@pytest.mark.timeout(30)
def test_Whenget_task_progress_registry_singletonCalled_ThenSucceeds():
    a = get_task_progress_registry()
    b = get_task_progress_registry()
    assert a is b
    key = "k"
    a[key] = 1
    assert b[key] == 1

