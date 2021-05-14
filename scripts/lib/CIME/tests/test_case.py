import os
import sys
import unittest

from CIME.case import Case
from CIME import utils as cime_utils

from . import utils

class TestCase(unittest.TestCase):

    def setUp(self):
        self.srcroot = os.path.abspath(cime_utils.get_cime_root())
        self.tempdir = utils.TemporaryDirectory()

        self.mock = utils.Mocker()
        self.mock.patch(Case, "read_xml")
        Case._force_read_only = False # pylint: disable=protected-access
        self.mock.patch('time.strftime', ret='00:00:00')
        self.mock.patch("sys.argv", ret=["/src/create_newcase",
                                            "--machine",
                                            "docker"], is_property=True)

    def test_new_hash(self):
        with self.tempdir as tempdir:
            with Case(tempdir) as case:
                os.environ["USER"] = "root"
                os.environ["HOSTNAME"] = "host1"

                expected = "134a939f62115fb44bf08a46bfb2bd13426833b5c8848cf7c4884af7af05b91a"

                # Check idempotency
                for _ in range(2):
                    value = case.new_hash()

                    self.assertTrue(value == expected,
                                    "{} != {}".format(value, expected))

                os.environ["USER"] = "johndoe"

                expected = "bb59f1c473ac07e9dd30bfab153c0530a777f89280b716cf42e6fe2f49811a6e"

                value = case.new_hash()

                self.assertTrue(value == expected,
                                "{} != {}".format(value, expected))

    def test_create(self):
        with self.tempdir as tempdir:
            caseroot = os.path.join(tempdir, "test1")
            with Case(caseroot, read_only=False) as case:
                os.environ["USER"] = "root"
                os.environ["HOSTNAME"] = "host1"
                os.environ["CIME_MODEL"] = "cesm"

                # Need to mock all of these to prevent errors with xml files
                # just want to ensure `create` calls `set_lookup_value`
                # correctly.
                _configure = self.mock.patch(case, 'configure')
                _create_caseroot = self.mock.patch(case, 'create_caseroot')
                _apply_user_mods = self.mock.patch(case, 'apply_user_mods')
                _lock_file = self.mock.patch('CIME.case.case.lock_file')
                _set_lookup_value = self.mock.patch(case, "set_lookup_value")

                srcroot = os.path.abspath(os.path.join(
                    os.path.dirname(__file__), "../../../../../"))
                case.create("test1", srcroot, "A", "f19_g16_rx1",
                            machine_name="ubuntu-latest")

                # Check that they're all called
                _configure.assert_called_with(args=["A", "f19_g16_rx1"])
                _create_caseroot.assert_called()
                _apply_user_mods.assert_called()
                _lock_file.assert_called()

                self.assertTrue(_set_lookup_value.calls[-1]['args'][0] ==
                                "CASE_HASH")
                self.assertTrue(_set_lookup_value.calls[-1]['args'][1] ==
                                "134a939f62115fb44bf08a46bfb2bd13426833b5c8848cf7c4884af7af05b91a")

class TestCase_RecordCmd(unittest.TestCase):

    def setUp(self):
        self.srcroot = os.path.abspath(cime_utils.get_cime_root())
        self.tempdir = utils.TemporaryDirectory()

        self.mock = utils.Mocker()
        self.mock.patch(Case, "__init__", ret=None)
        self.mock.patch(Case, "flush", ret=utils.Mocker())
        # Case.__init__ = utils.Mocker()
        # Case.flush = utils.Mocker()
        Case._force_read_only = False # pylint: disable=protected-access

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
                ret=utils.Mocker())
            mock.patch("time.strftime", ret="00:00:00")
            mock.patch("sys.argv", ret=["/src/create_newcase"], is_property=True)

            with Case(tempdir) as case:
                case.get_value = utils.Mocker(
                    side_effect=[tempdir, "/src"]
                )

                case.record_cmd(init=True)

        self.assertTrue(open_mock.calls[0]["args"] ==
                        ("{}/replay.sh".format(tempdir), "a"))

        expected = [
            "#!/bin/bash\n\n",
            "set -e\n\n",
            "# Created 00:00:00\n\n",
            "CASEDIR=\"{}\"\n\n".format(tempdir),
            "/src/create_newcase\n\n",
            "cd \"${CASEDIR}\"\n\n",
        ]

        calls = open_mock.ret.method_calls["writelines"][0]["args"][0]

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
            mock.patch("sys.argv", ret=["./create_newcase"], is_property=True)

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

        calls = open_mock.ret.method_calls["writelines"][0]["args"][0]

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

        calls = open_mock.ret.method_calls["writelines"][0]["args"][0]

        self.assert_calls_match(calls, expected)

if __name__ == '__main__':
    unittest.main()
