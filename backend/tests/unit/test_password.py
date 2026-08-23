import pytest
from app.core.security import hash_password,verify_password
def test_password_hash_roundtrip():
    h=hash_password("StrongPass1!")
    assert h!="StrongPass1!"
    assert verify_password("StrongPass1!",h)
    assert not verify_password("WrongPass1!",h)
def test_weak_password_rejected():
    with pytest.raises(ValueError):hash_password("password")
