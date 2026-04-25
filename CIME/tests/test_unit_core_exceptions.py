"""Unit tests for CIME.core.exceptions."""

import pytest

from CIME.core.exceptions import (
    BuildError,
    CIMEError,
    ConfigurationError,
    ExternalCommandError,
    InputError,
    LockingError,
    RetryableExternalCommandError,
    SubmitError,
    SystemTestError,
)


class TestCIMEError:
    """Tests for the base CIMEError exception."""

    def test_inherits_system_exit(self):
        assert issubclass(CIMEError, SystemExit)

    def test_inherits_exception(self):
        assert issubclass(CIMEError, Exception)

    def test_catchable_as_exception(self):
        with pytest.raises(Exception):
            raise CIMEError("test")

    def test_catchable_as_system_exit(self):
        with pytest.raises(SystemExit):
            raise CIMEError("test")

    def test_message_preserved(self):
        try:
            raise CIMEError("my message")
        except CIMEError as exc:
            assert str(exc) == "my message"


class TestSubclasses:
    """All typed exceptions inherit from CIMEError."""

    @pytest.mark.parametrize(
        "exc_class",
        [
            ConfigurationError,
            BuildError,
            SubmitError,
            SystemTestError,
            LockingError,
            ExternalCommandError,
            RetryableExternalCommandError,
            InputError,
        ],
    )
    def test_is_cime_error(self, exc_class):
        assert issubclass(exc_class, CIMEError)

    @pytest.mark.parametrize(
        "exc_class",
        [
            ConfigurationError,
            BuildError,
            SubmitError,
            SystemTestError,
            LockingError,
            InputError,
        ],
    )
    def test_simple_subclass_message(self, exc_class):
        with pytest.raises(exc_class, match="oops"):
            raise exc_class("oops")


class TestExternalCommandError:
    """Tests for ExternalCommandError and its retryable variant."""

    def test_stores_returncode_and_command(self):
        exc = ExternalCommandError("failed", returncode=42, command="make")
        assert exc.returncode == 42
        assert exc.command == "make"
        assert str(exc) == "failed"

    def test_defaults(self):
        exc = ExternalCommandError("failed")
        assert exc.returncode == 1
        assert exc.command == ""

    def test_retryable_is_external_command_error(self):
        assert issubclass(RetryableExternalCommandError, ExternalCommandError)

    def test_retryable_stores_fields(self):
        exc = RetryableExternalCommandError("timeout", returncode=124, command="srun")
        assert exc.returncode == 124
        assert exc.command == "srun"
