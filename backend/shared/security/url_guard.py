"""
shared/security/url_guard.py

SSRF protection for every outbound fetch of a user-supplied URL.

Crawled content ends up in the tenant's File Search store and can be read
back through chat, so fetching an internal address (Redis, the API container,
the cloud metadata endpoint at 169.254.169.254, …) would leak it. Every URL —
including each redirect hop — must resolve exclusively to public addresses.
"""
import ipaddress
import socket
from urllib.parse import urlparse

import httpx

ALLOWED_SCHEMES = {"http", "https"}


class UnsafeURLError(ValueError):
    """Raised when a URL is not allowed to be fetched."""


def _is_public_ip(ip: str) -> bool:
    addr = ipaddress.ip_address(ip)
    # Unwrap IPv4-mapped IPv6 (::ffff:10.0.0.1) so it can't sneak past is_global.
    if isinstance(addr, ipaddress.IPv6Address) and addr.ipv4_mapped:
        addr = addr.ipv4_mapped
    return addr.is_global and not addr.is_multicast


def assert_public_url(url: str) -> None:
    """Raises UnsafeURLError unless url is http(s) and every resolved address is public."""
    parsed = urlparse(url)
    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise UnsafeURLError(f"Scheme not allowed: {parsed.scheme or '(none)'}")
    host = parsed.hostname
    if not host:
        raise UnsafeURLError("URL has no host")

    try:
        port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
    except ValueError as e:
        raise UnsafeURLError(f"Invalid port: {e}") from e

    try:
        infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror as e:
        raise UnsafeURLError(f"Could not resolve host {host}: {e}") from e

    for info in infos:
        ip = info[4][0]
        if not _is_public_ip(ip):
            raise UnsafeURLError(f"Host {host} resolves to non-public address {ip}")


def is_public_url(url: str) -> bool:
    try:
        assert_public_url(url)
        return True
    except UnsafeURLError:
        return False


def _check_request(request: httpx.Request) -> None:
    # httpx fires request hooks for the initial request and every redirect hop.
    assert_public_url(str(request.url))


def safe_client(**kwargs) -> httpx.Client:
    """httpx.Client that refuses to connect to non-public hosts, including via redirects."""
    hooks = kwargs.pop("event_hooks", {}) or {}
    hooks.setdefault("request", []).insert(0, _check_request)
    return httpx.Client(event_hooks=hooks, **kwargs)
