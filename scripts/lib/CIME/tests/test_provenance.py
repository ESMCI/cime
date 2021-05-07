import os
import sys
import unittest

from CIME import provenance

from . import utils

class TestProvenance(unittest.TestCase):
    def test_run_git_cmd_recursively(self):
        with utils.Mocker() as mock:
            open_mock = mock.patch(
                "builtins.open" if sys.version_info.major > 2 else
                    "__builtin__.open",
                ret=utils.Mocker()
            )
            provenance.run_cmd = utils.Mocker(return_value=(0, "data", None))
            provenance._run_git_cmd_recursively('status', '/srcroot', '/output.txt') # pylint: disable=protected-access

        self.assertTrue(
            open_mock.calls[0]["args"] == ("/output.txt", "w"),
            open_mock.calls
        )

        write = open_mock._ret.method_calls["write"]

        self.assertTrue(write[0]["args"][0] == "data\n\n", write)
        self.assertTrue(write[1]["args"][0] == "data\n", write)

        run_cmd = provenance.run_cmd.calls

        self.assertTrue(run_cmd[0]["args"][0] == "git status")
        self.assertTrue(run_cmd[0]["kwargs"]["from_dir"] == "/srcroot")

        self.assertTrue(run_cmd[1]["args"][0] == "git submodule foreach"
                        " --recursive \"git status; echo\"", run_cmd)
        self.assertTrue(run_cmd[1]["kwargs"]["from_dir"] == "/srcroot")

    def test_run_git_cmd_recursively_error(self):
        with utils.Mocker() as mock:
            open_mock = mock.patch(
                "builtins.open" if sys.version_info.major > 2 else
                    "__builtin__.open",
                ret=utils.Mocker()
            )
            provenance.run_cmd = utils.Mocker(return_value=(1, "data", "error"))
            provenance._run_git_cmd_recursively('status', '/srcroot', '/output.txt') # pylint: disable=protected-access

        write = open_mock._ret.method_calls["write"]

        self.assertTrue(write[0]["args"][0] == "error\n\n", write)
        self.assertTrue(write[1]["args"][0] == "error\n", write)

        run_cmd = provenance.run_cmd.calls

        self.assertTrue(run_cmd[0]["args"][0] == "git status")
        self.assertTrue(run_cmd[0]["kwargs"]["from_dir"] == "/srcroot")

        self.assertTrue(run_cmd[1]["args"][0] == "git submodule foreach"
                        " --recursive \"git status; echo\"", run_cmd)
        self.assertTrue(run_cmd[1]["kwargs"]["from_dir"] == "/srcroot")

    def test_record_git_provenance(self):
        with utils.Mocker() as mock:
            open_mock = mock.patch(
                "builtins.open" if sys.version_info.major > 2 else
                    "__builtin__.open",
                ret=utils.Mocker()
            )

            provenance.safe_copy = utils.Mocker()
            provenance.run_cmd = utils.Mocker(return_value=(0, "data", None))
            provenance._record_git_provenance("/srcroot", "/output", "5") # pylint: disable=protected-access

        expected = [
            ("/output/GIT_STATUS.5", "w"),
            ("/output/GIT_DIFF.5", "w"),
            ("/output/GIT_LOG.5", "w"),
            ("/output/GIT_REMOTE.5", "w")
        ]

        for i in range(4):
             self.assertTrue(
                 open_mock.calls[i]["args"] == expected[i], open_mock.calls)

        write = open_mock._ret.method_calls["write"]

        expected = [
            "data\n\n",
            "data\n",
        ]

        for x in range(8):
            self.assertTrue(write[x]["args"][0] == expected[x%2], write)

        run_cmd = provenance.run_cmd.calls

        expected = [
            "git status",
            "git submodule foreach --recursive \"git status; echo\"",
            "git diff",
            "git submodule foreach --recursive \"git diff; echo\"",
            "git log --first-parent --pretty=oneline -n 5",
            "git submodule foreach --recursive \"git log --first-parent"
                " --pretty=oneline -n 5; echo\"",
            "git remote -v",
            "git submodule foreach --recursive \"git remote -v; echo\"",
        ]

        for x in range(len(run_cmd)):
            self.assertTrue(run_cmd[x]["args"][0] == expected[x], run_cmd[x])

        self.assertTrue(
            provenance.safe_copy.calls[0]["args"][0] == "/srcroot/.git/config",
            provenance.safe_copy.calls
        )
        self.assertTrue(
            provenance.safe_copy.calls[0]["args"][1] == "/output/GIT_CONFIG.5",
            provenance.safe_copy.calls
        )

if __name__ == '__main__':
    sys.path.insert(0, os.path.abspath(os.path.join('.', '..', '..', 'lib')))
    unittest.main()
