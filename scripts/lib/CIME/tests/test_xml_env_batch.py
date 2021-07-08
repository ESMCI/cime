#!/usr/bin/env python3

import unittest
from unittest import mock

from CIME.XML.env_batch import EnvBatch

# pylint: disable=unused-argument

class TestXMLEnvBatch(unittest.TestCase):

    @mock.patch("CIME.XML.env_batch.EnvBatch.get")
    def test_get_queue_specs(self, get):
        node = mock.MagicMock()

        batch = EnvBatch()

        get.side_effect = [
            "1", "1", None, None, "case.run", "08:00:00", "05:00:00", \
            "12:00:00", "false",
        ]

        nodemin, nodemax, jobname, walltimedef, walltimemin, walltimemax, \
            jobmin, jobmax, strict = batch.get_queue_specs(node)

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
    @mock.patch("CIME.XML.env_batch.EnvBatch.get_queue_specs", return_value=[
        1, 1, "case.run", "10:00:00", "08:00:00", "12:00:00", 1, 1, False,
    ])
    @mock.patch("CIME.XML.env_batch.EnvBatch.select_best_queue")
    @mock.patch("CIME.XML.env_batch.EnvBatch.get_default_queue")
    def test_set_job_defaults_honor_walltimemax(self, get_default_queue, select_best_queue,
                              get_queue_specs, text):
        case = mock.MagicMock()

        batch_jobs = [
            ("case.run", {
                "template": "template.case.run",
                "prereq": "$BUILD_COMPLETE and not $TEST"
            })
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

        env_workflow.set_value.assert_any_call("JOB_QUEUE", "default",
                                               subgroup="case.run",
                                               ignore_type=False)
        env_workflow.set_value.assert_any_call("JOB_WALLCLOCK_TIME", "20:00:00",
                                               subgroup="case.run")

    @mock.patch("CIME.XML.env_batch.EnvBatch.text", return_value="default")
    # nodemin, nodemax, jobname, walltimemin, walltimemax, jobmin, jobmax, strict
    @mock.patch("CIME.XML.env_batch.EnvBatch.get_queue_specs", return_value=[
        1, 1, "case.run", "10:00:00", "08:00:00", "12:00:00", 1, 1, False,
    ])
    @mock.patch("CIME.XML.env_batch.EnvBatch.select_best_queue")
    @mock.patch("CIME.XML.env_batch.EnvBatch.get_default_queue")
    def test_set_job_defaults_honor_walltimemin(self, get_default_queue, select_best_queue,
                              get_queue_specs, text):
        case = mock.MagicMock()

        batch_jobs = [
            ("case.run", {
                "template": "template.case.run",
                "prereq": "$BUILD_COMPLETE and not $TEST"
            })
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

        env_workflow.set_value.assert_any_call("JOB_QUEUE", "default",
                                               subgroup="case.run",
                                               ignore_type=False)
        env_workflow.set_value.assert_any_call("JOB_WALLCLOCK_TIME", "05:00:00",
                                               subgroup="case.run")

    @mock.patch("CIME.XML.env_batch.EnvBatch.text", return_value="default")
    # nodemin, nodemax, jobname, walltimemax, jobmin, jobmax, strict
    @mock.patch("CIME.XML.env_batch.EnvBatch.get_queue_specs", return_value=[
        1, 1, "case.run", "10:00:00", "08:00:00", "12:00:00", 1, 1, False,
    ])
    @mock.patch("CIME.XML.env_batch.EnvBatch.select_best_queue")
    @mock.patch("CIME.XML.env_batch.EnvBatch.get_default_queue")
    def test_set_job_defaults_user_walltime(self, get_default_queue,
                                            select_best_queue,
                                            get_queue_specs, text):
        case = mock.MagicMock()

        batch_jobs = [
            ("case.run", {
                "template": "template.case.run",
                "prereq": "$BUILD_COMPLETE and not $TEST"
            })
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

        env_workflow.set_value.assert_any_call("JOB_QUEUE", "default",
                                               subgroup="case.run",
                                               ignore_type=False)
        env_workflow.set_value.assert_any_call("JOB_WALLCLOCK_TIME", "10:00:00",
                                               subgroup="case.run")

    @mock.patch("CIME.XML.env_batch.EnvBatch.text", return_value="default")
    # nodemin, nodemax, jobname, walltimemax, jobmin, jobmax, strict
    @mock.patch("CIME.XML.env_batch.EnvBatch.get_queue_specs", return_value=[
        1, 1, "case.run", "10:00:00", "05:00:00", None, 1, 1, False,
    ])
    @mock.patch("CIME.XML.env_batch.EnvBatch.select_best_queue")
    @mock.patch("CIME.XML.env_batch.EnvBatch.get_default_queue")
    def test_set_job_defaults_walltimemax_none(self, get_default_queue, select_best_queue,
                              get_queue_specs, text):
        case = mock.MagicMock()

        batch_jobs = [
            ("case.run", {
                "template": "template.case.run",
                "prereq": "$BUILD_COMPLETE and not $TEST"
            })
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

        env_workflow.set_value.assert_any_call("JOB_QUEUE", "default",
                                               subgroup="case.run",
                                               ignore_type=False)
        env_workflow.set_value.assert_any_call("JOB_WALLCLOCK_TIME", "08:00:00",
                                               subgroup="case.run")

    @mock.patch("CIME.XML.env_batch.EnvBatch.text", return_value="default")
    # nodemin, nodemax, jobname, walltimemax, jobmin, jobmax, strict
    @mock.patch("CIME.XML.env_batch.EnvBatch.get_queue_specs", return_value=[
        1, 1, "case.run", "10:00:00", None, "12:00:00", 1, 1, False,
    ])
    @mock.patch("CIME.XML.env_batch.EnvBatch.select_best_queue")
    @mock.patch("CIME.XML.env_batch.EnvBatch.get_default_queue")
    def test_set_job_defaults_walltimemin_none(self, get_default_queue, select_best_queue,
                              get_queue_specs, text):
        case = mock.MagicMock()

        batch_jobs = [
            ("case.run", {
                "template": "template.case.run",
                "prereq": "$BUILD_COMPLETE and not $TEST"
            })
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

        env_workflow.set_value.assert_any_call("JOB_QUEUE", "default",
                                               subgroup="case.run",
                                               ignore_type=False)
        env_workflow.set_value.assert_any_call("JOB_WALLCLOCK_TIME", "08:00:00",
                                               subgroup="case.run")

    @mock.patch("CIME.XML.env_batch.EnvBatch.text", return_value="default")
    # nodemin, nodemax, jobname, walltimemax, jobmin, jobmax, strict
    @mock.patch("CIME.XML.env_batch.EnvBatch.get_queue_specs", return_value=[
        1, 1, "case.run", "10:00:00", "08:00:00", "12:00:00", 1, 1, False,
    ])
    @mock.patch("CIME.XML.env_batch.EnvBatch.select_best_queue")
    @mock.patch("CIME.XML.env_batch.EnvBatch.get_default_queue")
    def test_set_job_defaults_walltimedef(self, get_default_queue, select_best_queue,
                              get_queue_specs, text):
        case = mock.MagicMock()

        batch_jobs = [
            ("case.run", {
                "template": "template.case.run",
                "prereq": "$BUILD_COMPLETE and not $TEST"
            })
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

        env_workflow.set_value.assert_any_call("JOB_QUEUE", "default",
                                               subgroup="case.run",
                                               ignore_type=False)
        env_workflow.set_value.assert_any_call("JOB_WALLCLOCK_TIME", "10:00:00",
                                               subgroup="case.run")

    @mock.patch("CIME.XML.env_batch.EnvBatch.text", return_value="default")
    # nodemin, nodemax, jobname, walltimemax, jobmin, jobmax, strict
    @mock.patch("CIME.XML.env_batch.EnvBatch.get_queue_specs", return_value=[
        1, 1, "case.run", None, "08:00:00", "12:00:00", 1, 1, False,
    ])
    @mock.patch("CIME.XML.env_batch.EnvBatch.select_best_queue")
    @mock.patch("CIME.XML.env_batch.EnvBatch.get_default_queue")
    def test_set_job_defaults(self, get_default_queue, select_best_queue,
                              get_queue_specs, text):
        case = mock.MagicMock()

        batch_jobs = [
            ("case.run", {
                "template": "template.case.run",
                "prereq": "$BUILD_COMPLETE and not $TEST"
            })
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

        env_workflow.set_value.assert_any_call("JOB_QUEUE", "default",
                                               subgroup="case.run",
                                               ignore_type=False)
        env_workflow.set_value.assert_any_call("JOB_WALLCLOCK_TIME", "12:00:00",
                                               subgroup="case.run")

if __name__ == '__main__':
    unittest.main()
