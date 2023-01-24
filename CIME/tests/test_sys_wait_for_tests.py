#!/usr/bin/env python3

import os
import signal
import shutil
import sys
import time
import threading

from CIME import utils
from CIME import test_status
from CIME.tests import base
from CIME.tests import utils as test_utils


class TestWaitForTests(base.BaseTestCase):
    def setUp(self):
        super().setUp()

        self._testroot = os.path.join(self.TEST_ROOT, "TestWaitForTests")
        self._timestamp = utils.get_timestamp()

        # basic tests
        self._testdir_all_pass = os.path.join(
            self._testroot, "scripts_regression_tests.testdir_all_pass"
        )
        self._testdir_with_fail = os.path.join(
            self._testroot, "scripts_regression_tests.testdir_with_fail"
        )
        self._testdir_unfinished = os.path.join(
            self._testroot, "scripts_regression_tests.testdir_unfinished"
        )
        self._testdir_unfinished2 = os.path.join(
            self._testroot, "scripts_regression_tests.testdir_unfinished2"
        )

        # live tests
        self._testdir_teststatus1 = os.path.join(
            self._testroot, "scripts_regression_tests.testdir_teststatus1"
        )
        self._testdir_teststatus2 = os.path.join(
            self._testroot, "scripts_regression_tests.testdir_teststatus2"
        )

        self._testdirs = [
            self._testdir_all_pass,
            self._testdir_with_fail,
            self._testdir_unfinished,
            self._testdir_unfinished2,
            self._testdir_teststatus1,
            self._testdir_teststatus2,
        ]
        basic_tests = self._testdirs[: self._testdirs.index(self._testdir_teststatus1)]

        for testdir in self._testdirs:
            if os.path.exists(testdir):
                shutil.rmtree(testdir)
            os.makedirs(testdir)

        for r in range(10):
            for testdir in basic_tests:
                os.makedirs(os.path.join(testdir, str(r)))
                test_utils.make_fake_teststatus(
                    os.path.join(testdir, str(r)),
                    "Test_%d" % r,
                    test_status.TEST_PASS_STATUS,
                    test_status.RUN_PHASE,
                )

        test_utils.make_fake_teststatus(
            os.path.join(self._testdir_with_fail, "5"),
            "Test_5",
            test_status.TEST_FAIL_STATUS,
            test_status.RUN_PHASE,
        )
        test_utils.make_fake_teststatus(
            os.path.join(self._testdir_unfinished, "5"),
            "Test_5",
            test_status.TEST_PEND_STATUS,
            test_status.RUN_PHASE,
        )
        test_utils.make_fake_teststatus(
            os.path.join(self._testdir_unfinished2, "5"),
            "Test_5",
            test_status.TEST_PASS_STATUS,
            test_status.SUBMIT_PHASE,
        )

        integration_tests = self._testdirs[len(basic_tests) :]
        for integration_test in integration_tests:
            os.makedirs(os.path.join(integration_test, "0"))
            test_utils.make_fake_teststatus(
                os.path.join(integration_test, "0"),
                "Test_0",
                test_status.TEST_PASS_STATUS,
                test_status.CORE_PHASES[0],
            )

        # Set up proxy if possible
        self._unset_proxy = self.setup_proxy()

        self._thread_error = None

    def tearDown(self):
        super().tearDown()

        do_teardown = sys.exc_info() == (None, None, None) and not self.NO_TEARDOWN

        if do_teardown:
            for testdir in self._testdirs:
                shutil.rmtree(testdir)

    def simple_test(self, testdir, expected_results, extra_args="", build_name=None):
        # Need these flags to test dashboard if e3sm
        if self._config.create_test_flag_mode == "e3sm" and build_name is not None:
            extra_args += " -b %s" % build_name

        expected_stat = 0
        for expected_result in expected_results:
            if not (
                expected_result == "PASS"
                or (expected_result == "PEND" and "-n" in extra_args)
            ):
                expected_stat = utils.TESTS_FAILED_ERR_CODE

        output = self.run_cmd_assert_result(
            "%s/wait_for_tests -p ACME_test */TestStatus %s"
            % (self.TOOLS_DIR, extra_args),
            from_dir=testdir,
            expected_stat=expected_stat,
        )

        lines = [
            line
            for line in output.splitlines()
            if (
                line.startswith("PASS")
                or line.startswith("FAIL")
                or line.startswith("PEND")
            )
        ]
        self.assertEqual(len(lines), len(expected_results))
        for idx, line in enumerate(lines):
            testname, status = test_utils.parse_test_status(line)
            self.assertEqual(status, expected_results[idx])
            self.assertEqual(testname, "Test_%d" % idx)

    def threaded_test(self, testdir, expected_results, extra_args="", build_name=None):
        try:
            self.simple_test(testdir, expected_results, extra_args, build_name)
        except AssertionError as e:
            self._thread_error = str(e)

    def test_wait_for_test_all_pass(self):
        self.simple_test(self._testdir_all_pass, ["PASS"] * 10)

    def test_wait_for_test_with_fail(self):
        expected_results = ["FAIL" if item == 5 else "PASS" for item in range(10)]
        self.simple_test(self._testdir_with_fail, expected_results)

    def test_wait_for_test_no_wait(self):
        expected_results = ["PEND" if item == 5 else "PASS" for item in range(10)]
        self.simple_test(self._testdir_unfinished, expected_results, "-n")

    def test_wait_for_test_timeout(self):
        expected_results = ["PEND" if item == 5 else "PASS" for item in range(10)]
        self.simple_test(self._testdir_unfinished, expected_results, "--timeout=3")

    def test_wait_for_test_wait_for_pend(self):
        run_thread = threading.Thread(
            target=self.threaded_test, args=(self._testdir_unfinished, ["PASS"] * 10)
        )
        run_thread.daemon = True
        run_thread.start()

        time.sleep(5)  # Kinda hacky

        self.assertTrue(run_thread.is_alive(), msg="wait_for_tests should have waited")

        with test_status.TestStatus(
            test_dir=os.path.join(self._testdir_unfinished, "5")
        ) as ts:
            ts.set_status(test_status.RUN_PHASE, test_status.TEST_PASS_STATUS)

        run_thread.join(timeout=10)

        self.assertFalse(
            run_thread.is_alive(), msg="wait_for_tests should have finished"
        )

        self.assertTrue(
            self._thread_error is None,
            msg="Thread had failure: %s" % self._thread_error,
        )

    def test_wait_for_test_wait_for_missing_run_phase(self):
        run_thread = threading.Thread(
            target=self.threaded_test, args=(self._testdir_unfinished2, ["PASS"] * 10)
        )
        run_thread.daemon = True
        run_thread.start()

        time.sleep(5)  # Kinda hacky

        self.assertTrue(run_thread.is_alive(), msg="wait_for_tests should have waited")

        with test_status.TestStatus(
            test_dir=os.path.join(self._testdir_unfinished2, "5")
        ) as ts:
            ts.set_status(test_status.RUN_PHASE, test_status.TEST_PASS_STATUS)

        run_thread.join(timeout=10)

        self.assertFalse(
            run_thread.is_alive(), msg="wait_for_tests should have finished"
        )

        self.assertTrue(
            self._thread_error is None,
            msg="Thread had failure: %s" % self._thread_error,
        )

    def test_wait_for_test_wait_kill(self):
        expected_results = ["PEND" if item == 5 else "PASS" for item in range(10)]
        run_thread = threading.Thread(
            target=self.threaded_test, args=(self._testdir_unfinished, expected_results)
        )
        run_thread.daemon = True
        run_thread.start()

        time.sleep(5)

        self.assertTrue(run_thread.is_alive(), msg="wait_for_tests should have waited")

        self.kill_python_subprocesses(signal.SIGTERM, expected_num_killed=1)

        run_thread.join(timeout=10)

        self.assertFalse(
            run_thread.is_alive(), msg="wait_for_tests should have finished"
        )

        self.assertTrue(
            self._thread_error is None,
            msg="Thread had failure: %s" % self._thread_error,
        )

    def test_wait_for_test_cdash_pass(self):
        expected_results = ["PASS"] * 10
        build_name = "regression_test_pass_" + self._timestamp
        run_thread = threading.Thread(
            target=self.threaded_test,
            args=(self._testdir_all_pass, expected_results, "", build_name),
        )
        run_thread.daemon = True
        run_thread.start()

        run_thread.join(timeout=10)

        self.assertFalse(
            run_thread.is_alive(), msg="wait_for_tests should have finished"
        )

        self.assertTrue(
            self._thread_error is None,
            msg="Thread had failure: %s" % self._thread_error,
        )

        self.assert_dashboard_has_build(build_name)

    def test_wait_for_test_cdash_kill(self):
        expected_results = ["PEND" if item == 5 else "PASS" for item in range(10)]
        build_name = "regression_test_kill_" + self._timestamp
        run_thread = threading.Thread(
            target=self.threaded_test,
            args=(self._testdir_unfinished, expected_results, "", build_name),
        )
        run_thread.daemon = True
        run_thread.start()

        time.sleep(5)

        self.assertTrue(run_thread.is_alive(), msg="wait_for_tests should have waited")

        self.kill_python_subprocesses(signal.SIGTERM, expected_num_killed=1)

        run_thread.join(timeout=10)

        self.assertFalse(
            run_thread.is_alive(), msg="wait_for_tests should have finished"
        )
        self.assertTrue(
            self._thread_error is None,
            msg="Thread had failure: %s" % self._thread_error,
        )

        self.assert_dashboard_has_build(build_name)

        if self._config.test_mode == "e3sm":
            cdash_result_dir = os.path.join(self._testdir_unfinished, "Testing")
            tag_file = os.path.join(cdash_result_dir, "TAG")
            self.assertTrue(os.path.isdir(cdash_result_dir))
            self.assertTrue(os.path.isfile(tag_file))

            tag = open(tag_file, "r").readlines()[0].strip()
            xml_file = os.path.join(cdash_result_dir, tag, "Test.xml")
            self.assertTrue(os.path.isfile(xml_file))

            xml_contents = open(xml_file, "r").read()
            self.assertTrue(
                r"<TestList><Test>Test_0</Test><Test>Test_1</Test><Test>Test_2</Test><Test>Test_3</Test><Test>Test_4</Test><Test>Test_5</Test><Test>Test_6</Test><Test>Test_7</Test><Test>Test_8</Test><Test>Test_9</Test></TestList>"
                in xml_contents
            )
            self.assertTrue(
                r'<Test Status="notrun"><Name>Test_5</Name>' in xml_contents
            )

            # TODO: Any further checking of xml output worth doing?

    def live_test_impl(self, testdir, expected_results, last_phase, last_status):
        run_thread = threading.Thread(
            target=self.threaded_test, args=(testdir, expected_results)
        )
        run_thread.daemon = True
        run_thread.start()

        time.sleep(5)

        self.assertTrue(run_thread.is_alive(), msg="wait_for_tests should have waited")

        for core_phase in test_status.CORE_PHASES[1:]:
            with test_status.TestStatus(
                test_dir=os.path.join(self._testdir_teststatus1, "0")
            ) as ts:
                ts.set_status(
                    core_phase,
                    last_status
                    if core_phase == last_phase
                    else test_status.TEST_PASS_STATUS,
                )

            time.sleep(5)

            if core_phase != last_phase:
                self.assertTrue(
                    run_thread.is_alive(),
                    msg="wait_for_tests should have waited after passing phase {}".format(
                        core_phase
                    ),
                )
            else:
                run_thread.join(timeout=10)
                self.assertFalse(
                    run_thread.is_alive(),
                    msg="wait_for_tests should have finished after phase {}".format(
                        core_phase
                    ),
                )
                break

        self.assertTrue(
            self._thread_error is None,
            msg="Thread had failure: %s" % self._thread_error,
        )

    def test_wait_for_test_test_status_integration_pass(self):
        self.live_test_impl(
            self._testdir_teststatus1,
            ["PASS"],
            test_status.RUN_PHASE,
            test_status.TEST_PASS_STATUS,
        )

    def test_wait_for_test_test_status_integration_submit_fail(self):
        self.live_test_impl(
            self._testdir_teststatus1,
            ["FAIL"],
            test_status.SUBMIT_PHASE,
            test_status.TEST_FAIL_STATUS,
        )
