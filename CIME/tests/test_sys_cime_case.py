#!/usr/bin/env python3

import collections
import os
import re
import shutil
import sys
import time

from CIME import utils
from CIME.tests import base
from CIME.case.case import Case
from CIME.XML.env_run import EnvRun


class TestCimeCase(base.BaseTestCase):
    def test_cime_case(self):
        casedir = self._create_test(
            ["--no-build", "TESTRUNPASS_P1.f19_g16_rx1.A"], test_id=self._baseline_name
        )

        self.assertEqual(type(self.MACHINE.get_value("MAX_TASKS_PER_NODE")), int)
        self.assertTrue(
            type(self.MACHINE.get_value("PROJECT_REQUIRED")) in [type(None), bool]
        )

        with Case(casedir, read_only=False) as case:
            build_complete = case.get_value("BUILD_COMPLETE")
            self.assertFalse(
                build_complete,
                msg="Build complete had wrong value '%s'" % build_complete,
            )

            case.set_value("BUILD_COMPLETE", True)
            build_complete = case.get_value("BUILD_COMPLETE")
            self.assertTrue(
                build_complete,
                msg="Build complete had wrong value '%s'" % build_complete,
            )

            case.flush()

            build_complete = utils.run_cmd_no_fail(
                "./xmlquery BUILD_COMPLETE --value", from_dir=casedir
            )
            self.assertEqual(
                build_complete,
                "TRUE",
                msg="Build complete had wrong value '%s'" % build_complete,
            )

            # Test some test properties
            self.assertEqual(case.get_value("TESTCASE"), "TESTRUNPASS")

    def _batch_test_fixture(self, testcase_name):
        if not self.MACHINE.has_batch_system() or self.NO_BATCH:
            self.skipTest("Skipping testing user prerequisites without batch systems")
        testdir = os.path.join(self._testroot, testcase_name)
        if os.path.exists(testdir):
            shutil.rmtree(testdir)
        args = "--case {name} --script-root {testdir} --compset X --res f19_g16 --handle-preexisting-dirs=r --output-root {testdir}".format(
            name=testcase_name, testdir=testdir
        )
        if self._config.allow_unsupported:
            args += " --run-unsupported"

        self.run_cmd_assert_result(
            "{}/create_newcase {}".format(self.SCRIPT_DIR, args),
            from_dir=self.SCRIPT_DIR,
        )
        self.run_cmd_assert_result("./case.setup", from_dir=testdir)

        return testdir

    def test_cime_case_prereq(self):
        testcase_name = "prereq_test"
        testdir = self._batch_test_fixture(testcase_name)
        with Case(testdir, read_only=False) as case:
            if case.get_value("depend_string") is None:
                self.skipTest(
                    "Skipping prereq test, depend_string was not provided for this batch system"
                )
            job_name = "case.run"
            prereq_name = "prereq_test"
            batch_commands = case.submit_jobs(
                prereq=prereq_name, job=job_name, skip_pnl=True, dry_run=True
            )
            self.assertTrue(
                isinstance(batch_commands, collections.Sequence),
                "case.submit_jobs did not return a sequence for a dry run",
            )
            self.assertTrue(
                len(batch_commands) > 0,
                "case.submit_jobs did not return any job submission string",
            )
            # The first element in the internal sequence should just be the job name
            # The second one (batch_cmd_index) should be the actual batch submission command
            batch_cmd_index = 1
            # The prerequisite should be applied to all jobs, though we're only expecting one
            for batch_cmd in batch_commands:
                self.assertTrue(
                    isinstance(batch_cmd, collections.Sequence),
                    "case.submit_jobs did not return a sequence of sequences",
                )
                self.assertTrue(
                    len(batch_cmd) > batch_cmd_index,
                    "case.submit_jobs returned internal sequences with length <= {}".format(
                        batch_cmd_index
                    ),
                )
                self.assertTrue(
                    isinstance(batch_cmd[1], str),
                    "case.submit_jobs returned internal sequences without the batch command string as the second parameter: {}".format(
                        batch_cmd[1]
                    ),
                )
                batch_cmd_args = batch_cmd[1]

                jobid_ident = "jobid"
                dep_str_fmt = case.get_env("batch").get_value(
                    "depend_string", subgroup=None
                )
                self.assertTrue(
                    jobid_ident in dep_str_fmt,
                    "dependency string doesn't include the jobid identifier {}".format(
                        jobid_ident
                    ),
                )
                dep_str = dep_str_fmt[: dep_str_fmt.index(jobid_ident)]

                prereq_substr = None
                while dep_str in batch_cmd_args:
                    dep_id_pos = batch_cmd_args.find(dep_str) + len(dep_str)
                    batch_cmd_args = batch_cmd_args[dep_id_pos:]
                    prereq_substr = batch_cmd_args[: len(prereq_name)]
                    if prereq_substr == prereq_name:
                        break

                self.assertTrue(
                    prereq_name in prereq_substr,
                    "Dependencies added, but not the user specified one",
                )

    def test_cime_case_allow_failed_prereq(self):
        testcase_name = "allow_failed_prereq_test"
        testdir = self._batch_test_fixture(testcase_name)
        with Case(testdir, read_only=False) as case:
            depend_allow = case.get_value("depend_allow_string")
            if depend_allow is None:
                self.skipTest(
                    "Skipping allow_failed_prereq test, depend_allow_string was not provided for this batch system"
                )
            job_name = "case.run"
            prereq_name = "prereq_allow_fail_test"
            depend_allow = depend_allow.replace("jobid", prereq_name)
            batch_commands = case.submit_jobs(
                prereq=prereq_name,
                allow_fail=True,
                job=job_name,
                skip_pnl=True,
                dry_run=True,
            )
            self.assertTrue(
                isinstance(batch_commands, collections.Sequence),
                "case.submit_jobs did not return a sequence for a dry run",
            )
            num_submissions = 1
            if case.get_value("DOUT_S"):
                num_submissions = 2
            self.assertTrue(
                len(batch_commands) == num_submissions,
                "case.submit_jobs did not return any job submission strings",
            )
            self.assertTrue(depend_allow in batch_commands[0][1])

    def test_cime_case_resubmit_immediate(self):
        testcase_name = "resubmit_immediate_test"
        testdir = self._batch_test_fixture(testcase_name)
        with Case(testdir, read_only=False) as case:
            depend_string = case.get_value("depend_string")
            if depend_string is None:
                self.skipTest(
                    "Skipping resubmit_immediate test, depend_string was not provided for this batch system"
                )
            depend_string = re.sub("jobid.*$", "", depend_string)
            job_name = "case.run"
            num_submissions = 6
            case.set_value("RESUBMIT", num_submissions - 1)
            batch_commands = case.submit_jobs(
                job=job_name, skip_pnl=True, dry_run=True, resubmit_immediate=True
            )
            self.assertTrue(
                isinstance(batch_commands, collections.Sequence),
                "case.submit_jobs did not return a sequence for a dry run",
            )
            if case.get_value("DOUT_S"):
                num_submissions = 12
            self.assertTrue(
                len(batch_commands) == num_submissions,
                "case.submit_jobs did not return {} submitted jobs".format(
                    num_submissions
                ),
            )
            for i, cmd in enumerate(batch_commands):
                if i > 0:
                    self.assertTrue(depend_string in cmd[1])

    def test_cime_case_st_archive_resubmit(self):
        testcase_name = "st_archive_resubmit_test"
        testdir = self._batch_test_fixture(testcase_name)
        with Case(testdir, read_only=False) as case:
            case.case_setup(clean=False, test_mode=False, reset=True)
            orig_resubmit = 2
            case.set_value("RESUBMIT", orig_resubmit)
            case.case_st_archive(resubmit=False)
            new_resubmit = case.get_value("RESUBMIT")
            self.assertTrue(
                orig_resubmit == new_resubmit, "st_archive resubmitted when told not to"
            )
            case.case_st_archive(resubmit=True)
            new_resubmit = case.get_value("RESUBMIT")
            self.assertTrue(
                (orig_resubmit - 1) == new_resubmit,
                "st_archive did not resubmit when told to",
            )

    def test_cime_case_build_threaded_1(self):
        casedir = self._create_test(
            ["--no-build", "TESTRUNPASS_P1x1.f19_g16_rx1.A"],
            test_id=self._baseline_name,
        )

        with Case(casedir, read_only=False) as case:
            build_threaded = case.get_value("SMP_PRESENT")
            self.assertFalse(build_threaded)

            build_threaded = case.get_build_threaded()
            self.assertFalse(build_threaded)

            case.set_value("FORCE_BUILD_SMP", True)

            build_threaded = case.get_build_threaded()
            self.assertTrue(build_threaded)

    def test_cime_case_build_threaded_2(self):
        casedir = self._create_test(
            ["--no-build", "TESTRUNPASS_P1x2.f19_g16_rx1.A"],
            test_id=self._baseline_name,
        )

        with Case(casedir, read_only=False) as case:
            build_threaded = case.get_value("SMP_PRESENT")
            self.assertTrue(build_threaded)

            build_threaded = case.get_build_threaded()
            self.assertTrue(build_threaded)

    def test_cime_case_mpi_serial(self):
        casedir = self._create_test(
            ["--no-build", "TESTRUNPASS_Mmpi-serial_P10.f19_g16_rx1.A"],
            test_id=self._baseline_name,
        )

        with Case(casedir, read_only=True) as case:

            # Serial cases should not be using pnetcdf
            self.assertEqual(case.get_value("CPL_PIO_TYPENAME"), "netcdf")

            # Serial cases should be using 1 task
            self.assertEqual(case.get_value("TOTALPES"), 1)

            self.assertEqual(case.get_value("NTASKS_CPL"), 1)

    def test_cime_case_force_pecount(self):
        casedir = self._create_test(
            [
                "--no-build",
                "--force-procs=16",
                "--force-threads=8",
                "TESTRUNPASS.f19_g16_rx1.A",
            ],
            test_id=self._baseline_name,
        )

        with Case(casedir, read_only=True) as case:
            self.assertEqual(case.get_value("NTASKS_CPL"), 16)

            self.assertEqual(case.get_value("NTHRDS_CPL"), 8)

    def test_cime_case_xmlchange_append(self):
        casedir = self._create_test(
            ["--no-build", "TESTRUNPASS_P1x1.f19_g16_rx1.A"],
            test_id=self._baseline_name,
        )

        self.run_cmd_assert_result(
            "./xmlchange --id PIO_CONFIG_OPTS --val='-opt1'", from_dir=casedir
        )
        result = self.run_cmd_assert_result(
            "./xmlquery --value PIO_CONFIG_OPTS", from_dir=casedir
        )
        self.assertEqual(result, "-opt1")

        self.run_cmd_assert_result(
            "./xmlchange --id PIO_CONFIG_OPTS --val='-opt2' --append", from_dir=casedir
        )
        result = self.run_cmd_assert_result(
            "./xmlquery --value PIO_CONFIG_OPTS", from_dir=casedir
        )
        self.assertEqual(result, "-opt1 -opt2")

    def test_cime_case_test_walltime_mgmt_1(self):
        if self._config.test_mode == "cesm":
            self.skipTest("Skipping walltime test. Depends on E3SM batch settings")

        test_name = "ERS.f19_g16_rx1.A"
        casedir = self._create_test(
            ["--no-setup", "--machine=blues", "--non-local", test_name],
            test_id=self._baseline_name,
            env_changes="unset CIME_GLOBAL_WALLTIME &&",
        )

        result = self.run_cmd_assert_result(
            "./xmlquery JOB_WALLCLOCK_TIME -N --subgroup=case.test --value",
            from_dir=casedir,
        )
        self.assertEqual(result, "00:10:00")

        result = self.run_cmd_assert_result(
            "./xmlquery JOB_QUEUE -N --subgroup=case.test --value", from_dir=casedir
        )
        self.assertEqual(result, "biggpu")

    def test_cime_case_test_walltime_mgmt_2(self):
        if self._config.test_mode == "cesm":
            self.skipTest("Skipping walltime test. Depends on E3SM batch settings")

        test_name = "ERS_P64.f19_g16_rx1.A"
        casedir = self._create_test(
            ["--no-setup", "--machine=blues", "--non-local", test_name],
            test_id=self._baseline_name,
            env_changes="unset CIME_GLOBAL_WALLTIME &&",
        )

        result = self.run_cmd_assert_result(
            "./xmlquery JOB_WALLCLOCK_TIME -N --subgroup=case.test --value",
            from_dir=casedir,
        )
        self.assertEqual(result, "01:00:00")

        result = self.run_cmd_assert_result(
            "./xmlquery JOB_QUEUE -N --subgroup=case.test --value", from_dir=casedir
        )
        self.assertEqual(result, "biggpu")

    def test_cime_case_test_walltime_mgmt_3(self):
        if self._config.test_mode == "cesm":
            self.skipTest("Skipping walltime test. Depends on E3SM batch settings")

        test_name = "ERS_P64.f19_g16_rx1.A"
        casedir = self._create_test(
            [
                "--no-setup",
                "--machine=blues",
                "--non-local",
                "--walltime=0:10:00",
                test_name,
            ],
            test_id=self._baseline_name,
            env_changes="unset CIME_GLOBAL_WALLTIME &&",
        )

        result = self.run_cmd_assert_result(
            "./xmlquery JOB_WALLCLOCK_TIME -N --subgroup=case.test --value",
            from_dir=casedir,
        )
        self.assertEqual(result, "00:10:00")

        result = self.run_cmd_assert_result(
            "./xmlquery JOB_QUEUE -N --subgroup=case.test --value", from_dir=casedir
        )
        self.assertEqual(result, "biggpu")  # Not smart enough to select faster queue

    def test_cime_case_test_walltime_mgmt_4(self):
        if self._config.test_mode == "cesm":
            self.skipTest("Skipping walltime test. Depends on E3SM batch settings")

        test_name = "ERS_P1.f19_g16_rx1.A"
        casedir = self._create_test(
            [
                "--no-setup",
                "--machine=blues",
                "--non-local",
                "--walltime=2:00:00",
                test_name,
            ],
            test_id=self._baseline_name,
            env_changes="unset CIME_GLOBAL_WALLTIME &&",
        )

        result = self.run_cmd_assert_result(
            "./xmlquery JOB_WALLCLOCK_TIME -N --subgroup=case.test --value",
            from_dir=casedir,
        )
        self.assertEqual(result, "01:00:00")

        result = self.run_cmd_assert_result(
            "./xmlquery JOB_QUEUE -N --subgroup=case.test --value", from_dir=casedir
        )
        self.assertEqual(result, "biggpu")

    def test_cime_case_test_walltime_mgmt_5(self):
        if self._config.test_mode == "cesm":
            self.skipTest("Skipping walltime test. Depends on E3SM batch settings")

        test_name = "ERS_P1.f19_g16_rx1.A"
        casedir = self._create_test(
            ["--no-setup", "--machine=blues", "--non-local", test_name],
            test_id=self._baseline_name,
            env_changes="unset CIME_GLOBAL_WALLTIME &&",
        )

        self.run_cmd_assert_result(
            "./xmlchange JOB_QUEUE=slartibartfast -N --subgroup=case.test",
            from_dir=casedir,
            expected_stat=1,
        )

        self.run_cmd_assert_result(
            "./xmlchange JOB_QUEUE=slartibartfast -N --force --subgroup=case.test",
            from_dir=casedir,
        )

        result = self.run_cmd_assert_result(
            "./xmlquery JOB_WALLCLOCK_TIME -N --subgroup=case.test --value",
            from_dir=casedir,
        )
        self.assertEqual(result, "01:00:00")

        result = self.run_cmd_assert_result(
            "./xmlquery JOB_QUEUE -N --subgroup=case.test --value", from_dir=casedir
        )
        self.assertEqual(result, "slartibartfast")

    def test_cime_case_test_walltime_mgmt_6(self):
        if not self._hasbatch:
            self.skipTest("Skipping walltime test. Depends on batch system")

        test_name = "ERS_P1.f19_g16_rx1.A"
        casedir = self._create_test(
            ["--no-build", test_name],
            test_id=self._baseline_name,
            env_changes="unset CIME_GLOBAL_WALLTIME &&",
        )

        self.run_cmd_assert_result(
            "./xmlchange JOB_WALLCLOCK_TIME=421:32:11 --subgroup=case.test",
            from_dir=casedir,
        )

        self.run_cmd_assert_result("./case.setup --reset", from_dir=casedir)

        result = self.run_cmd_assert_result(
            "./xmlquery JOB_WALLCLOCK_TIME --subgroup=case.test --value",
            from_dir=casedir,
        )
        with Case(casedir) as case:
            walltime_format = case.get_value("walltime_format", subgroup=None)
            if walltime_format is not None and walltime_format.count(":") == 1:
                self.assertEqual(result, "421:32")
            else:
                self.assertEqual(result, "421:32:11")

    def test_cime_case_test_walltime_mgmt_7(self):
        if not self._hasbatch:
            self.skipTest("Skipping walltime test. Depends on batch system")

        test_name = "ERS_P1.f19_g16_rx1.A"
        casedir = self._create_test(
            ["--no-build", "--walltime=01:00:00", test_name],
            test_id=self._baseline_name,
            env_changes="unset CIME_GLOBAL_WALLTIME &&",
        )

        self.run_cmd_assert_result(
            "./xmlchange JOB_WALLCLOCK_TIME=421:32:11 --subgroup=case.test",
            from_dir=casedir,
        )

        self.run_cmd_assert_result("./case.setup --reset", from_dir=casedir)

        result = self.run_cmd_assert_result(
            "./xmlquery JOB_WALLCLOCK_TIME --subgroup=case.test --value",
            from_dir=casedir,
        )
        with Case(casedir) as case:
            walltime_format = case.get_value("walltime_format", subgroup=None)
            if walltime_format is not None and walltime_format.count(":") == 1:
                self.assertEqual(result, "421:32")
            else:
                self.assertEqual(result, "421:32:11")

    def test_cime_case_test_walltime_mgmt_8(self):
        if self._config.test_mode == "cesm":
            self.skipTest("Skipping walltime test. Depends on E3SM batch settings")

        test_name = "SMS_P25600.f19_g16_rx1.A"
        machine, compiler = "theta", "gnu"
        casedir = self._create_test(
            [
                "--no-setup",
                "--non-local",
                "--machine={}".format(machine),
                "--compiler={}".format(compiler),
                "--project e3sm",
                test_name,
            ],
            test_id=self._baseline_name,
            env_changes="unset CIME_GLOBAL_WALLTIME &&",
        )

        result = self.run_cmd_assert_result(
            "./xmlquery JOB_WALLCLOCK_TIME -N --subgroup=case.test --value",
            from_dir=casedir,
        )
        self.assertEqual(result, "09:00:00")

        result = self.run_cmd_assert_result(
            "./xmlquery JOB_QUEUE -N --subgroup=case.test --value", from_dir=casedir
        )
        self.assertEqual(result, "default")

    def test_cime_case_test_custom_project(self):
        test_name = "ERS_P1.f19_g16_rx1.A"
        # have to use a machine both models know and one that doesn't put PROJECT in any key paths
        machine = self._config.test_custom_project_machine
        compiler = "gnu"
        casedir = self._create_test(
            [
                "--no-setup",
                "--machine={}".format(machine),
                "--compiler={}".format(compiler),
                "--project=testproj",
                test_name,
                "--mpilib=mpi-serial",
                "--non-local",
            ],
            test_id=self._baseline_name,
            env_changes="unset CIME_GLOBAL_WALLTIME &&",
        )

        result = self.run_cmd_assert_result(
            "./xmlquery --non-local --value PROJECT --subgroup=case.test",
            from_dir=casedir,
        )
        self.assertEqual(result, "testproj")

    def test_create_test_longname(self):
        self._create_test(
            ["SMS.f19_g16.2000_SATM_XLND_SICE_SOCN_XROF_XGLC_SWAV", "--no-build"]
        )

    def test_env_loading(self):
        if self._machine != "mappy":
            self.skipTest("Skipping env load test - Only works on mappy")

        casedir = self._create_test(
            ["--no-build", "TESTRUNPASS.f19_g16_rx1.A"], test_id=self._baseline_name
        )

        with Case(casedir, read_only=True) as case:
            env_mach = case.get_env("mach_specific")
            orig_env = dict(os.environ)

            env_mach.load_env(case)
            module_env = dict(os.environ)

            os.environ.clear()
            os.environ.update(orig_env)

            env_mach.load_env(case, force_method="generic")
            generic_env = dict(os.environ)

            os.environ.clear()
            os.environ.update(orig_env)

            problems = ""
            for mkey, mval in module_env.items():
                if mkey not in generic_env:
                    if not mkey.startswith("PS") and mkey != "OLDPWD":
                        problems += "Generic missing key: {}\n".format(mkey)
                elif (
                    mval != generic_env[mkey]
                    and mkey not in ["_", "SHLVL", "PWD"]
                    and not mkey.endswith("()")
                ):
                    problems += "Value mismatch for key {}: {} != {}\n".format(
                        mkey, repr(mval), repr(generic_env[mkey])
                    )

            for gkey in generic_env.keys():
                if gkey not in module_env:
                    problems += "Modules missing key: {}\n".format(gkey)

            self.assertEqual(problems, "", msg=problems)

    def test_case_submit_interface(self):
        # the current directory may not exist, so make sure we are in a real directory
        os.chdir(os.getenv("HOME"))
        sys.path.append(self.TOOLS_DIR)
        case_submit_path = os.path.join(self.TOOLS_DIR, "case.submit")

        module = utils.import_from_file("case.submit", case_submit_path)

        sys.argv = [
            "case.submit",
            "--batch-args",
            "'random_arguments_here.%j'",
            "--mail-type",
            "fail",
            "--mail-user",
            "'random_arguments_here.%j'",
        ]
        module._main_func(None, True)

    def test_xml_caching(self):
        casedir = self._create_test(
            ["--no-build", "TESTRUNPASS.f19_g16_rx1.A"], test_id=self._baseline_name
        )

        active = os.path.join(casedir, "env_run.xml")
        backup = os.path.join(casedir, "env_run.xml.bak")

        utils.safe_copy(active, backup)

        with Case(casedir, read_only=False) as case:
            env_run = EnvRun(casedir, read_only=True)
            self.assertEqual(case.get_value("RUN_TYPE"), "startup")
            case.set_value("RUN_TYPE", "branch")
            self.assertEqual(case.get_value("RUN_TYPE"), "branch")
            self.assertEqual(env_run.get_value("RUN_TYPE"), "branch")

        with Case(casedir) as case:
            self.assertEqual(case.get_value("RUN_TYPE"), "branch")

        time.sleep(0.2)
        utils.safe_copy(backup, active)

        with Case(casedir, read_only=False) as case:
            self.assertEqual(case.get_value("RUN_TYPE"), "startup")
            case.set_value("RUN_TYPE", "branch")

        with Case(casedir, read_only=False) as case:
            self.assertEqual(case.get_value("RUN_TYPE"), "branch")
            time.sleep(0.2)
            utils.safe_copy(backup, active)
            case.read_xml()  # Manual re-sync
            self.assertEqual(case.get_value("RUN_TYPE"), "startup")
            case.set_value("RUN_TYPE", "branch")
            self.assertEqual(case.get_value("RUN_TYPE"), "branch")

        with Case(casedir) as case:
            self.assertEqual(case.get_value("RUN_TYPE"), "branch")
            time.sleep(0.2)
            utils.safe_copy(backup, active)
            env_run = EnvRun(casedir, read_only=True)
            self.assertEqual(env_run.get_value("RUN_TYPE"), "startup")

        with Case(casedir, read_only=False) as case:
            self.assertEqual(case.get_value("RUN_TYPE"), "startup")
            case.set_value("RUN_TYPE", "branch")

        # behind the back detection.
        with self.assertRaises(utils.CIMEError):
            with Case(casedir, read_only=False) as case:
                case.set_value("RUN_TYPE", "startup")
                time.sleep(0.2)
                utils.safe_copy(backup, active)

        with Case(casedir, read_only=False) as case:
            case.set_value("RUN_TYPE", "branch")

        # If there's no modications within CIME, the files should not be written
        # and therefore no timestamp check
        with Case(casedir) as case:
            time.sleep(0.2)
            utils.safe_copy(backup, active)

    def test_configure(self):
        testname = "SMS.f09_g16.X"
        casedir = self._create_test(
            [testname, "--no-build"], test_id=self._baseline_name
        )

        manual_config_dir = os.path.join(casedir, "manual_config")
        os.mkdir(manual_config_dir)

        utils.run_cmd_no_fail(
            "{} --machine={} --compiler={}".format(
                os.path.join(utils.get_cime_root(), "CIME", "scripts", "configure"),
                self._machine,
                self._compiler,
            ),
            from_dir=manual_config_dir,
        )

        with open(os.path.join(casedir, "env_mach_specific.xml"), "r") as fd:
            case_env_contents = fd.read()

        with open(os.path.join(manual_config_dir, "env_mach_specific.xml"), "r") as fd:
            man_env_contents = fd.read()

        self.assertEqual(case_env_contents, man_env_contents)

    def test_self_build_cprnc(self):
        if self.NO_FORTRAN_RUN:
            self.skipTest("Skipping fortran test")
        if self.TEST_COMPILER and "gpu" in self.TEST_COMPILER:
            self.skipTest("Skipping cprnc test for gpu compiler")

        testname = "ERS_Ln7.f19_g16_rx1.A"
        casedir = self._create_test(
            [testname, "--no-build"], test_id=self._baseline_name
        )

        self.run_cmd_assert_result(
            "./xmlchange CCSM_CPRNC=this_is_a_broken_cprnc", from_dir=casedir
        )
        self.run_cmd_assert_result("./case.build", from_dir=casedir)
        self.run_cmd_assert_result("./case.submit", from_dir=casedir)

        self._wait_for_tests(self._baseline_name, always_wait=True)

    def test_case_clean(self):
        testname = "ERS_Ln7.f19_g16_rx1.A"
        casedir = self._create_test(
            [testname, "--no-build"], test_id=self._baseline_name
        )

        self.run_cmd_assert_result("./case.setup --clean", from_dir=casedir)
        self.run_cmd_assert_result("./case.setup --clean", from_dir=casedir)
        self.run_cmd_assert_result("./case.setup", from_dir=casedir)
