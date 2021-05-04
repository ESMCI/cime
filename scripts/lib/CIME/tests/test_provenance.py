import os
import sys
import unittest

from CIME import provenance

# TODO replace with actual mock once 2.7 is dropped
class Mocker:
    calls = []

    def __init__(self, ret=None, cmd=None):
        self._orig = []
        self._ret = ret
        self._cmd = cmd

    def __getattr__(self, name):
        return Mocker(self._ret, name)

    def __call__(self, *args, **kwargs):
        args = list(args)
        if self._cmd is not None:
            args.insert(0, self._cmd)

        call_sig = " ".join([
            x for x in args + [
                "{}={}".format(y, z) for y, z in kwargs.items()]])
        self.calls.append(call_sig)
        return self._ret if self._ret is not None else self

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        for m, module, method in self._orig:
            setattr(sys.modules[module], method, m)

    def patch(self, method, ret=None):
        x = method.split('.')
        main = '.'.join(x[:-1])
        self._orig.append((getattr(sys.modules[main], x[-1]), main, x[-1]))
        setattr(sys.modules[main], x[-1], Mocker(ret, x[-1]))

class TestProvenance(unittest.TestCase):
    def test_run_git_cmd_recursively(self):
        with Mocker() as mock:
            Mocker.calls =[]
            mock.patch("CIME.provenance.run_cmd", (0, "data", None))
            if sys.version_info.major > 2:
                mock.patch("builtins.open")
            else:
                mock.patch("__builtin__.open")

            provenance._run_git_cmd_recursively('status', '/srcroot', '/output.txt') # pylint: disable=protected-access
        expected = [
            "run_cmd git status from_dir=/srcroot",
            ("run_cmd git submodule foreach --recursive \"git status; echo\""
             " from_dir=/srcroot"),
            "open /output.txt w",
            "write data\n\n",
            "write data\n",
        ]

        self.assertTrue(len(expected) == len(mock.calls))

        for x, y in zip(expected, mock.calls):
            self.assertTrue(x == y, "{} != {}".format(x, y))

    def test_run_git_cmd_recursively_error(self):
        with Mocker() as mock:
            Mocker.calls =[]
            mock.patch("CIME.provenance.run_cmd", (1, "data", "error"))
            if sys.version_info.major > 2:
                mock.patch("builtins.open")
            else:
                mock.patch("__builtin__.open")

            provenance._run_git_cmd_recursively('status', '/srcroot', '/output.txt') # pylint: disable=protected-access
        expected = [
            "run_cmd git status from_dir=/srcroot",
            ("run_cmd git submodule foreach --recursive \"git status; echo\""
             " from_dir=/srcroot"),
            "open /output.txt w",
            "write error\n\n",
            "write error\n",
        ]

        self.assertTrue(len(expected) == len(mock.calls))

        for x, y in zip(expected, mock.calls):
            self.assertTrue(x == y, "{} != {}".format(x, y))

    def test_record_git_provenance(self):
        with Mocker() as mock:
            Mocker.calls =[]
            mock.patch("CIME.provenance.safe_copy")
            mock.patch("CIME.provenance.run_cmd", (0, "data", None))
            if sys.version_info.major > 2:
                mock.patch("builtins.open")
            else:
                mock.patch("__builtin__.open")

            provenance._record_git_provenance("/srcroot", "/output", "5") # pylint: disable=protected-access

        expected = [
            "run_cmd git status from_dir=/srcroot",
            ("run_cmd git submodule foreach --recursive \"git status; echo\""
             " from_dir=/srcroot"),
            "open /output/GIT_STATUS.5 w",
            "write data\n\n",
            "write data\n",
            "run_cmd git diff from_dir=/srcroot",
            ("run_cmd git submodule foreach --recursive \"git diff; echo\""
             " from_dir=/srcroot"),
            "open /output/GIT_DIFF.5 w",
            "write data\n\n",
            "write data\n",
            "run_cmd git log --first-parent --pretty=oneline -n 5 from_dir=/srcroot",
            ("run_cmd git submodule foreach --recursive \"git log"
             " --first-parent --pretty=oneline -n 5; echo\" from_dir=/srcroot"),
            "open /output/GIT_LOG.5 w",
            "write data\n\n",
            "write data\n",
            "run_cmd git remote -v from_dir=/srcroot",
            ("run_cmd git submodule foreach --recursive \"git remote"
             " -v; echo\" from_dir=/srcroot"),
            "open /output/GIT_REMOTE.5 w",
            "write data\n\n",
            "write data\n",
            ("safe_copy /srcroot/.git/config /output/GIT_CONFIG.5"
             " preserve_meta=False")
        ]

        self.assertTrue(len(expected) == len(mock.calls),
                        mock.calls)

        for x, y in zip(expected, mock.calls):
            self.assertTrue(x == y, "{} != {}".format(x, y))

if __name__ == '__main__':
    sys.path.insert(0, os.path.abspath(os.path.join('.', '..', '..', 'lib')))
    unittest.main()
