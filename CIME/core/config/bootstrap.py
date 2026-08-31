"""
Centralized sys.path management for CIME.

CIME is not pip-installed; it relies on sys.path manipulation so that
scripts executed via symlinks (e.g. case.setup, xmlchange) can find
the CIME package. This module consolidates the various sys.path.insert
patterns scattered across the codebase into one place.

**This module is standalone for Slice 1** — existing call-sites are NOT
modified yet. Migration will happen incrementally in later slices.

Typical usage (future, after wiring)::

    from CIME.core.config.bootstrap import bootstrap_cime
    bootstrap_cime()                     # auto-detect CIMEROOT
    bootstrap_cime(cimeroot="/explicit") # explicit root
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
