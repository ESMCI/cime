#!/usr/bin/env python3

from CIME import utils
from CIME.tests import base


class TestSingleSubmit(base.BaseTestCase):
    def test_single_submit(self):
        # Skip unless on a batch system and users did not select no-batch
        if not self._hasbatch:
            self.skipTest("Skipping single submit. Not valid without batch")
        if self._config.test_mode == "cesm":
            self.skipTest("Skipping single submit. E3SM experimental feature")
        if self._machine not in ["sandiatoss3"]:
            self.skipTest("Skipping single submit. Only works on sandiatoss3")

        # Keep small enough for now that we don't have to worry about load balancing
        self._create_test(
            ["--single-submit", "SMS_Ln9_P8.f45_g37_rx1.A", "SMS_Ln9_P8.f19_g16_rx1.A"],
            env_changes="unset CIME_GLOBAL_WALLTIME &&",
        )
