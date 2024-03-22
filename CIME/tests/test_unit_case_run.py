import unittest
from unittest import mock

from CIME.utils import CIMEError
from CIME.case.case_run import TERMINATION_TEXT
from CIME.case.case_run import _post_run_check


def _case_post_run_check():
    case = mock.MagicMock()

    # RUNDIR, COMP_INTERFACE, COMP_CPL, COMP_ATM, COMP_OCN, MULTI_DRIVER
    case.get_value.side_effect = ("/tmp/run", "mct", "cpl", "satm", "socn", False)

    # COMP_CLASSES
    case.get_values.return_value = ("CPL", "ATM", "OCN")

    return case


class TestCaseSubmit(unittest.TestCase):
    @mock.patch("os.stat")
    @mock.patch("os.path.isfile")
    def test_post_run_check(self, isfile, stat):
        isfile.return_value = True

        stat.return_value.st_size = 1024

        # no exceptions means success
        for x in TERMINATION_TEXT:
            case = _case_post_run_check()

            with mock.patch("builtins.open", mock.mock_open(read_data=x)) as mock_file:
                _post_run_check(case, "1234")

    @mock.patch("os.stat")
    @mock.patch("os.path.isfile")
    def test_post_run_check_no_termination(self, isfile, stat):
        isfile.return_value = True

        stat.return_value.st_size = 1024

        case = _case_post_run_check()

        with self.assertRaises(CIMEError):
            with mock.patch(
                "builtins.open",
                mock.mock_open(read_data="I DONT HAVE A TERMINATION MESSAGE"),
            ) as mock_file:
                _post_run_check(case, "1234")
