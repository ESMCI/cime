"""
CIME Server implementations for data transfer.

Server availability is detected lazily on first access to avoid
running executables at import time.
"""

from functools import lru_cache
from shutil import which


@lru_cache(maxsize=None)
def is_protocol_available(protocol: str) -> bool:
    """
    Check if a protocol is available.

    Args:
        protocol: One of 'ftp', 'svn', 'wget', 'gftp'

    Returns:
        True if the protocol is available, False otherwise.
    """
    protocol = protocol.lower()
    if protocol == "ftp":
        try:
            from ftplib import FTP  # noqa: F401 pylint: disable=unused-import

            return True
        except ImportError:
            return False
    elif protocol == "svn":
        return which("svn") is not None
    elif protocol == "wget":
        return which("wget") is not None
    elif protocol == "gftp":
        return which("globus-url-copy") is not None
    return False


def __getattr__(name: str):
    """Lazy loading of server classes and has_* attributes."""
    if name == "FTP":
        if is_protocol_available("ftp"):
            from CIME.Servers.ftp import FTP

            return FTP
        raise AttributeError("FTP server not available")
    elif name == "SVN":
        if is_protocol_available("svn"):
            from CIME.Servers.svn import SVN

            return SVN
        raise AttributeError("SVN server not available (svn not found)")
    elif name == "WGET":
        if is_protocol_available("wget"):
            from CIME.Servers.wget import WGET

            return WGET
        raise AttributeError("WGET server not available (wget not found)")
    elif name == "GridFTP":
        if is_protocol_available("gftp"):
            from CIME.Servers.gftp import GridFTP

            return GridFTP
        raise AttributeError("GridFTP server not available (globus-url-copy not found)")
    elif name == "has_ftp":
        return is_protocol_available("ftp")
    elif name == "has_svn":
        return is_protocol_available("svn")
    elif name == "has_wget":
        return is_protocol_available("wget")
    elif name == "has_gftp":
        return is_protocol_available("gftp")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
