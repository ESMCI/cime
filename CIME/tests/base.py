#!/usr/bin/env python3

import glob
import os
import tempfile
import time
import signal
import shutil
import stat
import sys
import unittest

from CIME import utils
from CIME.config import Config
from CIME.XML.machines import Machines


def typed_os_environ(key, default_value, expected_type=None):
    # Infer type if not explicitly set
    dst_type = expected_type or type(default_value)

    value = os.environ.get(key, default_value)

    if value is not None and dst_type == bool:
        # Any else is false, might want to be more strict
        return value.lower() == "true" if isinstance(value, str) else value

    if value is None:
        return None

    return dst_type(value)


class BaseTestCase(unittest.TestCase):
    # These static values are set when scripts/lib/CIME/tests/scripts_regression_tests.py is called.
    MACHINE = None
    SCRIPT_DIR = utils.get_scripts_root()
    TOOLS_DIR = os.path.join(utils.get_cime_root(), "CIME", "Tools")
    TEST_ROOT = None
    TEST_COMPILER = None
    TEST_MPILIB = None
    NO_FORTRAN_RUN = None
    FAST_ONLY = None
    NO_BATCH = None
    NO_CMAKE = None
    NO_TEARDOWN = None
    GLOBAL_TIMEOUT = None

    def setUp(self):
        self._thread_error = None
        self._unset_proxy = self.setup_proxy()
        self._machine = self.MACHINE.get_machine_name()
        self._compiler = (
            self.MACHINE.get_default_compiler()
            if self.TEST_COMPILER is None
            else self.TEST_COMPILER
        )
        self._baseline_name = "fake_testing_only_%s" % utils.get_timestamp()
        self._baseline_area = os.path.join(self.TEST_ROOT, "baselines")
        self._testroot = self.TEST_ROOT
        self._hasbatch = self.MACHINE.has_batch_system() and not self.NO_BATCH
        self._do_teardown = not self.NO_TEARDOWN
        self._root_dir = os.getcwd()

        customize_path = os.path.join(utils.get_src_root(), "cime_config", "customize")
        self._config = Config.load(customize_path)

    def tearDown(self):
        self.kill_subprocesses()

        os.chdir(self._root_dir)

        if self._unset_proxy:
            del os.environ["http_proxy"]

        files_to_clean = []

        baselines = os.path.join(self._baseline_area, self._baseline_name)
        if os.path.isdir(baselines):
            files_to_clean.append(baselines)

        for test_id in ["master", self._baseline_name]:
            for leftover in glob.glob(os.path.join(self._testroot, "*%s*" % test_id)):
                files_to_clean.append(leftover)

        do_teardown = self._do_teardown and sys.exc_info() == (None, None, None)
        if not do_teardown and files_to_clean:
            print("Detected failed test or user request no teardown")
            print("Leaving files:")
            for file_to_clean in files_to_clean:
                print(" " + file_to_clean)
        else:
            # For batch machines need to avoid race condition as batch system
            # finishes I/O for the case.
            if self._hasbatch:
                time.sleep(5)

            for file_to_clean in files_to_clean:
                if os.path.isdir(file_to_clean):
                    shutil.rmtree(file_to_clean)
                else:
                    os.remove(file_to_clean)

    def assert_test_status(self, test_name, test_status_obj, test_phase, expected_stat):
        test_status = test_status_obj.get_status(test_phase)
        self.assertEqual(
            test_status,
            expected_stat,
            msg="Problem with {}: for phase '{}': has status '{}', expected '{}'".format(
                test_name, test_phase, test_status, expected_stat
            ),
        )

    def run_cmd_assert_result(
        self, cmd, from_dir=None, expected_stat=0, env=None, verbose=False, shell=True
    ):
        from_dir = os.getcwd() if from_dir is None else from_dir
        stat, output, errput = utils.run_cmd(
            cmd, from_dir=from_dir, env=env, verbose=verbose, shell=shell
        )
        if expected_stat == 0:
            expectation = "SHOULD HAVE WORKED, INSTEAD GOT STAT %s" % stat
        else:
            expectation = "EXPECTED STAT %s, INSTEAD GOT STAT %s" % (
                expected_stat,
                stat,
            )
        msg = """
    COMMAND: %s
    FROM_DIR: %s
    %s
    OUTPUT: %s
    ERRPUT: %s
    """ % (
            cmd,
            from_dir,
            expectation,
            output,
            errput,
        )
        self.assertEqual(stat, expected_stat, msg=msg)

        return output

    def setup_proxy(self):
        if "http_proxy" not in os.environ:
            proxy = self.MACHINE.get_value("PROXY")
            if proxy is not None:
                os.environ["http_proxy"] = proxy
                return True

        return False

    def assert_dashboard_has_build(self, build_name, expected_count=1):
        # Do not test E3SM dashboard if model is CESM
        if self._config.test_mode == "e3sm":
            time.sleep(10)  # Give chance for cdash to update

            wget_file = tempfile.mktemp()

            utils.run_cmd_no_fail(
                "wget https://my.cdash.org/api/v1/index.php?project=ACME_test --no-check-certificate -O %s"
                % wget_file
            )

            raw_text = open(wget_file, "r").read()
            os.remove(wget_file)

            num_found = raw_text.count(build_name)
            self.assertEqual(
                num_found,
                expected_count,
                msg="Dashboard did not have expected num occurances of build name '%s'. Expected %s, found %s"
                % (build_name, expected_count, num_found),
            )

    def kill_subprocesses(
        self, name=None, sig=signal.SIGKILL, expected_num_killed=None
    ):
        # Kill all subprocesses
        proc_ids = utils.find_proc_id(proc_name=name, children_only=True)
        if expected_num_killed is not None:
            self.assertEqual(
                len(proc_ids),
                expected_num_killed,
                msg="Expected to find %d processes to kill, found %d"
                % (expected_num_killed, len(proc_ids)),
            )
        for proc_id in proc_ids:
            try:
                os.kill(proc_id, sig)
            except OSError:
                pass

    def kill_python_subprocesses(self, sig=signal.SIGKILL, expected_num_killed=None):
        self.kill_subprocesses("[Pp]ython", sig, expected_num_killed)

    def _create_test(
        self,
        extra_args,
        test_id=None,
        run_errors=False,
        env_changes="",
        default_baseline_area=False,
    ):
        """
        Convenience wrapper around create_test. Returns list of full paths to created cases. If multiple cases,
        the order of the returned list is not guaranteed to match the order of the arguments.
        """
        # All stub model not supported in nuopc driver
        driver = utils.get_cime_default_driver()
        if driver == "nuopc" and "cime_developer" in extra_args:
            extra_args.append(
                " ^SMS_Ln3.T42_T42.S ^PRE.f19_f19.ADESP_TEST ^PRE.f19_f19.ADESP ^DAE.ww3a.ADWAV"
            )

        test_id = (
            "{}-{}".format(self._baseline_name, utils.get_timestamp())
            if test_id is None
            else test_id
        )
        extra_args.append("-t {}".format(test_id))
        if not default_baseline_area:
            extra_args.append("--baseline-root {}".format(self._baseline_area))
        if self.NO_BATCH:
            extra_args.append("--no-batch")
        if self.TEST_COMPILER and (
            [extra_arg for extra_arg in extra_args if "--compiler" in extra_arg] == []
        ):
            extra_args.append("--compiler={}".format(self.TEST_COMPILER))
        if self.TEST_MPILIB and (
            [extra_arg for extra_arg in extra_args if "--mpilib" in extra_arg] == []
        ):
            extra_args.append("--mpilib={}".format(self.TEST_MPILIB))
        if [extra_arg for extra_arg in extra_args if "--machine" in extra_arg] == []:
            extra_args.append(f"--machine {self.MACHINE.get_machine_name()}")
        extra_args.append("--test-root={0} --output-root={0}".format(self._testroot))

        full_run = (
            set(extra_args)
            & set(["-n", "--namelist-only", "--no-setup", "--no-build", "--no-run"])
        ) == set()
        if full_run and not self.NO_BATCH:
            extra_args.append("--wait")

        expected_stat = 0 if not run_errors else utils.TESTS_FAILED_ERR_CODE

        output = self.run_cmd_assert_result(
            "{} {}/create_test {}".format(
                env_changes, self.SCRIPT_DIR, " ".join(extra_args)
            ),
            expected_stat=expected_stat,
        )
        cases = []
        for line in output.splitlines():
            if "Case dir:" in line:
                casedir = line.split()[-1]
                self.assertTrue(
                    os.path.isdir(casedir), msg="Missing casedir {}".format(casedir)
                )
                cases.append(casedir)

        self.assertTrue(len(cases) > 0, "create_test made no cases")

        return cases[0] if len(cases) == 1 else cases

    def _wait_for_tests(self, test_id, expect_works=True, always_wait=False):
        if self._hasbatch or always_wait:
            timeout_arg = (
                "--timeout={}".format(self.GLOBAL_TIMEOUT)
                if self.GLOBAL_TIMEOUT is not None
                else ""
            )
            expected_stat = 0 if expect_works else utils.TESTS_FAILED_ERR_CODE
            self.run_cmd_assert_result(
                "{}/wait_for_tests {} *{}/TestStatus".format(
                    self.TOOLS_DIR, timeout_arg, test_id
                ),
                from_dir=self._testroot,
                expected_stat=expected_stat,
            )

    def get_casedir(self, case_fragment, all_cases):
        potential_matches = [item for item in all_cases if case_fragment in item]
        self.assertTrue(
            len(potential_matches) == 1,
            "Ambiguous casedir selection for {}, found  {}  among  {}".format(
                case_fragment, potential_matches, all_cases
            ),
        )
        return potential_matches[0]

    def verify_perms(self, root_dir):
        for root, dirs, files in os.walk(root_dir):
            for filename in files:
                full_path = os.path.join(root, filename)
                st = os.stat(full_path)
                self.assertTrue(
                    st.st_mode & stat.S_IWGRP,
                    msg="file {} is not group writeable".format(full_path),
                )
                self.assertTrue(
                    st.st_mode & stat.S_IRGRP,
                    msg="file {} is not group readable".format(full_path),
                )
                self.assertTrue(
                    st.st_mode & stat.S_IROTH,
                    msg="file {} is not world readable".format(full_path),
                )

            for dirname in dirs:
                full_path = os.path.join(root, dirname)
                st = os.stat(full_path)

                self.assertTrue(
                    st.st_mode & stat.S_IWGRP,
                    msg="dir {} is not group writable".format(full_path),
                )
                self.assertTrue(
                    st.st_mode & stat.S_IRGRP,
                    msg="dir {} is not group readable".format(full_path),
                )
                self.assertTrue(
                    st.st_mode & stat.S_IXGRP,
                    msg="dir {} is not group executable".format(full_path),
                )
                self.assertTrue(
                    st.st_mode & stat.S_IROTH,
                    msg="dir {} is not world readable".format(full_path),
                )
                self.assertTrue(
                    st.st_mode & stat.S_IXOTH,
                    msg="dir {} is not world executable".format(full_path),
                )
