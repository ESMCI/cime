#!/usr/bin/env python3

"""Unit tests for ``build._clean_cache_impl``.

These tests exercise the ``--clean-cache`` flag added to ``case.build``,
which removes ``CMakeCache.txt`` and the small CMake bookkeeping files in
``CMakeFiles/`` while preserving compiled object files so the next build can
incrementally re-configure CMake without rebuilding everything.
"""

import os
from unittest import mock

import pytest

from CIME import build


def _make_case(exeroot, caseroot):
    """Build a minimal ``Case`` mock that ``_clean_cache_impl`` understands."""
    case = mock.MagicMock()
    case.get_value.side_effect = lambda key: {
        "EXEROOT": str(exeroot),
        "CASEROOT": str(caseroot),
    }[key]
    return case


@pytest.fixture
def cmake_bld(tmp_path):
    """Create a fake ``cmake-bld`` tree with a populated CMakeFiles/ directory."""
    exeroot = tmp_path / "bld"
    bldroot = exeroot / "cmake-bld"
    cmake_files = bldroot / "CMakeFiles"
    target_dir = cmake_files / "atm.dir"
    target_dir.mkdir(parents=True)

    # The cache file itself.
    (bldroot / "CMakeCache.txt").write_text("# fake cache\n")

    # CMake bookkeeping files that reference the cache.
    (cmake_files / "cmake.check_cache").write_text("")
    (cmake_files / "CMakeCacheCopy.txt").write_text("")

    # A precious object file that must survive a cache clean.
    object_file = target_dir / "foo.f90.o"
    object_file.write_bytes(b"\x7fELF")

    return exeroot, object_file


@mock.patch("CIME.build.unlock_file")
def test_clean_cache_removes_cache_and_bookkeeping(unlock_file, tmp_path, cmake_bld):
    """Happy path: cache + check-cache files removed, objects preserved."""
    exeroot, object_file = cmake_bld
    case = _make_case(exeroot, tmp_path)

    build._clean_cache_impl(case)

    bldroot = exeroot / "cmake-bld"
    assert not (bldroot / "CMakeCache.txt").exists()
    assert not (bldroot / "CMakeFiles" / "cmake.check_cache").exists()
    assert not (bldroot / "CMakeFiles" / "CMakeCacheCopy.txt").exists()

    # Object files must be preserved.
    assert object_file.exists()
    # CMakeFiles/ itself must remain (per-target object directories live there).
    assert (bldroot / "CMakeFiles" / "atm.dir").is_dir()

    case.set_value.assert_any_call("BUILD_COMPLETE", "FALSE")
    case.flush.assert_called_once()
    unlock_file.assert_called_once_with("env_build.xml", str(tmp_path))


@mock.patch("CIME.build.unlock_file")
def test_clean_cache_no_build_dir_is_noop(unlock_file, tmp_path):
    """If the cmake-bld directory does not exist, the call should be a no-op."""
    exeroot = tmp_path / "bld"  # intentionally not created
    case = _make_case(exeroot, tmp_path)

    build._clean_cache_impl(case)

    case.set_value.assert_not_called()
    case.flush.assert_not_called()
    unlock_file.assert_not_called()


@mock.patch("CIME.build.unlock_file")
def test_clean_cache_missing_cache_file_still_resets_state(unlock_file, tmp_path):
    """A cmake-bld dir without CMakeCache.txt still resets BUILD_COMPLETE."""
    exeroot = tmp_path / "bld"
    (exeroot / "cmake-bld").mkdir(parents=True)
    case = _make_case(exeroot, tmp_path)

    build._clean_cache_impl(case)

    case.set_value.assert_any_call("BUILD_COMPLETE", "FALSE")
    case.flush.assert_called_once()
    unlock_file.assert_called_once_with("env_build.xml", str(tmp_path))


def test_clean_dispatches_to_clean_cache_when_requested(tmp_path):
    """``build.clean(..., clean_cache=True)`` must route to the cache impl."""
    exeroot = tmp_path / "bld"
    (exeroot / "cmake-bld").mkdir(parents=True)
    case = _make_case(exeroot, tmp_path)
    case._gitinterface = None

    with mock.patch("CIME.build._clean_cache_impl") as cache_impl, mock.patch(
        "CIME.build._clean_impl"
    ) as full_impl, mock.patch("CIME.build.run_and_log_case_status") as runner:
        runner.side_effect = lambda functor, *a, **kw: functor()

        build.clean(case, clean_cache=True)

        cache_impl.assert_called_once_with(case)
        full_impl.assert_not_called()
        # The phase name should be distinct from the regular clean phase so
        # case status logs make the operation traceable.
        assert runner.call_args.args[1] == "build.clean_cache"


def test_clean_dispatches_to_clean_impl_by_default(tmp_path):
    """Without ``clean_cache``, the legacy clean path must still be used."""
    case = _make_case(tmp_path / "bld", tmp_path)
    case._gitinterface = None

    with mock.patch("CIME.build._clean_cache_impl") as cache_impl, mock.patch(
        "CIME.build._clean_impl"
    ) as full_impl, mock.patch("CIME.build.run_and_log_case_status") as runner:
        runner.side_effect = lambda functor, *a, **kw: functor()

        build.clean(case, clean_all=True)

        full_impl.assert_called_once_with(case, None, True, None)
        cache_impl.assert_not_called()
        assert runner.call_args.args[1] == "build.clean"
