"""
Centralized sys.path management for CIME.

CIME is not pip-installed; it relies on sys.path manipulation so that
scripts executed via symlinks (e.g. case.setup, xmlchange) can find
the CIME package. This module consolidates the various sys.path.insert
patterns scattered across the codebase into one place.

**This module is standalone for Slice 1** — existing call-sites are NOT
modified yet. Migration will happen incrementally in later slices.

Public API summary:

``bootstrap_cime_script()``
    Full-fidelity drop-in replacement for
    ``from standard_script_setup import *``.  Performs the dual Python
    version check, ``sys.path`` / ``CIMEROOT`` setup, and enables
    unbuffered stdout/stderr.  Use this in entry-point scripts when
    migrating away from ``standard_script_setup``.

``bootstrap_cime()``
    Granular primitive: resolves CIMEROOT, prepends it (and CIME/Tools)
    to ``sys.path``, and optionally sets ``os.environ["CIMEROOT"]``.
    Intentionally omits the version check and I/O buffering so callers
    that only need path setup are not forced to accept those side effects.

``check_minimum_python_version()``
    Standalone version guard; call explicitly when partial behaviour is
    needed (e.g. inside test harnesses that manage buffering themselves).

Typical usage (future, after wiring)::

    from CIME.core.config.bootstrap import bootstrap_cime_script
    bootstrap_cime_script()   # full legacy-equivalent entry-point setup

    # or, for scripts that only need path setup:
    from CIME.core.config.bootstrap import bootstrap_cime
    bootstrap_cime()
"""

import os
import sys
import warnings
from typing import List, Optional, Sequence


def find_cimeroot(starting_dir: Optional[str] = None) -> str:
    """Locate the CIME root directory.

    Resolution order:
    1. ``starting_dir`` argument (if provided)
    2. ``CIMEROOT`` environment variable
    3. Walk upward from this file to find the directory containing ``CIME/``

    Returns:
        Absolute path to the CIME root directory.

    Raises:
        RuntimeError: If CIMEROOT cannot be determined.
    """
    if starting_dir is not None:
        resolved = os.path.abspath(starting_dir)
        if _is_cimeroot(resolved):
            return resolved
        raise RuntimeError(f"Specified directory is not a valid CIMEROOT: {resolved}")

    env_root = os.environ.get("CIMEROOT")
    if env_root and _is_cimeroot(env_root):
        return os.path.abspath(env_root)

    # Walk up from this file: CIME/core/config/bootstrap.py -> CIME/core/config -> CIME/core -> CIME -> root
    candidate = os.path.abspath(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", "..")
    )
    if _is_cimeroot(candidate):
        return candidate

    raise RuntimeError(
        "Cannot determine CIMEROOT. Set the CIMEROOT environment variable "
        "or pass cimeroot explicitly."
    )


def _is_cimeroot(path: str) -> bool:
    """Check whether a directory looks like a valid CIMEROOT."""
    return os.path.isdir(os.path.join(path, "CIME"))


def bootstrap_cime(
    cimeroot: Optional[str] = None,
    extra_paths: Optional[Sequence[str]] = None,
    set_env: bool = True,
) -> str:
    """Set up sys.path for CIME and return the resolved CIMEROOT.

    This is the single function that should be called to prepare the
    Python environment for CIME imports. It:

    1. Resolves CIMEROOT
    2. Inserts CIMEROOT at the front of sys.path (if not already present)
    3. Inserts CIME/Tools at position 1 (if not already present)
    4. Inserts any extra_paths
    5. Optionally sets the CIMEROOT environment variable

    Args:
        cimeroot: Explicit CIMEROOT path. If None, auto-detected.
        extra_paths: Additional paths to insert after CIMEROOT and Tools.
        set_env: Whether to set ``os.environ["CIMEROOT"]``.

    Returns:
        The resolved CIMEROOT path.
    """
    root = find_cimeroot(cimeroot)
    tools_path = get_tools_path(root)

    paths_to_add: List[str] = [root, tools_path]
    if extra_paths:
        paths_to_add.extend(str(p) for p in extra_paths)

    _prepend_sys_path(paths_to_add)

    if set_env:
        os.environ["CIMEROOT"] = root

    return root


def _prepend_sys_path(paths: Sequence[str]) -> None:
    """Prepend paths to the front of ``sys.path``, order-preserving and deduped.

    Each path is converted to an absolute path and placed at the front of
    ``sys.path`` such that ``paths[0]`` ends up at index 0, ``paths[1]`` at
    index 1, and so on. If a path is already present it is removed first, so
    the entry is repositioned to the front rather than duplicated.

    Duplicate entries within ``paths`` itself are collapsed to the first
    occurrence before any insertion, so positions are stable regardless of
    how many times a path appears in the input. A ``UserWarning`` is issued
    when duplicates are detected, since they may indicate a caller bug that
    would silently affect import precedence.

    Args:
        paths: Paths to place at the front of ``sys.path``, highest priority
            first.

    Warns:
        UserWarning: If ``paths`` contains duplicate entries.

    Example:
        Given ``sys.path = [A, B, C]`` and ``paths = [C, D, C]``, the
        duplicate ``C`` is collapsed to its first occurrence, giving an
        effective prepend list of ``[C, D]``.  The result is::

            sys.path == [C, D, A, B]
    """
    # Deduplicate while preserving first-occurrence order.
    abs_paths = [os.path.abspath(p) for p in paths]
    unique = list(dict.fromkeys(abs_paths))
    duplicates = [p for p in unique if abs_paths.count(p) > 1]
    if duplicates:
        warnings.warn(
            f"Duplicate paths passed to _prepend_sys_path: {duplicates}. "
            "First occurrence takes precedence; this may affect import order.",
            UserWarning,
            stacklevel=2,
        )
    for i, absp in enumerate(unique):
        # Remove any existing entry so the path is repositioned, not duplicated.
        if absp in sys.path:
            sys.path.remove(absp)
        sys.path.insert(i, absp)


def get_tools_path(cimeroot: Optional[str] = None) -> str:
    """Return the CIME/Tools directory path."""
    root = cimeroot or find_cimeroot()
    return os.path.join(root, "CIME", "Tools")


def bootstrap_cime_script(cimeroot: Optional[str] = None) -> str:
    """Full-fidelity replacement for ``from standard_script_setup import *``.

    This is the single call that entry-point scripts should make when
    migrating away from ``standard_script_setup``.  It reproduces all
    side effects of the legacy star-import in one place:

    1. Enforces Python >= 3.9 (hard error).
    2. Warns when Python < 3.10 (soft warning to stderr).
    3. Resolves CIMEROOT, prepends it and ``CIME/Tools`` to ``sys.path``,
       and sets ``os.environ["CIMEROOT"]`` — identical to
       ``bootstrap_cime()``.
    4. Calls ``CIME.utils.stop_buffering_output()`` to enable unbuffered
       stdout/stderr, matching the behaviour of ``standard_script_setup``
       which calls this at import time.

    ``stop_buffering_output`` is imported lazily (inside the function body)
    to avoid a circular-import hazard: this module is intentionally
    standalone and may be imported before ``CIME.utils`` is reachable.
    Once ``bootstrap_cime()`` has run, ``CIME.utils`` is importable, so
    the lazy import is safe.

    Args:
        cimeroot: Explicit CIMEROOT path. If None, auto-detected.

    Returns:
        The resolved CIMEROOT path.

    Raises:
        RuntimeError: If Python < 3.9 or CIMEROOT cannot be determined.

    Example::

        #!/usr/bin/env python3
        from CIME.core.config.bootstrap import bootstrap_cime_script
        bootstrap_cime_script()

        import argparse
        import logging
        # ... rest of script
    """
    check_minimum_python_version(3, 9)
    check_minimum_python_version(3, 10, warn_only=True)
    root = bootstrap_cime(cimeroot=cimeroot)
    from CIME.utils import stop_buffering_output  # noqa: PLC0415 (lazy import)

    stop_buffering_output()
    return root


def check_minimum_python_version(
    major: int = 3, minor: int = 9, warn_only: bool = False
) -> None:
    """Check that the running Python meets minimum version requirements.

    Consolidated from CIME/Tools/standard_script_setup.py.

    Args:
        major: Required major version.
        minor: Required minimum minor version.
        warn_only: If True, print warning instead of raising.

    Raises:
        RuntimeError: If version is insufficient and warn_only is False.
    """
    if sys.version_info >= (major, minor):
        return
    msg = (
        f"Python {major}.{minor} is {'recommended' if warn_only else 'required'} "
        f"to run CIME. You have {sys.version_info[0]}.{sys.version_info[1]}"
    )
    if warn_only:
        print(msg + ".", file=sys.stderr)
        return
    raise RuntimeError(msg + " - please use a newer version of Python.")
