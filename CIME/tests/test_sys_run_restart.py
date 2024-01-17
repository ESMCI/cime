#!/usr/bin/env python3

import os

from CIME import utils
from CIME.tests import base


class TestRunRestart(base.BaseTestCase):
    def test_run_restart(self):
        if self.NO_FORTRAN_RUN:
            self.skipTest("Skipping fortran test")
        driver = utils.get_cime_default_driver()
        if driver == "mct":
            walltime = "00:15:00"
        else:
            walltime = "00:30:00"

        casedir = self._create_test(
            ["--walltime " + walltime, "NODEFAIL_P1.f09_g16.X"],
            test_id=self._baseline_name,
        )
        rundir = utils.run_cmd_no_fail("./xmlquery RUNDIR --value", from_dir=casedir)
        fail_sentinel = os.path.join(rundir, "FAIL_SENTINEL")
        self.assertTrue(os.path.exists(fail_sentinel), msg="Missing %s" % fail_sentinel)

        self.assertEqual(open(fail_sentinel, "r").read().count("FAIL"), 3)

    def test_run_restart_too_many_fails(self):
        if self.NO_FORTRAN_RUN:
            self.skipTest("Skipping fortran test")
        driver = utils.get_cime_default_driver()
        if driver == "mct":
            walltime = "00:15:00"
        else:
            walltime = "00:30:00"

        casedir = self._create_test(
            ["--walltime " + walltime, "NODEFAIL_P1.f09_g16.X"],
            test_id=self._baseline_name,
            env_changes="NODEFAIL_NUM_FAILS=5",
            run_errors=True,
        )
        rundir = utils.run_cmd_no_fail("./xmlquery RUNDIR --value", from_dir=casedir)
        fail_sentinel = os.path.join(rundir, "FAIL_SENTINEL")
        self.assertTrue(os.path.exists(fail_sentinel), msg="Missing %s" % fail_sentinel)

        self.assertEqual(open(fail_sentinel, "r").read().count("FAIL"), 4)
