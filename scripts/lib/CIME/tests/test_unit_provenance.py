#!/usr/bin/env python3

import os
import sys
import tempfile
import unittest
from unittest import mock

from CIME import provenance
from CIME import utils

# pylint: disable=protected-access
class TestProvenance(unittest.TestCase):
    def test_parse_dot_git_path_error(self):
        with self.assertRaises(utils.CIMEError):
            provenance._parse_dot_git_path("/src/CIME")

    def test_parse_dot_git_path(self):
        value = provenance._parse_dot_git_path("/src/CIME/.git/worktrees/test")

        assert value == "/src/CIME/.git"

    def test_find_git_root(self):
        with tempfile.TemporaryDirectory() as tempdir:
            os.makedirs(os.path.join(tempdir, ".git"))

            value = provenance._find_git_root(tempdir)

            assert value == f"{tempdir}/.git"

    def test_find_git_root_worktree(self):
        with tempfile.TemporaryDirectory() as tempdir:
            with open(os.path.join(tempdir, ".git"), "w") as fd:
                fd.write("gitdir: /src/CIME/.git/worktrees/test")

            value = provenance._find_git_root(tempdir)

            assert value == "/src/CIME/.git/worktrees/test"

    def test_find_git_root_worktree_malformed(self):
        with tempfile.TemporaryDirectory() as tempdir:
            with open(os.path.join(tempdir, ".git"), "w") as fd:
                fd.write("some value: /src/CIME/.git/worktrees/test")

            with self.assertRaises(utils.CIMEError):
                provenance._find_git_root(tempdir)

    def test_find_git_root_error(self):
        with tempfile.TemporaryDirectory() as tempdir:
            with self.assertRaises(utils.CIMEError):
                provenance._find_git_root(tempdir)

    @mock.patch("CIME.provenance.run_cmd")
    def test_run_git_cmd_recursively(self, run_cmd):
        run_cmd.return_value = (0, "data", None)

        with mock.patch("CIME.provenance.open", mock.mock_open()) as m:
            provenance._run_git_cmd_recursively(
                "status", "/srcroot", "/output.txt"
            )  # pylint: disable=protected-access

        m.assert_called_with("/output.txt", "w")

        write = m.return_value.__enter__.return_value.write

        write.assert_any_call("data\n\n")
        write.assert_any_call("data\n")

        run_cmd.assert_any_call("git status", from_dir="/srcroot")
        run_cmd.assert_any_call(
            'git submodule foreach --recursive "git status; echo"', from_dir="/srcroot"
        )

    @mock.patch("CIME.provenance.run_cmd")
    def test_run_git_cmd_recursively_error(self, run_cmd):
        run_cmd.return_value = (1, "data", "error")

        with mock.patch("CIME.provenance.open", mock.mock_open()) as m:
            provenance._run_git_cmd_recursively(
                "status", "/srcroot", "/output.txt"
            )  # pylint: disable=protected-access

        m.assert_called_with("/output.txt", "w")

        write = m.return_value.__enter__.return_value.write

        write.assert_any_call("error\n\n")
        write.assert_any_call("error\n")

        run_cmd.assert_any_call("git status", from_dir="/srcroot")
        run_cmd.assert_any_call(
            'git submodule foreach --recursive "git status; echo"', from_dir="/srcroot"
        )

    @mock.patch("CIME.provenance.safe_copy")
    @mock.patch("CIME.provenance.run_cmd")
    def test_record_git_provenance(self, run_cmd, safe_copy):
        run_cmd.return_value = (0, "data", None)

        with mock.patch("CIME.provenance.open", mock.mock_open()) as m:
            with tempfile.TemporaryDirectory() as tempdir:
                os.makedirs(os.path.join(tempdir, ".git"))

                provenance._record_git_provenance(
                    tempdir, "/output", "5"
                )  # pylint: disable=protected-access

        m.assert_any_call("/output/GIT_STATUS.5", "w")
        m.assert_any_call("/output/GIT_DIFF.5", "w")
        m.assert_any_call("/output/GIT_LOG.5", "w")
        m.assert_any_call("/output/GIT_REMOTE.5", "w")

        write = m.return_value.__enter__.return_value.write

        write.assert_any_call("data\n\n")
        write.assert_any_call("data\n")

        run_cmd.assert_any_call("git status", from_dir=tempdir)
        run_cmd.assert_any_call(
            'git submodule foreach --recursive "git status; echo"', from_dir=tempdir
        )
        run_cmd.assert_any_call("git diff", from_dir=tempdir)
        run_cmd.assert_any_call(
            'git submodule foreach --recursive "git diff; echo"', from_dir=tempdir
        )
        run_cmd.assert_any_call(
            "git log --first-parent --pretty=oneline -n 5", from_dir=tempdir
        )
        run_cmd.assert_any_call(
            'git submodule foreach --recursive "git log --first-parent'
            ' --pretty=oneline -n 5; echo"',
            from_dir=tempdir,
        )
        run_cmd.assert_any_call("git remote -v", from_dir=tempdir)
        run_cmd.assert_any_call(
            'git submodule foreach --recursive "git remote -v; echo"', from_dir=tempdir
        )

        safe_copy.assert_any_call(
            f"{tempdir}/.git/config", "/output/GIT_CONFIG.5", preserve_meta=False
        )


if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(".", "..", "..", "lib")))
    unittest.main()
