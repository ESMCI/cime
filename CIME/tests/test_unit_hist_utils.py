import unittest
from unittest import mock

import pytest

from CIME.hist_utils import copy_histfiles, get_ts_synopsis


class TestHistUtils(unittest.TestCase):
    @mock.patch("CIME.hist_utils.safe_copy")
    def test_copy_histfiles_exclude(self, safe_copy):
        case = mock.MagicMock()

        case.get_env.return_value.get_latest_hist_files.side_effect = [
            ["/tmp/testing.cpl.hi.nc"],
            ["/tmp/testing.atm.hi.nc"],
        ]

        case.get_env.return_value.exclude_testing.side_effect = [True, False]

        case.get_value.side_effect = [
            "/tmp",  # RUNDIR
            None,  # RUN_REFCASE
            "testing",  # CASE
            True,  # TEST
            True,  # TEST
        ]

        case.get_compset_components.return_value = ["atm"]

        test_files = [
            "testing.cpl.hi.nc",
        ]

        with mock.patch("os.listdir", return_value=test_files):
            comments, num_copied = copy_histfiles(case, "base")

        assert num_copied == 1

    @mock.patch("CIME.hist_utils.safe_copy")
    def test_copy_histfiles(self, safe_copy):
        case = mock.MagicMock()

        case.get_env.return_value.get_latest_hist_files.return_value = [
            "/tmp/testing.cpl.hi.nc",
        ]

        case.get_env.return_value.exclude_testing.return_value = False

        case.get_value.side_effect = [
            "/tmp",  # RUNDIR
            None,  # RUN_REFCASE
            "testing",  # CASE
            True,  # TEST
        ]

        case.get_compset_components.return_value = []

        test_files = [
            "testing.cpl.hi.nc",
        ]

        with mock.patch("os.listdir", return_value=test_files):
            comments, num_copied = copy_histfiles(case, "base")

        assert num_copied == 1


def test_get_ts_synopsis_pass_at_end():
    """Comments ending with PASS should return empty string."""
    assert get_ts_synopsis("stuff\nPASS") == ""


def test_get_ts_synopsis_pass_on_own_line_with_multiple_lines_after():
    """PASS on its own line followed by multiple lines of content.

    Fix for #4932: When baseline comparison passes but additional content
    (like bless messages) is appended after the PASS line, the synopsis
    should still be empty.

    Note: Most cases are covered by doctests in hist_utils.py. These tests
    cover additional edge cases.
    """
    comments = "Comparing hists\nPASS\nBless info line 1\nBless info line 2\n"
    assert get_ts_synopsis(comments) == ""


@pytest.mark.parametrize(
    "variant",
    ["Pass", "pass", "PASSING", "passed", "  PASS", "PASS extra"],
)
def test_get_ts_synopsis_pass_is_case_sensitive_and_exact(variant):
    """Only the exact token 'PASS' on its own line marks success.

    Variants like 'Pass', 'pass', 'PASSING', or indented '  PASS' must NOT
    short-circuit to an empty synopsis. _compare_hists is the sole producer
    of the PASS marker and always writes it verbatim and unindented; anything
    else falls through to the normal failure-detection logic (and ultimately
    the catch-all if nothing matches).
    """
    catch_all = "ERROR Could not interpret CPRNC output"
    assert get_ts_synopsis(f"header\n{variant}") == catch_all


def test_get_ts_synopsis_pass_handles_crlf_line_endings():
    """PASS on a CRLF-terminated line is still recognized as success.

    In practice _compare_hists writes LF-terminated strings on Unix, but the
    regex tolerates an optional CR so that comments originating from any
    platform-normalized source (Windows-edited bless logs, etc.) are not
    misreported as 'ERROR Could not interpret CPRNC output'.
    """
    assert get_ts_synopsis("header\r\nPASS\r\n") == ""
    assert get_ts_synopsis("header\r\nPASS\r\n  Most recent bless: abc123\r\n") == ""
