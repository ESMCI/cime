#!/usr/bin/env python3

"""
Unit tests for ERR system test
"""

import shutil
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from CIME.SystemTests.err import ERR


@pytest.fixture
def tempdir():
    """Create a temporary directory for test files."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def caseroot(tempdir):
    """Create case directory structure."""
    caseroot = tempdir / "caseroot"
    caseroot.mkdir(parents=True, exist_ok=True)

    run_dir = caseroot / "run"
    run_dir.mkdir(parents=True, exist_ok=True)

    return caseroot


def create_mock_case(caseroot, drv_restart_pointer=None):
    """Create a mock case for testing ERR.

    This creates a MagicMock case with the minimum required configuration
    to instantiate an ERR test object.

    Args:
        caseroot: Path to the case root directory
        drv_restart_pointer: Value for DRV_RESTART_POINTER (None if not supported)

    Returns:
        mock case object
    """
    case = mock.MagicMock()

    run_dir = caseroot / "run"

    def get_value(key, *args, **kwargs):
        values = {
            "CASEROOT": str(caseroot),
            "CASEBASEID": "ERR.f19_g16.S",
            "COMP_INTERFACE": "mct",
            "DRV_RESTART_POINTER": drv_restart_pointer,
            "STOP_N": 5,
            "REST_N": 2,
            "STOP_OPTION": "ndays",
            "RUNDIR": str(run_dir),
            "DOUT_S_ROOT": str(caseroot / "archive"),
            "NINST": 1,
            "CASE": "ERR.f19_g16.S",
            "CIME_OUTPUT_ROOT": str(caseroot.parent),
        }
        return values.get(key)

    case.get_value.side_effect = get_value
    case.get_env.return_value.get_jobs.return_value = [("case.run", {})]
    case.get_compset_components.return_value = []

    return case


def setup_archive_with_restart(caseroot, restart_date="2000-01-01-00000"):
    """Create archive directory structure with restart files.

    Args:
        caseroot: Path to case root directory
        restart_date: Name of restart directory (default: "2000-01-01-00000")

    Returns:
        Path to the restart directory
    """
    rest_dir = caseroot / "archive" / "rest" / restart_date
    rest_dir.mkdir(parents=True, exist_ok=True)
    (rest_dir / "rpointer.cpl").touch()
    return rest_dir


@mock.patch(
    "CIME.SystemTests.system_tests_compare_two.SystemTestsCompareTwo._setup_cases_if_not_yet_done"
)
def test_case_two_custom_prerun_action_with_drv_restart_pointer(
    _setup_cases_if_not_yet_done, caseroot
):
    """Test _case_two_custom_prerun_action sets DRV_RESTART_POINTER when supported."""
    case = create_mock_case(caseroot, drv_restart_pointer="rpointer.cpl")
    setup_archive_with_restart(caseroot)

    test = ERR(case)
    test._case1 = mock.MagicMock()
    test._case1.get_value.return_value = str(caseroot / "archive")
    test._case = mock.MagicMock()

    test._case_two_custom_prerun_action()

    test._case.set_value.assert_any_call(
        "DRV_RESTART_POINTER", "rpointer.cpl.2000-01-01-00000"
    )


@mock.patch(
    "CIME.SystemTests.system_tests_compare_two.SystemTestsCompareTwo._setup_cases_if_not_yet_done"
)
def test_case_two_custom_prerun_action_without_drv_restart_pointer(
    _setup_cases_if_not_yet_done, caseroot
):
    """Test _case_two_custom_prerun_action skips DRV_RESTART_POINTER when not supported."""
    case = create_mock_case(caseroot, drv_restart_pointer=None)
    setup_archive_with_restart(caseroot)

    test = ERR(case)
    test._case1 = mock.MagicMock()
    test._case1.get_value.return_value = str(caseroot / "archive")
    test._case = mock.MagicMock()

    test._case_two_custom_prerun_action()

    # Verify DRV_RESTART_POINTER was NOT set
    for call in test._case.set_value.call_args_list:
        assert (
            call[0][0] != "DRV_RESTART_POINTER"
        ), "DRV_RESTART_POINTER should not be set when model doesn't support it"
