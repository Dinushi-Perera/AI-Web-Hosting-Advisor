import ipaddress, socket, time
from urllib.parse import urlsplit, urljoin
import httpx
from app.core.config import settings
from app.core.exceptions import AppError

BLOCKED_HOSTS={"localhost","metadata.google.internal","metadata","instance-data","169.254.169.254"}

def _host_ips(host:str)->set[str]:
    try: return {r[4][0] for r in socket.getaddrinfo(host,None,type=socket.SOCK_STREAM)}
    except socket.gaierror as exc: raise AppError("URL_UNREACHABLE","The host could not be resolved.",400) from exc

def _safe_ip(ip_text:str)->bool:
    try:
        ip=ipaddress.ip_address(ip_text)
        return not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified)
    except ValueError: return False

def validate_public_url(url:str)->str:
    if not url or len(url)>2048: raise AppError("URL_INVALID","Enter a valid public HTTP/HTTPS URL.",422)
    try: p=urlsplit(url)
    except Exception as exc: raise AppError("URL_INVALID","Enter a valid public HTTP/HTTPS URL.",422) from exc
    if p.scheme.lower() not in {"http","https"} or not p.hostname: raise AppError("URL_INVALID","Only public HTTP/HTTPS URLs are allowed.",422)
    host=p.hostname.lower().rstrip(".")
    if host in BLOCKED_HOSTS or host.endswith(".local") or host.endswith(".internal"): raise AppError("URL_BLOCKED","Private, local and metadata endpoints are blocked.",400)
    if p.username or p.password: raise AppError("URL_BLOCKED","URLs containing credentials are blocked.",400)
    # A normal DNS hostname is not an IP literal. Only apply literal-IP rules
    # when ipaddress can actually parse the host; DNS answers are validated
    # independently below to prevent private-address and rebinding targets.
    try: literal_ip=ipaddress.ip_address(host)
    except ValueError: literal_ip=None
    if literal_ip is not None and not _safe_ip(str(literal_ip)):
        raise AppError("URL_BLOCKED","Private or unsafe IP addresses are blocked.",400)
    ips=_host_ips(host)
    if not ips or any(not _safe_ip(ip) for ip in ips): raise AppError("URL_BLOCKED","The hostname resolves to a private or unsafe address.",400)
    port=p.port
    if port and port not in {80,443}: raise AppError("URL_BLOCKED","Only standard HTTP/HTTPS ports are allowed.",400)
    return p.geturl()

def safe_fetch(url:str, max_bytes:int|None=None):
    current=validate_public_url(url); max_bytes=max_bytes or settings.max_external_response_bytes
    timeout=httpx.Timeout(settings.http_read_timeout,connect=settings.http_connect_timeout)
    start=time.perf_counter()
    with httpx.Client(timeout=timeout,follow_redirects=False,headers={"User-Agent":"AIHostingAdvisor/1.0"}) as client:
        for _ in range(settings.max_redirects+1):
            validate_public_url(current)
            with client.stream("GET",current) as resp:
                if resp.status_code in {301,302,303,307,308}:
                    loc=resp.headers.get("location")
                    if not loc: break
                    current=urljoin(current,loc); continue
                content=bytearray()
                for chunk in resp.iter_bytes():
                    content.extend(chunk)
                    if len(content)>max_bytes: raise AppError("URL_RESPONSE_TOO_LARGE","Website response exceeded the safe analysis limit.",400)
                return {"url":current,"status_code":resp.status_code,"headers":dict(resp.headers),"content":bytes(content),"response_time_ms":round((time.perf_counter()-start)*1000)}
    raise AppError("URL_TOO_MANY_REDIRECTS","Too many redirects.",400)
