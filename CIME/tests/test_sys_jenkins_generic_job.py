#!/usr/bin/env python3

import glob
import os
import signal
import stat
import threading
import time

from CIME import get_tests
from CIME import utils
from CIME.tests import base


class TestJenkinsGenericJob(base.BaseTestCase):
    def setUp(self):
        super().setUp()

        if self._config.test_mode == "cesm":
            self.skipTest("Skipping Jenkins tests. E3SM feature")

        # Need to run in a subdir in order to not have CTest clash. Name it
        # such that it should be cleaned up by the parent tearDown
        self._testdir = os.path.join(
            self._testroot, "jenkins_test_%s" % self._baseline_name
        )
        os.makedirs(self._testdir)

        # Change root to avoid clashing with other jenkins_generic_jobs
        self._jenkins_root = os.path.join(self._testdir, "J")

    def tearDown(self):
        super().tearDown()

        if "TESTRUNDIFF_ALTERNATE" in os.environ:
            del os.environ["TESTRUNDIFF_ALTERNATE"]

    def simple_test(self, expect_works, extra_args, build_name=None):
        if self.NO_BATCH:
            extra_args += " --no-batch"

        # Need these flags to test dashboard if e3sm
        if self._config.test_mode == "e3sm" and build_name is not None:
            extra_args += (
                " -p ACME_test --submit-to-cdash --cdash-build-group=Nightly -c %s"
                % build_name
            )

        self.run_cmd_assert_result(
            "%s/jenkins_generic_job -r %s %s -B %s"
            % (self.TOOLS_DIR, self._testdir, extra_args, self._baseline_area),
            from_dir=self._testdir,
            expected_stat=(0 if expect_works else utils.TESTS_FAILED_ERR_CODE),
            shell=False,
        )

    def threaded_test(self, expect_works, extra_args, build_name=None):
        try:
            self.simple_test(expect_works, extra_args, build_name)
        except AssertionError as e:
            self._thread_error = str(e)

    def assert_num_leftovers(self, suite):
        num_tests_in_suite = len(get_tests.get_test_suite(suite))

        case_glob = "%s/*%s*/" % (self._jenkins_root, self._baseline_name.capitalize())
        jenkins_dirs = glob.glob(case_glob)  # Case dirs
        # scratch_dirs = glob.glob("%s/*%s*/" % (self._testroot, test_id)) # blr/run dirs

        self.assertEqual(
            num_tests_in_suite,
            len(jenkins_dirs),
            msg="Wrong number of leftover directories in %s, expected %d, see %s. Glob checked %s"
            % (self._jenkins_root, num_tests_in_suite, jenkins_dirs, case_glob),
        )

        # JGF: Can't test this at the moment due to root change flag given to jenkins_generic_job
        # self.assertEqual(num_tests_in_tiny + 1, len(scratch_dirs),
        #                  msg="Wrong number of leftover directories in %s, expected %d, see %s" % \
        #                      (self._testroot, num_tests_in_tiny, scratch_dirs))

    def test_jenkins_generic_job(self):
        # Generate fresh baselines so that this test is not impacted by
        # unresolved diffs
        self.simple_test(True, "-t cime_test_only_pass -g -b %s" % self._baseline_name)
        self.assert_num_leftovers("cime_test_only_pass")

        build_name = "jenkins_generic_job_pass_%s" % utils.get_timestamp()
        self.simple_test(
            True,
            "-t cime_test_only_pass -b %s" % self._baseline_name,
            build_name=build_name,
        )
        self.assert_num_leftovers(
            "cime_test_only_pass"
        )  # jenkins_generic_job should have automatically cleaned up leftovers from prior run
        self.assert_dashboard_has_build(build_name)

    def test_jenkins_generic_job_save_timing(self):
        self.simple_test(
            True, "-t cime_test_timing --save-timing -b %s" % self._baseline_name
        )
        self.assert_num_leftovers("cime_test_timing")

        jenkins_dirs = glob.glob(
            "%s/*%s*/" % (self._jenkins_root, self._baseline_name.capitalize())
        )  # case dirs
        case = jenkins_dirs[0]
        result = self.run_cmd_assert_result(
            "./xmlquery --value SAVE_TIMING", from_dir=case
        )
        self.assertEqual(result, "TRUE")

    def test_jenkins_generic_job_kill(self):
        build_name = "jenkins_generic_job_kill_%s" % utils.get_timestamp()
        run_thread = threading.Thread(
            target=self.threaded_test,
            args=(False, " -t cime_test_only_slow_pass -b master", build_name),
        )
        run_thread.daemon = True
        run_thread.start()

        time.sleep(120)

        self.kill_subprocesses(sig=signal.SIGTERM)

        run_thread.join(timeout=30)

        self.assertFalse(
            run_thread.is_alive(), msg="jenkins_generic_job should have finished"
        )
        self.assertTrue(
            self._thread_error is None,
            msg="Thread had failure: %s" % self._thread_error,
        )
        self.assert_dashboard_has_build(build_name)

    def test_jenkins_generic_job_realistic_dash(self):
        # The actual quality of the cdash results for this test can only
        # be inspected manually

        # Generate fresh baselines so that this test is not impacted by
        # unresolved diffs
        self.simple_test(False, "-t cime_test_all -g -b %s" % self._baseline_name)
        self.assert_num_leftovers("cime_test_all")

        # Should create a diff
        os.environ["TESTRUNDIFF_ALTERNATE"] = "True"

        # Should create a nml diff
        # Modify namelist
        fake_nl = """
 &fake_nml
   fake_item = 'fake'
   fake = .true.
/"""
        baseline_glob = glob.glob(
            os.path.join(self._baseline_area, self._baseline_name, "TESTRUNPASS*")
        )
        self.assertEqual(
            len(baseline_glob),
            1,
            msg="Expected one match, got:\n%s" % "\n".join(baseline_glob),
        )

        for baseline_dir in baseline_glob:
            nl_path = os.path.join(baseline_dir, "CaseDocs", "datm_in")
            self.assertTrue(os.path.isfile(nl_path), msg="Missing file %s" % nl_path)

            os.chmod(nl_path, stat.S_IRUSR | stat.S_IWUSR)
            with open(nl_path, "a") as nl_file:
                nl_file.write(fake_nl)

        build_name = "jenkins_generic_job_mixed_%s" % utils.get_timestamp()
        self.simple_test(
            False, "-t cime_test_all -b %s" % self._baseline_name, build_name=build_name
        )
        self.assert_num_leftovers(
            "cime_test_all"
        )  # jenkins_generic_job should have automatically cleaned up leftovers from prior run
        self.assert_dashboard_has_build(build_name)
