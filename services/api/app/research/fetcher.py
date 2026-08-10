import ipaddress, socket
from urllib.parse import urlparse

def validate_public_url(url:str)->str:
    p=urlparse(url)
    if p.scheme not in {"http","https"} or not p.hostname: raise ValueError("URL deve usar http/https e possuir host")
    host=p.hostname.lower()
    if host in {"localhost","localhost.localdomain"}: raise ValueError("Host local bloqueado")
    try: infos=socket.getaddrinfo(host,p.port or (443 if p.scheme=="https" else 80),type=socket.SOCK_STREAM)
    except socket.gaierror as e: raise ValueError("Host não resolvido") from e
    for info in infos:
        ip=ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified: raise ValueError("Destino de rede não público bloqueado")
    return url
