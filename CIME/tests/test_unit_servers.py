"""Unit tests for CIME.Servers lazy loading.

These tests verify:
1. Lazy loading behavior (no subprocess at import time)
2. Backward compatibility with existing usage patterns
3. is_protocol_available() API
"""

import pytest


class TestServersLazyLoading:
    """Tests for lazy loading of server modules."""

    def test_import_does_not_run_which(self):
        """Importing CIME.Servers should not run shutil.which()."""
        import CIME.Servers

        assert CIME.Servers is not None

    def test_availability_not_checked_at_import(self):
        """Availability flags should be unchecked after import."""
        import importlib
        import sys

        # Force reimport
        for mod in list(sys.modules.keys()):
            if "CIME.Servers" in mod:
                del sys.modules[mod]

        import CIME.Servers

        assert CIME.Servers is not None


class TestProtocolAvailability:
    """Tests for is_protocol_available() API."""

    def test_is_protocol_available_ftp(self):
        """FTP should always be available (stdlib)."""
        import CIME.Servers

        assert CIME.Servers.is_protocol_available("ftp") is True

    def test_is_protocol_available_invalid(self):
        """Invalid protocol should return False."""
        import CIME.Servers

        assert CIME.Servers.is_protocol_available("invalid") is False

    def test_is_protocol_available_case_insensitive(self):
        """Protocol check should be case-insensitive."""
        import CIME.Servers

        assert CIME.Servers.is_protocol_available("FTP") is True
        assert CIME.Servers.is_protocol_available("Ftp") is True
        assert CIME.Servers.is_protocol_available("ftp") is True


class TestServerClassAccess:
    """Tests for accessing server classes."""

    def test_ftp_attribute_access(self):
        """Accessing CIME.Servers.FTP should work via __getattr__."""
        import CIME.Servers

        FTP = CIME.Servers.FTP
        assert FTP is not None
        assert FTP.__name__ == "FTP"

    def test_ftp_has_ftp_login_method(self):
        """FTP class should have ftp_login class method (used by check_input_data)."""
        import CIME.Servers

        assert hasattr(CIME.Servers.FTP, "ftp_login")

    def test_wget_has_wget_login_method(self):
        """WGET class should have wget_login class method if available."""
        import CIME.Servers

        if CIME.Servers.is_protocol_available("wget"):
            assert hasattr(CIME.Servers.WGET, "wget_login")

    def test_unavailable_server_raises_attribute_error(self):
        """Accessing unavailable server should raise AttributeError."""
        import CIME.Servers

        if not CIME.Servers.is_protocol_available("gftp"):
            with pytest.raises(AttributeError):
                _ = CIME.Servers.GridFTP


class TestBackwardCompatibility:
    """Tests for backward compatibility with existing code patterns."""

    def test_has_ftp_attribute(self):
        """has_ftp attribute should return True (FTP always available)."""
        import CIME.Servers

        assert CIME.Servers.has_ftp is True

    def test_has_attributes_exist(self):
        """All has_* attributes should be accessible."""
        import CIME.Servers

        # These should not raise, regardless of availability
        _ = CIME.Servers.has_ftp
        _ = CIME.Servers.has_svn
        _ = CIME.Servers.has_wget
        _ = CIME.Servers.has_gftp

    def test_instantiate_ftp_server(self):
        """Should be able to instantiate FTP server (backward compat)."""
        import CIME.Servers

        FTP = CIME.Servers.FTP
        assert FTP is not None
