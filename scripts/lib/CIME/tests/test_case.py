import os
import sys
import unittest

from CIME.case import Case
from CIME import utils as cime_utils

from . import utils

class TestCase_RecordCmd(unittest.TestCase):

    def setUp(self):
        self.srcroot = os.path.abspath(cime_utils.get_cime_root())
        self.tempdir = utils.TemporaryDirectory()

        Case.__init__ = utils.Mocker()
        Case.flush = utils.Mocker()
        Case._force_read_only = False

    def assert_calls_match(self, calls, expected):
        self.assertTrue(len(calls) == len(expected), calls)

        for x, y in zip(calls, expected):
            self.assertTrue(x == y, calls)

    def test_init(self):
        with self.tempdir as tempdir:
            mock = utils.Mocker()
            open_mock = mock.patch(
                "builtins.open" if sys.version_info.major > 2 else
                    "__builtin__.open",
                ret=utils.Mocker()
            )
            mock.patch("time.strftime", ret="00:00:00")
            mock.patch("sys.argv", ret=["/src/create_newcase"], property=True)

            with Case(tempdir) as case:
                case.get_value = utils.Mocker(
                    side_effect=[tempdir, "/src"]
                )

                case.record_cmd(init=True)

        expected = [
            "#!/bin/bash\n\n",
            "set -e\n\n",
            "# Created 00:00:00\n\n",
            "CASEDIR=\"{}\"\n\n".format(tempdir),
            "/src/create_newcase\n\n",
            "cd \"${CASEDIR}\"\n\n",
        ]

        calls = open_mock.method_calls["writelines"][0]["args"][0]

        self.assert_calls_match(calls, expected)

    def test_sub_relative(self):
        with self.tempdir as tempdir:
            mock = utils.Mocker()
            open_mock = mock.patch(
                "builtins.open" if sys.version_info.major > 2 else
                    "__builtin__.open",
                ret=utils.Mocker()
            )
            mock.patch("time.strftime", ret="00:00:00")
            mock.patch("sys.argv", ret=["./create_newcase"], property=True)

            with Case(tempdir) as case:
                case.get_value = utils.Mocker(
                    side_effect=[tempdir, "/src"]
                )

                case.record_cmd(init=True)

        expected = [
            "#!/bin/bash\n\n",
            "set -e\n\n",
            "# Created 00:00:00\n\n",
            "CASEDIR=\"{}\"\n\n".format(tempdir),
            "/src/scripts/create_newcase\n\n",
            "cd \"${CASEDIR}\"\n\n",
        ]

        calls = open_mock.method_calls["writelines"][0]["args"][0]

        self.assert_calls_match(calls, expected)

    def test_cmd_arg(self):
        with self.tempdir as tempdir:
            mock = utils.Mocker()
            open_mock = mock.patch(
                "builtins.open" if sys.version_info.major > 2 else
                    "__builtin__.open",
                ret=utils.Mocker()
            )

            with Case(tempdir) as case:
                case.get_value = utils.Mocker(
                    side_effect=[tempdir, "/src"]
                )

                case.record_cmd(["/some/custom/command", "arg1"])

        expected = [
            "/some/custom/command arg1\n\n",
        ]

        calls = open_mock.method_calls["writelines"][0]["args"][0]

        self.assert_calls_match(calls, expected)

if __name__ == '__main__':
    unittest.main()
