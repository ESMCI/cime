#!/usr/bin/env python3

import glob
import logging
import os
import unittest
from unittest import mock

from CIME import get_tests
from CIME import utils
from CIME import test_status
from CIME import test_scheduler
from CIME.tests import base


class TestTestScheduler(base.BaseTestCase):
    @mock.patch("time.strftime", return_value="00:00:00")
    def test_chksum(self, strftime):  # pylint: disable=unused-argument
        if self._config.test_mode == "e3sm":
            self.skipTest("Skipping chksum test. Depends on CESM settings")

        ts = test_scheduler.TestScheduler(
            ["SEQ_Ln9.f19_g16_rx1.A.cori-haswell_gnu"],
            machine_name="cori-haswell",
            chksum=True,
            test_root="/tests",
        )

        with mock.patch.object(ts, "_shell_cmd_for_phase") as _shell_cmd_for_phase:
            ts._run_phase(
                "SEQ_Ln9.f19_g16_rx1.A.cori-haswell_gnu"
            )  # pylint: disable=protected-access

            _shell_cmd_for_phase.assert_called_with(
                "SEQ_Ln9.f19_g16_rx1.A.cori-haswell_gnu",
                "./case.submit --skip-preview-namelist --chksum",
                "RUN",
                from_dir="/tests/SEQ_Ln9.f19_g16_rx1.A.cori-haswell_gnu.00:00:00",
            )

    def test_a_phases(self):
        # exclude the MEMLEAK tests here.
        tests = get_tests.get_full_test_names(
            [
                "cime_test_only",
                "^TESTMEMLEAKFAIL_P1.f09_g16.X",
                "^TESTMEMLEAKPASS_P1.f09_g16.X",
                "^TESTRUNSTARCFAIL_P1.f19_g16_rx1.A",
                "^TESTTESTDIFF_P1.f19_g16_rx1.A",
                "^TESTBUILDFAILEXC_P1.f19_g16_rx1.A",
                "^TESTRUNFAILEXC_P1.f19_g16_rx1.A",
            ],
            self._machine,
            self._compiler,
        )
        self.assertEqual(len(tests), 3)
        ct = test_scheduler.TestScheduler(
            tests,
            test_root=self._testroot,
            output_root=self._testroot,
            compiler=self._compiler,
            mpilib=self.TEST_MPILIB,
            machine_name=self.MACHINE.get_machine_name(),
        )

        build_fail_test = [item for item in tests if "TESTBUILDFAIL" in item][0]
        run_fail_test = [item for item in tests if "TESTRUNFAIL" in item][0]
        pass_test = [item for item in tests if "TESTRUNPASS" in item][0]

        self.assertTrue(
            "BUILDFAIL" in build_fail_test, msg="Wrong test '%s'" % build_fail_test
        )
        self.assertTrue(
            "RUNFAIL" in run_fail_test, msg="Wrong test '%s'" % run_fail_test
        )
        self.assertTrue("RUNPASS" in pass_test, msg="Wrong test '%s'" % pass_test)

        for idx, phase in enumerate(ct._phases):
            for test in ct._tests:
                if phase == test_scheduler.TEST_START:
                    continue
                elif phase == test_status.MODEL_BUILD_PHASE:
                    ct._update_test_status(test, phase, test_status.TEST_PEND_STATUS)

                    if test == build_fail_test:
                        ct._update_test_status(
                            test, phase, test_status.TEST_FAIL_STATUS
                        )
                        self.assertTrue(ct._is_broken(test))
                        self.assertFalse(ct._work_remains(test))
                    else:
                        ct._update_test_status(
                            test, phase, test_status.TEST_PASS_STATUS
                        )
                        self.assertFalse(ct._is_broken(test))
                        self.assertTrue(ct._work_remains(test))

                elif phase == test_status.RUN_PHASE:
                    if test == build_fail_test:
                        with self.assertRaises(utils.CIMEError):
                            ct._update_test_status(
                                test, phase, test_status.TEST_PEND_STATUS
                            )
                    else:
                        ct._update_test_status(
                            test, phase, test_status.TEST_PEND_STATUS
                        )
                        self.assertFalse(ct._work_remains(test))

                        if test == run_fail_test:
                            ct._update_test_status(
                                test, phase, test_status.TEST_FAIL_STATUS
                            )
                            self.assertTrue(ct._is_broken(test))
                        else:
                            ct._update_test_status(
                                test, phase, test_status.TEST_PASS_STATUS
                            )
                            self.assertFalse(ct._is_broken(test))

                    self.assertFalse(ct._work_remains(test))

                else:
                    with self.assertRaises(utils.CIMEError):
                        ct._update_test_status(
                            test, ct._phases[idx + 1], test_status.TEST_PEND_STATUS
                        )

                    with self.assertRaises(utils.CIMEError):
                        ct._update_test_status(
                            test, phase, test_status.TEST_PASS_STATUS
                        )

                    ct._update_test_status(test, phase, test_status.TEST_PEND_STATUS)
                    self.assertFalse(ct._is_broken(test))
                    self.assertTrue(ct._work_remains(test))

                    with self.assertRaises(utils.CIMEError):
                        ct._update_test_status(
                            test, phase, test_status.TEST_PEND_STATUS
                        )

                    ct._update_test_status(test, phase, test_status.TEST_PASS_STATUS)

                    with self.assertRaises(utils.CIMEError):
                        ct._update_test_status(
                            test, phase, test_status.TEST_FAIL_STATUS
                        )

                    self.assertFalse(ct._is_broken(test))
                    self.assertTrue(ct._work_remains(test))

    def test_b_full(self):
        tests = get_tests.get_full_test_names(
            ["cime_test_only"], self._machine, self._compiler
        )
        test_id = "%s-%s" % (self._baseline_name, utils.get_timestamp())
        ct = test_scheduler.TestScheduler(
            tests,
            test_id=test_id,
            no_batch=self.NO_BATCH,
            test_root=self._testroot,
            output_root=self._testroot,
            compiler=self._compiler,
            mpilib=self.TEST_MPILIB,
            machine_name=self.MACHINE.get_machine_name(),
        )

        build_fail_test = [item for item in tests if "TESTBUILDFAIL_" in item][0]
        build_fail_exc_test = [item for item in tests if "TESTBUILDFAILEXC" in item][0]
        run_fail_test = [item for item in tests if "TESTRUNFAIL_" in item][0]
        run_fail_exc_test = [item for item in tests if "TESTRUNFAILEXC" in item][0]
        pass_test = [item for item in tests if "TESTRUNPASS" in item][0]
        test_diff_test = [item for item in tests if "TESTTESTDIFF" in item][0]
        mem_fail_test = [item for item in tests if "TESTMEMLEAKFAIL" in item][0]
        mem_pass_test = [item for item in tests if "TESTMEMLEAKPASS" in item][0]
        st_arch_fail_test = [item for item in tests if "TESTRUNSTARCFAIL" in item][0]

        log_lvl = logging.getLogger().getEffectiveLevel()
        logging.disable(logging.CRITICAL)
        try:
            ct.run_tests()
        finally:
            logging.getLogger().setLevel(log_lvl)

        self._wait_for_tests(test_id, expect_works=False)

        test_statuses = glob.glob("%s/*%s/TestStatus" % (self._testroot, test_id))
        self.assertEqual(len(tests), len(test_statuses))

        for x in test_statuses:
            ts = test_status.TestStatus(test_dir=os.path.dirname(x))
            test_name = ts.get_name()
            log_files = glob.glob(
                "%s/%s*%s/TestStatus.log" % (self._testroot, test_name, test_id)
            )
            self.assertEqual(
                len(log_files),
                1,
                "Expected exactly one test_status.TestStatus.log file, found %d"
                % len(log_files),
            )
            log_file = log_files[0]
            if test_name == build_fail_test:

                self.assert_test_status(
                    test_name,
                    ts,
                    test_status.MODEL_BUILD_PHASE,
                    test_status.TEST_FAIL_STATUS,
                )
                data = open(log_file, "r").read()
                self.assertTrue(
                    "Intentional fail for testing infrastructure" in data,
                    "Broken test did not report build error:\n%s" % data,
                )
            elif test_name == build_fail_exc_test:
                data = open(log_file, "r").read()
                self.assert_test_status(
                    test_name,
                    ts,
                    test_status.SHAREDLIB_BUILD_PHASE,
                    test_status.TEST_FAIL_STATUS,
                )
                self.assertTrue(
                    "Exception from init" in data,
                    "Broken test did not report build error:\n%s" % data,
                )
            elif test_name == run_fail_test:
                self.assert_test_status(
                    test_name, ts, test_status.RUN_PHASE, test_status.TEST_FAIL_STATUS
                )
            elif test_name == run_fail_exc_test:
                self.assert_test_status(
                    test_name, ts, test_status.RUN_PHASE, test_status.TEST_FAIL_STATUS
                )
                data = open(log_file, "r").read()
                self.assertTrue(
                    "Exception from run_phase" in data,
                    "Broken test did not report run error:\n%s" % data,
                )
            elif test_name == mem_fail_test:
                self.assert_test_status(
                    test_name,
                    ts,
                    test_status.MEMLEAK_PHASE,
                    test_status.TEST_FAIL_STATUS,
                )
                self.assert_test_status(
                    test_name, ts, test_status.RUN_PHASE, test_status.TEST_PASS_STATUS
                )
            elif test_name == test_diff_test:
                self.assert_test_status(
                    test_name, ts, "COMPARE_base_rest", test_status.TEST_FAIL_STATUS
                )
                self.assert_test_status(
                    test_name, ts, test_status.RUN_PHASE, test_status.TEST_PASS_STATUS
                )
            elif test_name == st_arch_fail_test:
                self.assert_test_status(
                    test_name, ts, test_status.RUN_PHASE, test_status.TEST_PASS_STATUS
                )
                self.assert_test_status(
                    test_name,
                    ts,
                    test_status.STARCHIVE_PHASE,
                    test_status.TEST_FAIL_STATUS,
                )
            else:
                self.assertTrue(test_name in [pass_test, mem_pass_test])
                self.assert_test_status(
                    test_name, ts, test_status.RUN_PHASE, test_status.TEST_PASS_STATUS
                )
                if test_name == mem_pass_test:
                    self.assert_test_status(
                        test_name,
                        ts,
                        test_status.MEMLEAK_PHASE,
                        test_status.TEST_PASS_STATUS,
                    )

    def test_force_rebuild(self):
        tests = get_tests.get_full_test_names(
            [
                "TESTBUILDFAIL_P1.f19_g16_rx1.A",
                "TESTRUNFAIL_P1.f19_g16_rx1.A",
                "TESTRUNPASS_P1.f19_g16_rx1.A",
            ],
            self._machine,
            self._compiler,
        )
        test_id = "%s-%s" % (self._baseline_name, utils.get_timestamp())
        ct = test_scheduler.TestScheduler(
            tests,
            test_id=test_id,
            no_batch=self.NO_BATCH,
            test_root=self._testroot,
            output_root=self._testroot,
            compiler=self._compiler,
            mpilib=self.TEST_MPILIB,
            machine_name=self.MACHINE.get_machine_name(),
        )

        log_lvl = logging.getLogger().getEffectiveLevel()
        logging.disable(logging.CRITICAL)
        try:
            ct.run_tests()
        finally:
            logging.getLogger().setLevel(log_lvl)

        ct = test_scheduler.TestScheduler(
            tests,
            test_id=test_id,
            no_batch=self.NO_BATCH,
            test_root=self._testroot,
            output_root=self._testroot,
            compiler=self._compiler,
            mpilib=self.TEST_MPILIB,
            machine_name=self.MACHINE.get_machine_name(),
            force_rebuild=True,
            use_existing=True,
        )

        test_statuses = glob.glob("%s/*%s/TestStatus" % (self._testroot, test_id))

        for x in test_statuses:
            casedir = os.path.dirname(x)

            ts = test_status.TestStatus(test_dir=casedir)

            self.assertTrue(
                ts.get_status(test_status.SHAREDLIB_BUILD_PHASE)
                == test_status.TEST_PEND_STATUS
            )

    def test_c_use_existing(self):
        tests = get_tests.get_full_test_names(
            [
                "TESTBUILDFAIL_P1.f19_g16_rx1.A",
                "TESTRUNFAIL_P1.f19_g16_rx1.A",
                "TESTRUNPASS_P1.f19_g16_rx1.A",
            ],
            self._machine,
            self._compiler,
        )
        test_id = "%s-%s" % (self._baseline_name, utils.get_timestamp())
        ct = test_scheduler.TestScheduler(
            tests,
            test_id=test_id,
            no_batch=self.NO_BATCH,
            test_root=self._testroot,
            output_root=self._testroot,
            compiler=self._compiler,
            mpilib=self.TEST_MPILIB,
            machine_name=self.MACHINE.get_machine_name(),
        )

        build_fail_test = [item for item in tests if "TESTBUILDFAIL" in item][0]
        run_fail_test = [item for item in tests if "TESTRUNFAIL" in item][0]
        pass_test = [item for item in tests if "TESTRUNPASS" in item][0]

        log_lvl = logging.getLogger().getEffectiveLevel()
        logging.disable(logging.CRITICAL)
        try:
            ct.run_tests()
        finally:
            logging.getLogger().setLevel(log_lvl)

        test_statuses = glob.glob("%s/*%s/TestStatus" % (self._testroot, test_id))
        self.assertEqual(len(tests), len(test_statuses))

        self._wait_for_tests(test_id, expect_works=False)

        for x in test_statuses:
            casedir = os.path.dirname(x)
            ts = test_status.TestStatus(test_dir=casedir)
            test_name = ts.get_name()
            if test_name == build_fail_test:
                self.assert_test_status(
                    test_name,
                    ts,
                    test_status.MODEL_BUILD_PHASE,
                    test_status.TEST_FAIL_STATUS,
                )
                with test_status.TestStatus(test_dir=casedir) as ts:
                    ts.set_status(
                        test_status.MODEL_BUILD_PHASE, test_status.TEST_PEND_STATUS
                    )
            elif test_name == run_fail_test:
                self.assert_test_status(
                    test_name, ts, test_status.RUN_PHASE, test_status.TEST_FAIL_STATUS
                )
                with test_status.TestStatus(test_dir=casedir) as ts:
                    ts.set_status(
                        test_status.SUBMIT_PHASE, test_status.TEST_PEND_STATUS
                    )
            else:
                self.assertTrue(test_name == pass_test)
                self.assert_test_status(
                    test_name,
                    ts,
                    test_status.MODEL_BUILD_PHASE,
                    test_status.TEST_PASS_STATUS,
                )
                self.assert_test_status(
                    test_name,
                    ts,
                    test_status.SUBMIT_PHASE,
                    test_status.TEST_PASS_STATUS,
                )
                self.assert_test_status(
                    test_name, ts, test_status.RUN_PHASE, test_status.TEST_PASS_STATUS
                )

        os.environ["TESTBUILDFAIL_PASS"] = "True"
        os.environ["TESTRUNFAIL_PASS"] = "True"
        ct2 = test_scheduler.TestScheduler(
            tests,
            test_id=test_id,
            no_batch=self.NO_BATCH,
            use_existing=True,
            test_root=self._testroot,
            output_root=self._testroot,
            compiler=self._compiler,
            mpilib=self.TEST_MPILIB,
            machine_name=self.MACHINE.get_machine_name(),
        )

        log_lvl = logging.getLogger().getEffectiveLevel()
        logging.disable(logging.CRITICAL)
        try:
            ct2.run_tests()
        finally:
            logging.getLogger().setLevel(log_lvl)

        self._wait_for_tests(test_id)

        for x in test_statuses:
            ts = test_status.TestStatus(test_dir=os.path.dirname(x))
            test_name = ts.get_name()
            self.assert_test_status(
                test_name,
                ts,
                test_status.MODEL_BUILD_PHASE,
                test_status.TEST_PASS_STATUS,
            )
            self.assert_test_status(
                test_name, ts, test_status.SUBMIT_PHASE, test_status.TEST_PASS_STATUS
            )
            self.assert_test_status(
                test_name, ts, test_status.RUN_PHASE, test_status.TEST_PASS_STATUS
            )

        del os.environ["TESTBUILDFAIL_PASS"]
        del os.environ["TESTRUNFAIL_PASS"]

        # test that passed tests are not re-run

        ct2 = test_scheduler.TestScheduler(
            tests,
            test_id=test_id,
            no_batch=self.NO_BATCH,
            use_existing=True,
            test_root=self._testroot,
            output_root=self._testroot,
            compiler=self._compiler,
            mpilib=self.TEST_MPILIB,
            machine_name=self.MACHINE.get_machine_name(),
        )

        log_lvl = logging.getLogger().getEffectiveLevel()
        logging.disable(logging.CRITICAL)
        try:
            ct2.run_tests()
        finally:
            logging.getLogger().setLevel(log_lvl)

        self._wait_for_tests(test_id)

        for x in test_statuses:
            ts = test_status.TestStatus(test_dir=os.path.dirname(x))
            test_name = ts.get_name()
            self.assert_test_status(
                test_name,
                ts,
                test_status.MODEL_BUILD_PHASE,
                test_status.TEST_PASS_STATUS,
            )
            self.assert_test_status(
                test_name, ts, test_status.SUBMIT_PHASE, test_status.TEST_PASS_STATUS
            )
            self.assert_test_status(
                test_name, ts, test_status.RUN_PHASE, test_status.TEST_PASS_STATUS
            )

    def test_d_retry(self):
        args = [
            "TESTBUILDFAIL_P1.f19_g16_rx1.A",
            "TESTRUNFAILRESET_P1.f19_g16_rx1.A",
            "TESTRUNPASS_P1.f19_g16_rx1.A",
            "--retry=1",
        ]

        self._create_test(args)

    def test_e_test_inferred_compiler(self):
        if self._config.test_mode != "e3sm" or self._machine != "docker":
            self.skipTest("Skipping create_test test. Depends on E3SM settings")

        args = ["SMS.f19_g16_rx1.A.docker_gnuX", "--no-setup"]

        case = self._create_test(args, default_baseline_area=True)
        result = self.run_cmd_assert_result(
            "./xmlquery --value BASELINE_ROOT", from_dir=case
        )
        self.assertEqual(os.path.split(result)[1], "gnuX")


if __name__ == "__main__":
    unittest.main()
