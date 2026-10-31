import os
import tempfile
import unittest
from unittest import mock

from CIME import get_timing

LID = "123456-654321"


class TestGetTimingGitAdd(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.caseroot = tmp.name
        os.makedirs(os.path.join(self.caseroot, "timing"))

        self.case = mock.MagicMock()
        self.case.get_value.side_effect = {"CASEROOT": self.caseroot}.get

    def _touch(self, *names):
        for name in names:
            open(os.path.join(self.caseroot, "timing", name), "w").close()

    def _get_timing(self):
        # The parser normally writes the timing files, but it needs a full case and an
        # ESMF profile, so the responsibility moves to tests creating the files
        # themselves. append_case_status is mocked because it writes a CaseStatus file
        # into the working directory.
        with mock.patch.object(get_timing, "_TimingParser"), mock.patch.object(
            get_timing, "append_case_status"
        ):
            get_timing.get_timing(self.case, LID)

    def test_no_timing_files_does_nothing(self):
        # Intentionally create no timing files.
        self._get_timing()

        self.case._gitinterface._git_command.assert_not_called()

    def test_older_timing_files_does_nothing(self):
        # A timing file left by an earlier run is ignored.
        self._touch("cesm.ESMF_Profile.summary.000000-000000")

        self._get_timing()

        self.case._gitinterface._git_command.assert_not_called()

    def test_timing_files_present_runs_git_add(self):
        # Timing files for this run exist, so they are added to the case repo.
        self._touch("cesm.ESMF_Profile.summary." + LID, "cesm_timing.case." + LID)

        self._get_timing()

        self.case._gitinterface._git_command.assert_called_once_with("add", "*." + LID)

    def test_no_gitinterface_does_not_call_git(self):
        # Cases from create_test have no case-level git repo, so get_timing must not
        # touch git; it would raise AttributeError on None if it did.
        self.case._gitinterface = None
        self._touch("cesm_timing.case." + LID)

        self._get_timing()


if __name__ == "__main__":
    unittest.main()
