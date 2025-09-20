"""Minimal test to verify pytest works"""
import pytest


@pytest.mark.timeout(30)
def test_WhenminimalCalled_ThenSucceeds():
    assert True


@pytest.mark.timeout(30)
def test_WhenadditionCalled_ThenSucceeds():
    assert 1 + 1 == 2
