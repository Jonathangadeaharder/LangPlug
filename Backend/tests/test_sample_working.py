"""
Sample working test to verify test infrastructure
"""
import pytest

@pytest.mark.timeout(30)
def test_Whenbasic_mathCalled_ThenSucceeds():
    """Basic test that should always pass"""
    assert 1 + 1 == 2

@pytest.mark.timeout(30)
def test_Whenstring_operationsCalled_ThenSucceeds():
    """Test string operations"""
    assert "hello".upper() == "HELLO"
    assert len("test") == 4

@pytest.mark.timeout(30)
@pytest.mark.unit
def test_Whenlist_operationsCalled_ThenSucceeds():
    """Test list operations"""
    test_list = [1, 2, 3]
    test_list.append(4)
    assert len(test_list) == 4
    assert test_list[-1] == 4
