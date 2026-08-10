import socket, pytest
from app.research import fetcher
@pytest.mark.parametrize("url",["http://localhost/a","http://127.0.0.1/a","ftp://example.com/a"])
def test_rejects_obviously_unsafe_urls(url):
    with pytest.raises(ValueError): fetcher.validate_public_url(url)
def test_rejects_private_dns(monkeypatch):
    monkeypatch.setattr(socket,"getaddrinfo",lambda *a,**k:[(socket.AF_INET,socket.SOCK_STREAM,6,"",("10.0.0.5",443))])
    with pytest.raises(ValueError): fetcher.validate_public_url("https://internal.example/a")
def test_accepts_public_dns(monkeypatch):
    monkeypatch.setattr(socket,"getaddrinfo",lambda *a,**k:[(socket.AF_INET,socket.SOCK_STREAM,6,"",("93.184.216.34",443))])
    assert fetcher.validate_public_url("https://example.com/a")=="https://example.com/a"
