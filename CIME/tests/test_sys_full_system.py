#!/usr/bin/env python3

import os

from CIME import get_tests
from CIME import test_status
from CIME import utils
from CIME import wait_for_tests
from CIME.tests import base


class TestFullSystem(base.BaseTestCase):
    def test_full_system(self):
        # Put this inside any test that's slow
        if self.FAST_ONLY:
            self.skipTest("Skipping slow test")

        driver = utils.get_cime_default_driver()
        if driver == "mct":
            cases = self._create_test(
                ["--walltime=0:15:00", "cime_developer"], test_id=self._baseline_name
            )
        else:
            cases = self._create_test(
                ["--walltime=0:30:00", "cime_developer"], test_id=self._baseline_name
            )

        self.run_cmd_assert_result(
            "%s/cs.status.%s" % (self._testroot, self._baseline_name),
            from_dir=self._testroot,
        )

        # Ensure that we can get test times
        for case_dir in cases:
            tstatus = os.path.join(case_dir, "TestStatus")
            test_time = wait_for_tests.get_test_time(os.path.dirname(tstatus))
            self.assertIs(
                type(test_time), int, msg="get time did not return int for %s" % tstatus
            )
            self.assertTrue(test_time > 0, msg="test time was zero for %s" % tstatus)

        # Test that re-running works
        skip_tests = None
        if utils.get_cime_default_driver() == "nuopc":
            skip_tests = [
                "SMS_Ln3.T42_T42.S",
                "PRE.f19_f19.ADESP_TEST",
                "PRE.f19_f19.ADESP",
                "DAE.ww3a.ADWAV",
            ]
        tests = get_tests.get_test_suite(
            "cime_developer",
            machine=self._machine,
            compiler=self._compiler,
            skip_tests=skip_tests,
        )

        for test in tests:
            casedir = self.get_casedir(test, cases)

            # Subtle issue: The run phases of these tests will be in the PASS state until
            # the submitted case.test script is run, which could take a while if the system is
            # busy. This potentially leaves a window where the wait_for_tests command below will
            # not wait for the re-submitted jobs to run because it sees the original PASS.
            # The code below forces things back to PEND to avoid this race condition. Note
            # that we must use the MEMLEAK phase, not the RUN phase, because RUN being in a non-PEND
            # state is how system tests know they are being re-run and must reset certain
            # case settings.
            if self._hasbatch:
                with test_status.TestStatus(test_dir=casedir) as ts:
                    ts.set_status(
                        test_status.MEMLEAK_PHASE, test_status.TEST_PEND_STATUS
                    )

            self.run_cmd_assert_result(
                "./case.submit --skip-preview-namelist", from_dir=casedir
            )

        self._wait_for_tests(self._baseline_name)
