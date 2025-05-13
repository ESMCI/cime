import io
import unittest
from unittest import mock

from CIME.hist_utils import copy_histfiles
from CIME.XML.archive import Archive


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
