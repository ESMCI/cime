#!/usr/bin/env python3

import os
import time

from CIME import utils
from CIME.tests import base


class TestUserConcurrentMods(base.BaseTestCase):
    def test_user_concurrent_mods(self):
        # Put this inside any test that's slow
        if self.FAST_ONLY:
            self.skipTest("Skipping slow test")

        casedir = self._create_test(
            ["--walltime=0:30:00", "TESTRUNUSERXMLCHANGE_Mmpi-serial.f19_g16.X"],
            test_id=self._baseline_name,
        )

        with utils.Timeout(3000):
            while True:
                with open(os.path.join(casedir, "CaseStatus"), "r") as fd:
                    self._wait_for_tests(self._baseline_name)
                    contents = fd.read()
                    if contents.count("model execution success") == 2:
                        break

                time.sleep(5)

        rundir = utils.run_cmd_no_fail("./xmlquery RUNDIR --value", from_dir=casedir)
        if utils.get_cime_default_driver() == "nuopc":
            chk_file = "nuopc.runconfig"
        else:
            chk_file = "drv_in"
        with open(os.path.join(rundir, chk_file), "r") as fd:
            contents = fd.read()
            self.assertTrue("stop_n = 6" in contents)
