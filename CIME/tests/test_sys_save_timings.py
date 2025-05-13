#!/usr/bin/env python3

import getpass
import glob
import os

from CIME import provenance
from CIME import utils
from CIME.tests import base
from CIME.case.case import Case


class TestSaveTimings(base.BaseTestCase):
    def simple_test(self, manual_timing=False):
        if self.NO_FORTRAN_RUN:
            self.skipTest("Skipping fortran test")
        timing_flag = "" if manual_timing else "--save-timing"
        driver = utils.get_cime_default_driver()
        if driver == "mct":
            walltime = "00:15:00"
        else:
            walltime = "00:30:00"
        self._create_test(
            ["SMS_Ln9_P1.f19_g16_rx1.A", timing_flag, "--walltime=" + walltime],
            test_id=self._baseline_name,
        )

        statuses = glob.glob(
            "%s/*%s/TestStatus" % (self._testroot, self._baseline_name)
        )
        self.assertEqual(
            len(statuses),
            1,
            msg="Should have had exactly one match, found %s" % statuses,
        )
        casedir = os.path.dirname(statuses[0])

        with Case(casedir, read_only=True) as case:
            lids = utils.get_lids(case)
            timing_dir = case.get_value("SAVE_TIMING_DIR")
            casename = case.get_value("CASE")

        self.assertEqual(len(lids), 1, msg="Expected one LID, found %s" % lids)

        if manual_timing:
            self.run_cmd_assert_result(
                "cd %s && %s/save_provenance postrun" % (casedir, self.TOOLS_DIR)
            )
        if self._config.test_mode == "e3sm":
            provenance_glob = os.path.join(
                timing_dir,
                "performance_archive",
                getpass.getuser(),
                casename,
                lids[0] + "*",
            )
            provenance_dirs = glob.glob(provenance_glob)
            self.assertEqual(
                len(provenance_dirs),
                1,
                msg="wrong number of provenance dirs, expected 1, got {}, looked for {}".format(
                    provenance_dirs, provenance_glob
                ),
            )
            self.verify_perms("".join(provenance_dirs))

    def test_save_timings(self):
        self.simple_test()

    def test_save_timings_manual(self):
        self.simple_test(manual_timing=True)

    def _record_success(
        self,
        test_name,
        test_success,
        commit,
        exp_last_pass,
        exp_trans_fail,
        baseline_dir,
    ):
        provenance.save_test_success(
            baseline_dir, None, test_name, test_success, force_commit_test=commit
        )
        was_success, last_pass, trans_fail = provenance.get_test_success(
            baseline_dir, None, test_name, testing=True
        )
        self.assertEqual(
            test_success,
            was_success,
            msg="Broken was_success {} {}".format(test_name, commit),
        )
        self.assertEqual(
            last_pass,
            exp_last_pass,
            msg="Broken last_pass {} {}".format(test_name, commit),
        )
        self.assertEqual(
            trans_fail,
            exp_trans_fail,
            msg="Broken trans_fail {} {}".format(test_name, commit),
        )
        if test_success:
            self.assertEqual(exp_last_pass, commit, msg="Should never")

    def test_success_recording(self):
        if self._config.test_mode == "e3sm":
            self.skipTest("Skipping success recording tests. E3SM feature")

        fake_test1 = "faketest1"
        fake_test2 = "faketest2"
        baseline_dir = os.path.join(self._baseline_area, self._baseline_name)

        # Test initial state
        was_success, last_pass, trans_fail = provenance.get_test_success(
            baseline_dir, None, fake_test1, testing=True
        )
        self.assertFalse(was_success, msg="Broken initial was_success")
        self.assertEqual(last_pass, None, msg="Broken initial last_pass")
        self.assertEqual(trans_fail, None, msg="Broken initial trans_fail")

        # Test first result (test1 fails, test2 passes)
        #                    test_name , success, commit , expP , expTF, baseline)
        self._record_success(fake_test1, False, "AAA", None, "AAA", baseline_dir)
        self._record_success(fake_test2, True, "AAA", "AAA", None, baseline_dir)

        # Test second result matches first (no transition) (test1 fails, test2 passes)
        #                    test_name , success, commit , expP , expTF, baseline)
        self._record_success(fake_test1, False, "BBB", None, "AAA", baseline_dir)
        self._record_success(fake_test2, True, "BBB", "BBB", None, baseline_dir)

        # Test transition to new state (first real transition) (test1 passes, test2 fails)
        #                    test_name , success, commit , expP , expTF, baseline)
        self._record_success(fake_test1, True, "CCC", "CCC", "AAA", baseline_dir)
        self._record_success(fake_test2, False, "CCC", "BBB", "CCC", baseline_dir)

        # Test transition to new state (second real transition) (test1 fails, test2 passes)
        #                    test_name , success, commit , expP , expTF, baseline)
        self._record_success(fake_test1, False, "DDD", "CCC", "DDD", baseline_dir)
        self._record_success(fake_test2, True, "DDD", "DDD", "CCC", baseline_dir)

        # Test final repeat (test1 fails, test2 passes)
        #                    test_name , success, commit , expP , expTF, baseline)
        self._record_success(fake_test1, False, "EEE", "CCC", "DDD", baseline_dir)
        self._record_success(fake_test2, True, "EEE", "EEE", "CCC", baseline_dir)

        # Test final transition (test1 passes, test2 fails)
        #                    test_name , success, commit , expP , expTF, baseline)
        self._record_success(fake_test1, True, "FFF", "FFF", "DDD", baseline_dir)
        self._record_success(fake_test2, False, "FFF", "EEE", "FFF", baseline_dir)
