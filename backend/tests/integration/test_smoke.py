import pytest
pytestmark=pytest.mark.skip(reason="Run against dedicated MySQL/Redis test infrastructure in CI; not a fake in-memory integration result.")
def test_placeholder():pass
