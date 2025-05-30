#!/usr/bin/env python3

import os
import unittest
import tempfile
from contextlib import ExitStack
from unittest import mock

from CIME.utils import CIMEError, expect
from CIME.XML.env_batch import EnvBatch, get_job_deps
from CIME.XML.env_workflow import EnvWorkflow
from CIME.BuildTools.configure import FakeCase

# pylint: disable=unused-argument

XML_BASE = b"""<?xml version="1.0"?>
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
    <jobid_pattern>(\\d+)$</jobid_pattern>
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
      <queue walltimemax="00:15:00" nodemax="1">debug</queue>
      <queue walltimemax="24:00:00" nodemax="20" nodemin="5">big</queue>
      <queue walltimemax="00:30:00" nodemax="5" default="true">smallfast</queue>
    </queues>
  </batch_system>
</file>"""

XML_DIFF = b"""<?xml version="1.0"?>
<file id="env_batch.xml" version="2.0">
  <header>
      These variables may be changed anytime during a run, they
      control arguments to the batch submit command.
    </header>
  <group id="config_batch">
    <entry id="BATCH_SYSTEM" value="pbs">
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
    <batch_submit>batch</batch_submit>
    <batch_cancel>scancel</batch_cancel>
    <batch_directive>#SBATCH</batch_directive>
    <jobid_pattern>(\\d+)$</jobid_pattern>
    <depend_string>--dependency=afterok:jobid</depend_string>
    <depend_allow_string>--dependency=afterany:jobid</depend_allow_string>
    <depend_separator>:</depend_separator>
    <walltime_format>%H:%M:%S</walltime_format>
    <batch_mail_flag>--mail-user</batch_mail_flag>
    <batch_mail_type_flag>--mail-type</batch_mail_type_flag>
    <batch_mail_type>none, all, begin, end, fail</batch_mail_type>
    <submit_args>
      <arg flag="--time" name="$JOB_WALLCLOCK_TIME"/>
      <arg flag="-p" name="pbatch"/>
      <arg flag="--account" name="$PROJECT"/>
      <arg flag="-m" name="plane"/>
    </submit_args>
    <directives>
      <directive> --job-name={{ job_id }}</directive>
      <directive> --nodes=10</directive>
      <directive> --output={{ job_id }}.%j </directive>
      <directive> --exclusive </directive>
      <directive> --qos=high </directive>
    </directives>
  </batch_system>
  <batch_system MACH="docker" type="slurm">
    <submit_args>
      <argument>-w docker</argument>
    </submit_args>
    <queues>
      <queue walltimemax="00:15:00" nodemax="1">debug</queue>
      <queue walltimemax="24:00:00" nodemax="20" nodemin="10">big</queue>
    </queues>
  </batch_system>
</file>"""


XML_CHECK = b"""<?xml version="1.0"?>
<file id="env_batch.xml" version="2.0">
  <header>
      These variables may be changed anytime during a run, they
      control arguments to the batch submit command.
    </header>
  <group id="config_batch">
    <entry id="BATCH_SYSTEM" value="nersc_slurm">
      <type>char</type>
      <valid_values>miller_slurm,nersc_slurm,lc_slurm,moab,pbs,pbspro,lsf,slurm,cobalt,cobalt_theta,slurm_single_node,none</valid_values>
      <desc>The batch system type to use for this machine.</desc>
    </entry>
  </group>
  <group id="job_submission">
    <entry id="PROJECT_REQUIRED" value="TRUE">
      <type>logical</type>
      <valid_values>TRUE,FALSE</valid_values>
      <desc>whether the PROJECT value is required on this machine</desc>
    </entry>
  </group>
  <batch_system MACH="pm-gpu" type="nersc_slurm">
    <directives>
      <directive> --constraint=gpu</directive>
    </directives>
    <directives COMPSET="!.*MMF.*" compiler="gnugpu">
      <directive> --gpus-per-node=4</directive>
      <directive> --gpu-bind=none</directive>
    </directives>
    <directives COMPSET=".*MMF.*" compiler="gnugpu">
      <directive> --gpus-per-task=1</directive>
      <directive> --gpu-bind=map_gpu:0,1,2,3</directive>
    </directives>
    <directives compiler="nvidiagpu">
      <directive> --gpus-per-node=4</directive>
      <directive> --gpu-bind=none</directive>
    </directives>
    <directives compiler="gnu">
      <directive> -G 0</directive>
    </directives>
    <directives compiler="nvidia">
      <directive> -G 0</directive>
    </directives>
    <queues>
      <queue default="true" nodemax="1792" walltimemax="00:45:00">regular</queue>
      <queue nodemax="1792" strict="true" walltimemax="00:45:00">preempt</queue>
      <queue nodemax="1792" strict="true" walltimemax="00:45:00">shared</queue>
      <queue nodemax="1792" strict="true" walltimemax="00:45:00">overrun</queue>
      <queue nodemax="4" strict="true" walltimemax="00:15:00">debug</queue>
    </queues>
  </batch_system>
</file>"""

XML_WORKFLOW = b"""<?xml version="1.0"?>
<file id="env_workflow.xml" version="2.0">
 <header>
      These variables may be changed anytime during a run, they
      control jobs that will be submitted and their dependancies.
 </header>
 <group id="case.test">
    <entry id="task_count" value="1">
      <type>char</type>
    </entry>
    <entry id="thread_count" value="1">
      <type>char</type>
    </entry>
    <entry id="tasks_per_node" value="1">
      <type>char</type>
    </entry>
 </group>
</file>"""


def _open_temp_file(stack, data):
    tfile = stack.enter_context(tempfile.NamedTemporaryFile())

    tfile.write(data)

    tfile.seek(0)

    return tfile


class FakeCaseWWorkflow(FakeCase):
    """
    Extend the FakeCase class to have the functions needed for testing get_jobs_overrides
    Use FakeCase rather than a class mock in order to return a more complex and dynamic
    env_workflow object
    """

    def __init__(
        self,
        compiler,
        mpilib,
        debug,
        comp_interface,
        task_count,
        thread_count,
        tasks_per_node,
        mem_per_task,
        max_mem,
    ):
        super().__init__(compiler, mpilib, debug, comp_interface)
        self._vals["task_count"] = task_count
        self._vals["thread_count"] = thread_count
        self._vals["tasks_per_node"] = tasks_per_node
        self._vals["mem_per_task"] = mem_per_task
        self._vals["max_mem"] = max_mem

    def get_env(self, short_name):
        expect(
            short_name == "workflow",
            "FakeWWorkflow only can handle workflow as short_name sent in",
        )
        with ExitStack() as stack:
            WorkflowFile = _open_temp_file(stack, XML_WORKFLOW)
            env_workflow = EnvWorkflow(infile=WorkflowFile.name)
            env_workflow.set_value(
                "task_count", str(self.get_value("task_count")), subgroup="case.test"
            )
            env_workflow.set_value(
                "thread_count",
                str(self.get_value("thread_count")),
                subgroup="case.test",
            )
            env_workflow.set_value(
                "tasks_per_node",
                str(self.get_value("tasks_per_node")),
                subgroup="case.test",
            )

            return env_workflow

        return None

    def get_resolved_value(
        self, item, attribute=None, subgroup="PRIMARY", resolved=True
    ):
        print(item)
        expect(isinstance(item, str), "item must be a string")
        expect(("$" not in item), "$ not allowed in item for this fake")
        return item

    def get_mpirun_cmd(self, job, overrides):
        if self.get_value("MPILIB") == "mpi-serial":
            mpirun = ""
        else:
            mpirun = "mpirun"
        return mpirun


class TestXMLEnvBatch(unittest.TestCase):
    def test_compare_xml(self):
        with ExitStack() as stack:
            file1 = _open_temp_file(stack, XML_DIFF)
            batch1 = EnvBatch(infile=file1.name)

            file2 = _open_temp_file(stack, XML_BASE)
            batch2 = EnvBatch(infile=file2.name)

            diff = batch1.compare_xml(batch2)
            diff2 = batch2.compare_xml(batch1)

        expected_diff = {
            "BATCH_SYSTEM": ["pbs", "slurm"],
            "arg1": ["-p pbatch", "-p $JOB_QUEUE"],
            "arg3": ["-m plane", ""],
            "batch_submit": ["batch", "sbatch"],
            "directive1": [" --nodes=10", " --nodes={{ num_nodes }}"],
            "directive4": [" --qos=high ", ""],
            "queue1": ["big", "big"],
            "queue2": ["", "smallfast"],
        }

        assert diff == expected_diff

        expected_diff2 = {
            "BATCH_SYSTEM": ["slurm", "pbs"],
            "arg1": ["-p $JOB_QUEUE", "-p pbatch"],
            "arg3": ["", "-m plane"],
            "batch_submit": ["sbatch", "batch"],
            "directive1": [" --nodes={{ num_nodes }}", " --nodes=10"],
            "directive4": ["", " --qos=high "],
            "queue1": ["big", "big"],
            "queue2": ["smallfast", ""],
        }

        assert diff2 == expected_diff2

    def test_compare_xml_same(self):
        with ExitStack() as stack:
            file1 = _open_temp_file(stack, XML_CHECK)
            batch1 = EnvBatch(infile=file1.name)

            file2 = _open_temp_file(stack, XML_CHECK)
            batch2 = EnvBatch(infile=file2.name)

            diff = batch1.compare_xml(batch2)
            diff2 = batch2.compare_xml(batch1)

        expected_diff = {}
        assert diff == expected_diff, f"{diff}"
        assert diff2 == expected_diff, f"{diff2}"

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
    <jobid_pattern>(\\d+)$</jobid_pattern>
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

    def test_get_job_overrides_mpi_serial_single_task(self):
        """Test that get_job_overrides gives expected results for an mpi-serial case with a single task"""
        task_count = 1
        thread_count = 1
        mem_per_task = 10
        tasks_per_node = task_count
        max_mem = 235
        overrides = self.run_get_job_overrides(
            task_count, thread_count, mem_per_task, tasks_per_node, max_mem
        )
        self.assertEqual(overrides["mem_per_node"], mem_per_task)
        self.assertEqual(overrides["tasks_per_node"], task_count)
        self.assertEqual(overrides["max_tasks_per_node"], task_count)
        self.assertEqual(overrides["mpirun"], "")
        self.assertEqual(overrides["thread_count"], str(thread_count))
        self.assertEqual(overrides["num_nodes"], 1)

    def test_get_job_overrides_two_tasks(self):
        """Test that get_job_overrides gives expected results for a case with two tasks"""
        task_count = 2
        thread_count = 1
        mem_per_task = 10
        tasks_per_node = task_count
        max_mem = 235
        # import pdb; pdb.set_trace()
        overrides = self.run_get_job_overrides(
            task_count, thread_count, mem_per_task, tasks_per_node, max_mem
        )
        self.assertEqual(overrides["mem_per_node"], mem_per_task * task_count)
        self.assertEqual(overrides["tasks_per_node"], task_count)
        self.assertEqual(overrides["max_tasks_per_node"], task_count)
        self.assertEqual(overrides["mpirun"], "mpirun")
        self.assertEqual(overrides["thread_count"], str(thread_count))
        self.assertEqual(overrides["num_nodes"], 1)

    def test_get_job_overrides_sixteen_tasks(self):
        """Test that get_job_overrides gives expected results for a case with sixteen tasks"""
        task_count = 16
        thread_count = 1
        mem_per_task = 10
        tasks_per_node = task_count
        max_mem = 235
        overrides = self.run_get_job_overrides(
            task_count, thread_count, mem_per_task, tasks_per_node, max_mem
        )
        self.assertEqual(overrides["mem_per_node"], int(max_mem * task_count / 128))
        self.assertEqual(overrides["tasks_per_node"], task_count)
        self.assertEqual(overrides["max_tasks_per_node"], task_count)
        self.assertEqual(overrides["mpirun"], "mpirun")
        self.assertEqual(overrides["thread_count"], str(thread_count))
        self.assertEqual(overrides["num_nodes"], 1)

    def test_get_job_overrides_twentyfive_tasks(self):
        """Test that get_job_overrides gives expected results for a case with 25 tasks"""
        # This test is mportant for the CTSM regional amazon case that can use 25 tasks
        task_count = 25
        thread_count = 1
        mem_per_task = 10
        tasks_per_node = task_count
        max_mem = 235
        overrides = self.run_get_job_overrides(
            task_count, thread_count, mem_per_task, tasks_per_node, max_mem
        )
        self.assertEqual(overrides["mem_per_node"], int(max_mem * task_count / 128))
        self.assertEqual(overrides["tasks_per_node"], task_count)
        self.assertEqual(overrides["max_tasks_per_node"], task_count)
        self.assertEqual(overrides["mpirun"], "mpirun")
        self.assertEqual(overrides["thread_count"], str(thread_count))
        self.assertEqual(overrides["num_nodes"], 1)

    def test_get_job_overrides_eight_tasks_eight_threads(self):
        """Test that get_job_overrides gives expected results for a case with 8 tasks and 8 threads"""
        task_count = 8
        thread_count = 8
        mem_per_task = 10
        tasks_per_node = task_count
        max_mem = 235
        overrides = self.run_get_job_overrides(
            task_count, thread_count, mem_per_task, tasks_per_node, max_mem
        )
        self.assertEqual(overrides["mem_per_node"], int(max_mem / 2))
        self.assertEqual(overrides["tasks_per_node"], task_count)
        self.assertEqual(overrides["max_tasks_per_node"], task_count * thread_count)
        self.assertEqual(overrides["mpirun"], "mpirun")
        self.assertEqual(overrides["thread_count"], str(thread_count))
        self.assertEqual(overrides["num_nodes"], 1)

    def test_get_job_overrides_sixtyfour_tasks(self):
        """Test that get_job_overrides gives expected results for a case with 64 tasks"""
        task_count = 64
        thread_count = 1
        mem_per_task = 10
        tasks_per_node = task_count
        max_mem = 235
        overrides = self.run_get_job_overrides(
            task_count, thread_count, mem_per_task, tasks_per_node, max_mem
        )
        self.assertEqual(overrides["mem_per_node"], int(max_mem / 2))
        self.assertEqual(overrides["tasks_per_node"], task_count)
        self.assertEqual(overrides["max_tasks_per_node"], task_count)
        self.assertEqual(overrides["mpirun"], "mpirun")
        self.assertEqual(overrides["thread_count"], str(thread_count))
        self.assertEqual(overrides["num_nodes"], 1)

    def test_get_job_overrides_ninetysix_tasks(self):
        """Test that get_job_overrides gives expected results for a case with ninetysix tasks"""
        task_count = 96
        thread_count = 1
        mem_per_task = 10
        tasks_per_node = task_count
        max_mem = 235
        overrides = self.run_get_job_overrides(
            task_count, thread_count, mem_per_task, tasks_per_node, max_mem
        )
        self.assertEqual(overrides["mem_per_node"], int(max_mem * 3 / 4))
        self.assertEqual(overrides["tasks_per_node"], task_count)
        self.assertEqual(overrides["max_tasks_per_node"], task_count)
        self.assertEqual(overrides["mpirun"], "mpirun")
        self.assertEqual(overrides["thread_count"], str(thread_count))
        self.assertEqual(overrides["num_nodes"], 1)

    def test_get_job_overrides_hundredtwentyseven_tasks(self):
        """Test that get_job_overrides gives expected results for a case with 127 tasks"""
        task_count = 127
        thread_count = 1
        mem_per_task = 10
        tasks_per_node = task_count
        max_mem = 235
        overrides = self.run_get_job_overrides(
            task_count, thread_count, mem_per_task, tasks_per_node, max_mem
        )
        self.assertEqual(overrides["mem_per_node"], int(max_mem * task_count / 128))
        self.assertEqual(overrides["tasks_per_node"], task_count)
        self.assertEqual(overrides["max_tasks_per_node"], task_count)
        self.assertEqual(overrides["mpirun"], "mpirun")
        self.assertEqual(overrides["thread_count"], str(thread_count))
        self.assertEqual(overrides["num_nodes"], 1)

    def run_get_job_overrides(
        self, task_count, thread_count, mem_per_task, tasks_per_node, max_mem
    ):
        """Setup and run get_job_overrides so it can be tested from a variety of tests"""

        env_batch = EnvBatch()
        # NOTE: GPU_TYPE is assumed to be none, so no GPU settings will be done
        mpilib = "mpich"
        if task_count == 1:
            mpilib = "mpi-serial"
        case = FakeCaseWWorkflow(
            compiler="intel",
            mpilib=mpilib,
            debug="FALSE",
            comp_interface="nuopc",
            task_count=task_count,
            thread_count=thread_count,
            mem_per_task=mem_per_task,
            tasks_per_node=tasks_per_node,
            max_mem=max_mem,
        )
        totalpes = task_count * thread_count

        case.set_value("TOTALPES", totalpes)
        case.set_value("MAX_TASKS_PER_NODE", 128)
        case.set_value("MEM_PER_TASK", mem_per_task)
        case.set_value("MAX_MEM_PER_NODE", max_mem)

        case.set_value("MAX_GPUS_PER_NODE", 4)
        case.set_value("NGPUS_PER_NODE", 0)
        overrides = env_batch.get_job_overrides("case.test", case)
        self.assertEqual(overrides["ngpus_per_node"], 0)

        return overrides


if __name__ == "__main__":
    unittest.main()
