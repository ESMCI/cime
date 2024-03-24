#!/usr/bin/env python3

import os
import unittest
import tempfile
from unittest import mock

from CIME.utils import CIMEError
from CIME.XML.env_batch import EnvBatch, get_job_deps

# pylint: disable=unused-argument


class TestXMLEnvBatch(unittest.TestCase):
    @mock.patch("CIME.XML.env_batch.EnvBatch._submit_single_job")
    def test_submit_jobs(self, _submit_single_job):
        case = mock.MagicMock()

        case.get_value.side_effect = [
            False,
        ]

        env_batch = EnvBatch()

        with self.assertRaises(CIMEError):
            env_batch.submit_jobs(case)

    @mock.patch("CIME.XML.env_batch.os.path.isfile")
    @mock.patch("CIME.XML.env_batch.get_batch_script_for_job")
    @mock.patch("CIME.XML.env_batch.EnvBatch._submit_single_job")
    def test_submit_jobs_dependency(
        self, _submit_single_job, get_batch_script_for_job, isfile
    ):
        case = mock.MagicMock()

        case.get_env.return_value.get_jobs.return_value = [
            "case.build",
            "case.run",
        ]

        case.get_env.return_value.get_value.side_effect = [
            None,
            "",
            None,
            "case.build",
        ]

        case.get_value.side_effect = [
            False,
        ]

        _submit_single_job.side_effect = ["0", "1"]

        isfile.return_value = True

        get_batch_script_for_job.side_effect = [".case.build", ".case.run"]

        env_batch = EnvBatch()

        depid = env_batch.submit_jobs(case)

        _submit_single_job.assert_any_call(
            case,
            "case.build",
            skip_pnl=False,
            resubmit_immediate=False,
            dep_jobs=[],
            allow_fail=False,
            no_batch=False,
            mail_user=None,
            mail_type=None,
            batch_args=None,
            dry_run=False,
            workflow=True,
        )
        _submit_single_job.assert_any_call(
            case,
            "case.run",
            skip_pnl=False,
            resubmit_immediate=False,
            dep_jobs=[
                "0",
            ],
            allow_fail=False,
            no_batch=False,
            mail_user=None,
            mail_type=None,
            batch_args=None,
            dry_run=False,
            workflow=True,
        )
        assert depid == {"case.build": "0", "case.run": "1"}

    @mock.patch("CIME.XML.env_batch.os.path.isfile")
    @mock.patch("CIME.XML.env_batch.get_batch_script_for_job")
    @mock.patch("CIME.XML.env_batch.EnvBatch._submit_single_job")
    def test_submit_jobs_single(
        self, _submit_single_job, get_batch_script_for_job, isfile
    ):
        case = mock.MagicMock()

        case.get_env.return_value.get_jobs.return_value = [
            "case.run",
        ]

        case.get_env.return_value.get_value.return_value = None

        case.get_value.side_effect = [
            False,
        ]

        _submit_single_job.return_value = "0"

        isfile.return_value = True

        get_batch_script_for_job.side_effect = [
            ".case.run",
        ]

        env_batch = EnvBatch()

        depid = env_batch.submit_jobs(case)

        _submit_single_job.assert_any_call(
            case,
            "case.run",
            skip_pnl=False,
            resubmit_immediate=False,
            dep_jobs=[],
            allow_fail=False,
            no_batch=False,
            mail_user=None,
            mail_type=None,
            batch_args=None,
            dry_run=False,
            workflow=True,
        )
        assert depid == {"case.run": "0"}

    def test_get_job_deps(self):
        # no jobs
        job_deps = get_job_deps("", {})

        assert job_deps == []

        # dependency doesn't exist
        job_deps = get_job_deps("case.run", {})

        assert job_deps == []

        job_deps = get_job_deps("case.run", {"case.run": 0})

        assert job_deps == [
            "0",
        ]

        job_deps = get_job_deps(
            "case.run case.post_run_io", {"case.run": 0, "case.post_run_io": 1}
        )

        assert job_deps == ["0", "1"]

        # old syntax
        job_deps = get_job_deps("case.run and case.post_run_io", {"case.run": 0})

        assert job_deps == [
            "0",
        ]

        # old syntax
        job_deps = get_job_deps(
            "(case.run and case.post_run_io) or case.test", {"case.run": 0}
        )

        assert job_deps == [
            "0",
        ]

        job_deps = get_job_deps("", {}, user_prereq="2")

        assert job_deps == [
            "2",
        ]

        job_deps = get_job_deps("", {}, prev_job="1")

        assert job_deps == [
            "1",
        ]

    def test_get_submit_args_job_queue(self):
        with tempfile.NamedTemporaryFile() as tfile:
            tfile.write(
                b"""<?xml version="1.0"?>
<file id="env_batch.xml" version="2.0">
  <header>
      These variables may be changed anytime during a run, they
      control arguments to the batch submit command.
    </header>
  <group id="config_batch">
    <entry id="BATCH_SYSTEM" value="slurm">
      <type>char</type>
      <valid_values>miller_slurm,nersc_slurm,lc_slurm,moab,pbs,lsf,slurm,cobalt,cobalt_theta,none</valid_values>
      <desc>The batch system type to use for this machine.</desc>
    </entry>
  </group>
  <group id="job_submission">
    <entry id="PROJECT_REQUIRED" value="FALSE">
      <type>logical</type>
      <valid_values>TRUE,FALSE</valid_values>
      <desc>whether the PROJECT value is required on this machine</desc>
    </entry>
  </group>
  <batch_system MACH="docker" type="slurm">
    <submit_args>
      <argument>-w default</argument>
      <argument job_queue="short">-w short</argument>
      <argument job_queue="long">-w long</argument>
      <argument>-A $VARIABLE_THAT_DOES_NOT_EXIST</argument>
    </submit_args>
    <queues>
      <queue walltimemax="01:00:00" nodemax="1">long</queue>
      <queue walltimemax="00:30:00" nodemax="1" default="true">short</queue>
    </queues>
  </batch_system>
</file>
"""
            )

            tfile.seek(0)

            batch = EnvBatch(infile=tfile.name)

            case = mock.MagicMock()

            case.get_value.side_effect = ("long", "long", None)

            case.get_resolved_value.return_value = None

            case.filename = mock.PropertyMock(return_value=tfile.name)

            submit_args = batch.get_submit_args(case, ".case.run")

            expected_args = "  -w default -w long"
            assert submit_args == expected_args

    @mock.patch.dict(os.environ, {"TEST": "GOOD"})
    def test_get_submit_args(self):
        with tempfile.NamedTemporaryFile() as tfile:
            tfile.write(
                b"""<?xml version="1.0"?>
<file id="env_batch.xml" version="2.0">
  <header>
      These variables may be changed anytime during a run, they
      control arguments to the batch submit command.
    </header>
  <group id="config_batch">
    <entry id="BATCH_SYSTEM" value="slurm">
      <type>char</type>
      <valid_values>miller_slurm,nersc_slurm,lc_slurm,moab,pbs,lsf,slurm,cobalt,cobalt_theta,none</valid_values>
      <desc>The batch system type to use for this machine.</desc>
    </entry>
  </group>
  <group id="job_submission">
    <entry id="PROJECT_REQUIRED" value="FALSE">
      <type>logical</type>
      <valid_values>TRUE,FALSE</valid_values>
      <desc>whether the PROJECT value is required on this machine</desc>
    </entry>
  </group>
  <batch_system type="slurm">
    <batch_query per_job_arg="-j">squeue</batch_query>
    <batch_submit>sbatch</batch_submit>
    <batch_cancel>scancel</batch_cancel>
    <batch_directive>#SBATCH</batch_directive>
    <jobid_pattern>(\d+)$</jobid_pattern>
    <depend_string>--dependency=afterok:jobid</depend_string>
    <depend_allow_string>--dependency=afterany:jobid</depend_allow_string>
    <depend_separator>:</depend_separator>
    <walltime_format>%H:%M:%S</walltime_format>
    <batch_mail_flag>--mail-user</batch_mail_flag>
    <batch_mail_type_flag>--mail-type</batch_mail_type_flag>
    <batch_mail_type>none, all, begin, end, fail</batch_mail_type>
    <submit_args>
      <arg flag="--time" name="$JOB_WALLCLOCK_TIME"/>
      <arg flag="-p" name="$JOB_QUEUE"/>
      <arg flag="--account" name="$PROJECT"/>
      <arg flag="--no-arg" />
      <arg flag="--path" name="$$ENV{TEST}" />
    </submit_args>
    <directives>
      <directive> --job-name={{ job_id }}</directive>
      <directive> --nodes={{ num_nodes }}</directive>
      <directive> --output={{ job_id }}.%j </directive>
      <directive> --exclusive </directive>
    </directives>
  </batch_system>
  <batch_system MACH="docker" type="slurm">
    <submit_args>
      <argument>-w docker</argument>
    </submit_args>
    <queues>
      <queue walltimemax="01:00:00" nodemax="1">long</queue>
      <queue walltimemax="00:30:00" nodemax="1" default="true">short</queue>
    </queues>
  </batch_system>
</file>
"""
            )

            tfile.seek(0)

            batch = EnvBatch(infile=tfile.name)

            case = mock.MagicMock()

            case.get_value.side_effect = [
                os.path.dirname(tfile.name),
                "00:30:00",
                "long",
                "CIME",
                "/test",
            ]

            def my_get_resolved_value(val):
                return val

            # value for --path
            case.get_resolved_value.side_effect = my_get_resolved_value

            case.filename = mock.PropertyMock(return_value=tfile.name)

            submit_args = batch.get_submit_args(case, ".case.run")

            expected_args = "  --time 00:30:00 -p long --account CIME --no-arg --path /test -w docker"

            assert submit_args == expected_args

    @mock.patch("CIME.XML.env_batch.EnvBatch.get")
    def test_get_queue_specs(self, get):
        node = mock.MagicMock()

        batch = EnvBatch()

        get.side_effect = [
            "1",
            "1",
            None,
            None,
            "case.run",
            "08:00:00",
            "05:00:00",
            "12:00:00",
            "false",
        ]

        (
            nodemin,
            nodemax,
            jobname,
            walltimedef,
            walltimemin,
            walltimemax,
            jobmin,
            jobmax,
            strict,
        ) = batch.get_queue_specs(node)

        self.assertTrue(nodemin == 1)
        self.assertTrue(nodemax == 1)
        self.assertTrue(jobname == "case.run")
        self.assertTrue(walltimedef == "08:00:00")
        self.assertTrue(walltimemin == "05:00:00")
        self.assertTrue(walltimemax == "12:00:00")
        self.assertTrue(jobmin == None)
        self.assertTrue(jobmax == None)
        self.assertFalse(strict)

    @mock.patch("CIME.XML.env_batch.EnvBatch.text", return_value="default")
    # nodemin, nodemax, jobname, walltimemin, walltimemax, jobmin, jobmax, strict
    @mock.patch(
        "CIME.XML.env_batch.EnvBatch.get_queue_specs",
        return_value=[
            1,
            1,
            "case.run",
            "10:00:00",
            "08:00:00",
            "12:00:00",
            1,
            1,
            False,
        ],
    )
    @mock.patch("CIME.XML.env_batch.EnvBatch.select_best_queue")
    @mock.patch("CIME.XML.env_batch.EnvBatch.get_default_queue")
    def test_set_job_defaults_honor_walltimemax(
        self, get_default_queue, select_best_queue, get_queue_specs, text
    ):
        case = mock.MagicMock()

        batch_jobs = [
            (
                "case.run",
                {
                    "template": "template.case.run",
                    "prereq": "$BUILD_COMPLETE and not $TEST",
                },
            )
        ]

        def get_value(*args, **kwargs):
            if args[0] == "USER_REQUESTED_WALLTIME":
                return "20:00:00"

            return mock.MagicMock()

        case.get_value = get_value

        case.get_env.return_value.get_jobs.return_value = ["case.run"]

        batch = EnvBatch()

        batch.set_job_defaults(batch_jobs, case)

        env_workflow = case.get_env.return_value

        env_workflow.set_value.assert_any_call(
            "JOB_QUEUE", "default", subgroup="case.run", ignore_type=False
        )
        env_workflow.set_value.assert_any_call(
            "JOB_WALLCLOCK_TIME", "20:00:00", subgroup="case.run"
        )

    @mock.patch("CIME.XML.env_batch.EnvBatch.text", return_value="default")
    # nodemin, nodemax, jobname, walltimemin, walltimemax, jobmin, jobmax, strict
    @mock.patch(
        "CIME.XML.env_batch.EnvBatch.get_queue_specs",
        return_value=[
            1,
            1,
            "case.run",
            "10:00:00",
            "08:00:00",
            "12:00:00",
            1,
            1,
            False,
        ],
    )
    @mock.patch("CIME.XML.env_batch.EnvBatch.select_best_queue")
    @mock.patch("CIME.XML.env_batch.EnvBatch.get_default_queue")
    def test_set_job_defaults_honor_walltimemin(
        self, get_default_queue, select_best_queue, get_queue_specs, text
    ):
        case = mock.MagicMock()

        batch_jobs = [
            (
                "case.run",
                {
                    "template": "template.case.run",
                    "prereq": "$BUILD_COMPLETE and not $TEST",
                },
            )
        ]

        def get_value(*args, **kwargs):
            if args[0] == "USER_REQUESTED_WALLTIME":
                return "05:00:00"

            return mock.MagicMock()

        case.get_value = get_value

        case.get_env.return_value.get_jobs.return_value = ["case.run"]

        batch = EnvBatch()

        batch.set_job_defaults(batch_jobs, case)

        env_workflow = case.get_env.return_value

        env_workflow.set_value.assert_any_call(
            "JOB_QUEUE", "default", subgroup="case.run", ignore_type=False
        )
        env_workflow.set_value.assert_any_call(
            "JOB_WALLCLOCK_TIME", "05:00:00", subgroup="case.run"
        )

    @mock.patch("CIME.XML.env_batch.EnvBatch.text", return_value="default")
    # nodemin, nodemax, jobname, walltimemax, jobmin, jobmax, strict
    @mock.patch(
        "CIME.XML.env_batch.EnvBatch.get_queue_specs",
        return_value=[
            1,
            1,
            "case.run",
            "10:00:00",
            "08:00:00",
            "12:00:00",
            1,
            1,
            False,
        ],
    )
    @mock.patch("CIME.XML.env_batch.EnvBatch.select_best_queue")
    @mock.patch("CIME.XML.env_batch.EnvBatch.get_default_queue")
    def test_set_job_defaults_user_walltime(
        self, get_default_queue, select_best_queue, get_queue_specs, text
    ):
        case = mock.MagicMock()

        batch_jobs = [
            (
                "case.run",
                {
                    "template": "template.case.run",
                    "prereq": "$BUILD_COMPLETE and not $TEST",
                },
            )
        ]

        def get_value(*args, **kwargs):
            if args[0] == "USER_REQUESTED_WALLTIME":
                return "10:00:00"

            return mock.MagicMock()

        case.get_value = get_value

        case.get_env.return_value.get_jobs.return_value = ["case.run"]

        batch = EnvBatch()

        batch.set_job_defaults(batch_jobs, case)

        env_workflow = case.get_env.return_value

        env_workflow.set_value.assert_any_call(
            "JOB_QUEUE", "default", subgroup="case.run", ignore_type=False
        )
        env_workflow.set_value.assert_any_call(
            "JOB_WALLCLOCK_TIME", "10:00:00", subgroup="case.run"
        )

    @mock.patch("CIME.XML.env_batch.EnvBatch.text", return_value="default")
    # nodemin, nodemax, jobname, walltimemax, jobmin, jobmax, strict
    @mock.patch(
        "CIME.XML.env_batch.EnvBatch.get_queue_specs",
        return_value=[
            1,
            1,
            "case.run",
            "10:00:00",
            "05:00:00",
            None,
            1,
            1,
            False,
        ],
    )
    @mock.patch("CIME.XML.env_batch.EnvBatch.select_best_queue")
    @mock.patch("CIME.XML.env_batch.EnvBatch.get_default_queue")
    def test_set_job_defaults_walltimemax_none(
        self, get_default_queue, select_best_queue, get_queue_specs, text
    ):
        case = mock.MagicMock()

        batch_jobs = [
            (
                "case.run",
                {
                    "template": "template.case.run",
                    "prereq": "$BUILD_COMPLETE and not $TEST",
                },
            )
        ]

        def get_value(*args, **kwargs):
            if args[0] == "USER_REQUESTED_WALLTIME":
                return "08:00:00"

            return mock.MagicMock()

        case.get_value = get_value

        case.get_env.return_value.get_jobs.return_value = ["case.run"]

        batch = EnvBatch()

        batch.set_job_defaults(batch_jobs, case)

        env_workflow = case.get_env.return_value

        env_workflow.set_value.assert_any_call(
            "JOB_QUEUE", "default", subgroup="case.run", ignore_type=False
        )
        env_workflow.set_value.assert_any_call(
            "JOB_WALLCLOCK_TIME", "08:00:00", subgroup="case.run"
        )

    @mock.patch("CIME.XML.env_batch.EnvBatch.text", return_value="default")
    # nodemin, nodemax, jobname, walltimemax, jobmin, jobmax, strict
    @mock.patch(
        "CIME.XML.env_batch.EnvBatch.get_queue_specs",
        return_value=[
            1,
            1,
            "case.run",
            "10:00:00",
            None,
            "12:00:00",
            1,
            1,
            False,
        ],
    )
    @mock.patch("CIME.XML.env_batch.EnvBatch.select_best_queue")
    @mock.patch("CIME.XML.env_batch.EnvBatch.get_default_queue")
    def test_set_job_defaults_walltimemin_none(
        self, get_default_queue, select_best_queue, get_queue_specs, text
    ):
        case = mock.MagicMock()

        batch_jobs = [
            (
                "case.run",
                {
                    "template": "template.case.run",
                    "prereq": "$BUILD_COMPLETE and not $TEST",
                },
            )
        ]

        def get_value(*args, **kwargs):
            if args[0] == "USER_REQUESTED_WALLTIME":
                return "08:00:00"

            return mock.MagicMock()

        case.get_value = get_value

        case.get_env.return_value.get_jobs.return_value = ["case.run"]

        batch = EnvBatch()

        batch.set_job_defaults(batch_jobs, case)

        env_workflow = case.get_env.return_value

        env_workflow.set_value.assert_any_call(
            "JOB_QUEUE", "default", subgroup="case.run", ignore_type=False
        )
        env_workflow.set_value.assert_any_call(
            "JOB_WALLCLOCK_TIME", "08:00:00", subgroup="case.run"
        )

    @mock.patch("CIME.XML.env_batch.EnvBatch.text", return_value="default")
    # nodemin, nodemax, jobname, walltimemax, jobmin, jobmax, strict
    @mock.patch(
        "CIME.XML.env_batch.EnvBatch.get_queue_specs",
        return_value=[
            1,
            1,
            "case.run",
            "10:00:00",
            "08:00:00",
            "12:00:00",
            1,
            1,
            False,
        ],
    )
    @mock.patch("CIME.XML.env_batch.EnvBatch.select_best_queue")
    @mock.patch("CIME.XML.env_batch.EnvBatch.get_default_queue")
    def test_set_job_defaults_walltimedef(
        self, get_default_queue, select_best_queue, get_queue_specs, text
    ):
        case = mock.MagicMock()

        batch_jobs = [
            (
                "case.run",
                {
                    "template": "template.case.run",
                    "prereq": "$BUILD_COMPLETE and not $TEST",
                },
            )
        ]

        def get_value(*args, **kwargs):
            if args[0] == "USER_REQUESTED_WALLTIME":
                return None

            return mock.MagicMock()

        case.get_value = get_value

        case.get_env.return_value.get_jobs.return_value = ["case.run"]

        batch = EnvBatch()

        batch.set_job_defaults(batch_jobs, case)

        env_workflow = case.get_env.return_value

        env_workflow.set_value.assert_any_call(
            "JOB_QUEUE", "default", subgroup="case.run", ignore_type=False
        )
        env_workflow.set_value.assert_any_call(
            "JOB_WALLCLOCK_TIME", "10:00:00", subgroup="case.run"
        )

    @mock.patch("CIME.XML.env_batch.EnvBatch.text", return_value="default")
    # nodemin, nodemax, jobname, walltimemax, jobmin, jobmax, strict
    @mock.patch(
        "CIME.XML.env_batch.EnvBatch.get_queue_specs",
        return_value=[
            1,
            1,
            "case.run",
            None,
            "08:00:00",
            "12:00:00",
            1,
            1,
            False,
        ],
    )
    @mock.patch("CIME.XML.env_batch.EnvBatch.select_best_queue")
    @mock.patch("CIME.XML.env_batch.EnvBatch.get_default_queue")
    def test_set_job_defaults(
        self, get_default_queue, select_best_queue, get_queue_specs, text
    ):
        case = mock.MagicMock()

        batch_jobs = [
            (
                "case.run",
                {
                    "template": "template.case.run",
                    "prereq": "$BUILD_COMPLETE and not $TEST",
                },
            )
        ]

        def get_value(*args, **kwargs):
            if args[0] == "USER_REQUESTED_WALLTIME":
                return None

            return mock.MagicMock()

        case.get_value = get_value

        case.get_env.return_value.get_jobs.return_value = ["case.run"]

        batch = EnvBatch()

        batch.set_job_defaults(batch_jobs, case)

        env_workflow = case.get_env.return_value

        env_workflow.set_value.assert_any_call(
            "JOB_QUEUE", "default", subgroup="case.run", ignore_type=False
        )
        env_workflow.set_value.assert_any_call(
            "JOB_WALLCLOCK_TIME", "12:00:00", subgroup="case.run"
        )


if __name__ == "__main__":
    unittest.main()
