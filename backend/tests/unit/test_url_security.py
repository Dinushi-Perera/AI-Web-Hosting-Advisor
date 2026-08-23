import pytest
from app.services.url_security_service import validate_public_url
from app.core.exceptions import AppError
@pytest.mark.parametrize("url",["http://127.0.0.1","http://10.0.0.1","http://192.168.1.1","http://169.254.169.254","file:///etc/passwd","ftp://example.com"])
def test_blocks_unsafe_urls(url):
    with pytest.raises(AppError):validate_public_url(url)
