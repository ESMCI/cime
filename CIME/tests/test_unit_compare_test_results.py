#!/usr/bin/env python3

"""
This module contains unit tests for compare_test_results
"""

import unittest
import tempfile
import os
import shutil

from CIME import utils
from CIME import compare_test_results
from CIME.test_status import *
from CIME.tests.case_fake import CaseFake


class TestCaseFake(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.test_root = os.path.join(self.tempdir, "tests")
        self.baseline_root = os.path.join(self.test_root, "baselines")

        # TODO switch to unittest.mock
        self._old_strftime = utils.time.strftime
        utils.time.strftime = lambda *args: "2021-02-20"

        self._old_init = CaseFake.__init__
        CaseFake.__init__ = lambda x, y, *args: self._old_init(
            x, y, create_case_root=False
        )

        self._old_case = compare_test_results.Case
        compare_test_results.Case = CaseFake

    def tearDown(self):
        utils.time.strftime = self._old_strftime
        CaseFake.__init__ = self._old_init
        compare_test_results.Case = self._old_case

        shutil.rmtree(self.tempdir, ignore_errors=True)

    def _compare_test_results(self, baseline, test_id, phases, **kwargs):
        test_status_root = os.path.join(self.test_root, "gnu." + test_id)
        os.makedirs(test_status_root)

        with TestStatus(test_status_root, "test") as status:
            for x in phases:
                status.set_status(x[0], x[1])

        compare_test_results.compare_test_results(
            baseline, self.baseline_root, self.test_root, "gnu", test_id, **kwargs
        )

        compare_log = os.path.join(
            test_status_root, "compare.log.{}.2021-02-20".format(baseline)
        )

        self.assertTrue(os.path.exists(compare_log))

    def test_namelists_only(self):
        compare_test_results.compare_namelists = lambda *args: True
        compare_test_results.compare_history = lambda *args: (True, "Detail comments")

        phases = [
            (SETUP_PHASE, "PASS"),
            (RUN_PHASE, "PASS"),
        ]

        self._compare_test_results(
            "test1", "test-baseline", phases, namelists_only=True
        )

    def test_hist_only(self):
        compare_test_results.compare_namelists = lambda *args: True
        compare_test_results.compare_history = lambda *args: (True, "Detail comments")

        phases = [
            (SETUP_PHASE, "PASS"),
            (RUN_PHASE, "PASS"),
        ]

        self._compare_test_results("test1", "test-baseline", phases, hist_only=True)

    def test_failed_early(self):
        compare_test_results.compare_namelists = lambda *args: True
        compare_test_results.compare_history = lambda *args: (True, "Detail comments")

        phases = [
            (CREATE_NEWCASE_PHASE, "PASS"),
        ]

        self._compare_test_results("test1", "test-baseline", phases)

    def test_baseline(self):
        compare_test_results.compare_namelists = lambda *args: True
        compare_test_results.compare_history = lambda *args: (True, "Detail comments")

        phases = [
            (SETUP_PHASE, "PASS"),
            (RUN_PHASE, "PASS"),
        ]

        self._compare_test_results("test1", "test-baseline", phases)


if __name__ == "__main__":
    unittest.main()
