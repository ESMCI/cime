# Unit tests that get_timing acts only when timing files for the LID exist.
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

        # CASEROOT is the only value get_timing reads from the case
        self.case = mock.MagicMock()
        self.case.get_value.return_value = self.caseroot

    def _touch(self, *names):
        for name in names:
            open(os.path.join(self.caseroot, "timing", name), "w").close()

    def _get_timing(self, expect_log):
        # The parser normally writes the timing files, but it needs a full case and an
        # ESMF profile, so the responsibility moves to tests creating the files
        # themselves. append_case_status is mocked because it writes the "Timing files
        # created" line to CaseStatus.
        with mock.patch.object(get_timing, "_TimingParser"), mock.patch.object(
            get_timing, "append_case_status"
        ) as append_case_status:
            get_timing.get_timing(self.case, LID)

        if expect_log:
            append_case_status.assert_called_once()
        else:
            append_case_status.assert_not_called()

    def test_no_timing_files_does_nothing(self):
        self._get_timing(expect_log=False)

        self.case._gitinterface._git_command.assert_not_called()

    def test_older_timing_files_does_nothing(self):
        # A timing file left by an earlier run is ignored.
        self._touch("cesm.ESMF_Profile.summary.000000-000000")

        self._get_timing(expect_log=False)

        self.case._gitinterface._git_command.assert_not_called()

    def test_timing_files_present_runs_git_add(self):
        self._touch("cesm.ESMF_Profile.summary." + LID, "cesm_timing.case." + LID)

        self._get_timing(expect_log=True)

        self.case._gitinterface._git_command.assert_called_once_with("add", "*." + LID)

    def test_no_gitinterface_with_timing_files_still_logs_to_case_status(self):
        # Cases from create_test have no case-level git repo.
        self.case._gitinterface = None
        self._touch("cesm_timing.case." + LID)

        self._get_timing(expect_log=True)

    def test_no_gitinterface_without_timing_files_does_nothing(self):
        self.case._gitinterface = None

        self._get_timing(expect_log=False)


if __name__ == "__main__":
    unittest.main()
