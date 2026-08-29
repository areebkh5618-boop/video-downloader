"""
Phase 14 foundations + basic security for Phases 1-8.
SSRF protection, URL validation, filename sanitization.
"""
from __future__ import annotations
import ipaddress
import re
from urllib.parse import urlparse
from typing import Optional

from app.core.exceptions import SecurityError


PRIVATE_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def validate_url(url: str) -> str:
    """Strict URL validation. Only http/https. Block private IPs & dangerous schemes."""
    if not url or not isinstance(url, str):
        raise SecurityError("URL is required")

    url = url.strip()
    if len(url) > 2048:
        raise SecurityError("URL too long")

    try:
        parsed = urlparse(url)
    except Exception:
        raise SecurityError("Malformed URL")

    if parsed.scheme not in ("http", "https"):
        raise SecurityError("Only http and https URLs are allowed")

    if not parsed.netloc:
        raise SecurityError("Invalid URL host")

    hostname = parsed.hostname
    if not hostname:
        raise SecurityError("Invalid hostname")

    # Block obvious localhost names
    blocked_hosts = {"localhost", "localhost.localdomain", "ip6-localhost", "ip6-loopback"}
    if hostname.lower() in blocked_hosts:
        raise SecurityError("Localhost URLs are not allowed")

    # Try to resolve / check IP
    try:
        # If hostname is already an IP
        ip = ipaddress.ip_address(hostname)
        for net in PRIVATE_NETWORKS:
            if ip in net:
                raise SecurityError("Private or internal IP addresses are not allowed")
    except ValueError:
        # It's a domain name – we still block some patterns
        if hostname.lower().endswith((".local", ".internal", ".localhost")):
            raise SecurityError("Internal domain names are not allowed")

    return url


def sanitize_filename(name: str, max_len: int = 120) -> str:
    """Remove dangerous characters and path traversal sequences."""
    if not name:
        return "download"
    # Remove path separators and control chars
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", name)
    name = name.replace("..", "")
    name = re.sub(r"\s+", " ", name).strip()
    name = name[:max_len] or "download"
    return name