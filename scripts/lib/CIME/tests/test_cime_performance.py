#!/usr/bin/env python3

import time

from CIME.tests import base


class TestCimePerformance(base.BaseTestCase):
    def test_cime_case_ctrl_performance(self):

        ts = time.time()

        num_repeat = 5
        for _ in range(num_repeat):
            self._create_test(["cime_tiny", "--no-build"])

        elapsed = time.time() - ts

        print("Perf test result: {:0.2f}".format(elapsed))
