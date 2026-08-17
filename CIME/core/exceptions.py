"""
Typed exception hierarchy for CIME.

CIMEError inherits from both SystemExit and Exception so that:
- Tracebacks are suppressed in normal usage (SystemExit behavior)
- Exceptions are still catchable (Exception behavior)
- Users can run with --debug to see full tracebacks

All CIME-specific exceptions should inherit from CIMEError.
"""


class CIMEError(SystemExit, Exception):
    """Base exception for all CIME errors.

    Inherits from SystemExit to suppress tracebacks in normal usage,
    and from Exception to remain catchable.
    """


class ConfigurationError(CIMEError):
    """Invalid or missing configuration (XML files, env vars, etc.)."""


class BuildError(CIMEError):
    """Failure during model build."""


class SubmitError(CIMEError):
    """Failure during job submission."""


class SystemTestError(CIMEError):
    """Failure in a CIME system test."""


class LockingError(CIMEError):
    """Case locking or unlocking failure."""


class ExternalCommandError(CIMEError):
    """An external command (subprocess) failed.

    Modeled after subprocess.CalledProcessError for consistency.

    Attributes:
        returncode: Exit code of the command.
        cmd: The command that was run (string or list).
        output: Standard output captured from the command, if any.
        stderr: Standard error captured from the command, if any.
    """

    def __init__(
        self,
        message: str,
        returncode: int = 1,
        cmd: str = "",
        output: str = "",
        stderr: str = "",
        # Deprecated: use cmd instead
        command: str = "",
    ):
        super().__init__(message)
        self.returncode = returncode
        # Support both 'cmd' (preferred) and 'command' (deprecated) for compatibility
        self.cmd = cmd or command
        self.output = output
        self.stderr = stderr

    @property
    def command(self) -> str:
        """Deprecated: Use cmd instead."""
        return self.cmd


class RetryableExternalCommandError(ExternalCommandError):
    """An external command failed but may succeed on retry (transient error)."""


class InputError(CIMEError):
    """Invalid user input (bad arguments, missing required values)."""
