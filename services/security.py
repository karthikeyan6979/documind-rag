import ipaddress
import socket
from urllib.parse import urlparse
from fastapi import HTTPException

PRIVATE_NETS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
]


def is_private(hostname):
    try:
        ip = ipaddress.ip_address(hostname)
    except ValueError:
        ip = ipaddress.ip_address(socket.gethostbyname(hostname))
    return any(ip in net for net in PRIVATE_NETS)


def validate_url(url):
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(400, "Only http/https URLs allowed")
    if not parsed.hostname or is_private(parsed.hostname):
        raise HTTPException(400, "The given ip is not allowed")
