"""
SSRF guard — block audit/crawl targets that resolve to private,
loopback, link-local or cloud-metadata addresses.

The audit engine fetches arbitrary user-supplied URLs (by design — it is a
public website auditor). This guard prevents it from being abused as a proxy
into the internal network or the cloud metadata service (169.254.169.254).

Resolution happens at request time (defends against DNS-rebinding: a hostname
that resolves to a private/metadata IP is rejected regardless of how it is
spelled).
"""

import ipaddress
import socket
from urllib.parse import urlparse


# Cloud metadata endpoints (covered by link-local 169.254.0.0/16 too, but
# kept explicit for clarity / IPv6 metadata).
_BLOCKED_HOSTNAMES = {"localhost"}


def _ip_is_blocked(ip: ipaddress._BaseAddress) -> bool:
    """True if the resolved IP falls into a range we must never crawl."""
    return (
        ip.is_private          # 10/8, 172.16/12, 192.168/16, fc00::/7, ...
        or ip.is_loopback      # 127/8, ::1
        or ip.is_link_local    # 169.254/16 (incl. 169.254.169.254), fe80::/10
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified   # 0.0.0.0, ::
    )


def is_public_url(url: str) -> bool:
    """
    Return True only if every IP the URL's host resolves to is a public,
    routable address. Returns False for private/loopback/link-local/metadata
    targets, unresolvable hosts, or malformed URLs.
    """
    try:
        parsed = urlparse(url)
    except Exception:
        return False

    if parsed.scheme.lower() not in ("http", "https"):
        return False

    host = parsed.hostname
    if not host:
        return False

    host_l = host.lower()
    if host_l in _BLOCKED_HOSTNAMES:
        return False

    # If the host is already a literal IP, validate it directly.
    try:
        literal_ip = ipaddress.ip_address(host_l)
        return not _ip_is_blocked(literal_ip)
    except ValueError:
        pass  # Not a literal IP — resolve via DNS below.

    # Resolve the hostname; reject if it cannot be resolved or if ANY
    # resolved address is non-public (DNS-rebinding defence).
    try:
        infos = socket.getaddrinfo(host_l, None)
    except (socket.gaierror, UnicodeError, OSError):
        return False

    if not infos:
        return False

    for info in infos:
        sockaddr = info[4]
        ip_str = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            return False
        if _ip_is_blocked(ip):
            return False

    return True


async def _validate_redirect_response(response):
    """
    httpx response event hook: when following redirects, re-validate the
    redirect target so a public URL cannot 302 into a private/metadata
    address. Raises ValueError (caught by the auditor's try/except) on a
    blocked redirect target.
    """
    if response.is_redirect:
        location = response.headers.get("location")
        if location:
            target = str(response.url.join(location))
            if not is_public_url(target):
                raise ValueError(
                    f"Blocked redirect to non-public target: {target}"
                )


# Convenience: pass as `event_hooks=SSRF_EVENT_HOOKS` to httpx.AsyncClient
# alongside follow_redirects=True to make redirect-following SSRF-safe.
SSRF_EVENT_HOOKS = {"response": [_validate_redirect_response]}
