#!/usr/bin/env python3

"""Unit tests for the ``--timeout`` wiring of :mod:`CIME.jenkins_generic_job`.

These tests verify that a timeout provided to
:func:`CIME.jenkins_generic_job.jenkins_generic_job` is forwarded to
:func:`CIME.wait_for_tests.wait_for_tests`, which is what allows a very long
job to stop itself when Jenkins cannot deliver a timeout signal (for example
when the network connection to the agent is dropped).
"""

import tempfile
from unittest import mock

import pytest

from CIME import jenkins_generic_job


def _make_machine(scratch_root):
    """Return a batch-less machine mock sufficient to drive the job."""
    machine = mock.MagicMock()
    machine.has_batch_system.return_value = False
    machine.get_machine_name.return_value = "mymachine"
    machine.get_value.side_effect = lambda name: {
        "TESTS": "e3sm_developer",
        "PROXY": None,
        "CIME_OUTPUT_ROOT": scratch_root,
        "BATCH_SYSTEM": None,
    }.get(name)
    return machine


def _call(scratch_root, machine, **overrides):
    """Invoke ``jenkins_generic_job`` using the existing-test-id path."""
    kwargs = dict(
        generate_baselines=False,
        submit_to_cdash=False,
        no_batch=True,
        batch_build=False,
        baseline_name="master",
        arg_cdash_build_name=None,
        cdash_project="project",
        arg_test_suite="e3sm_developer",
        cdash_build_group="group",
        baseline_compare=False,
        scratch_root=scratch_root,
        parallel_jobs=None,
        walltime=None,
        machine=machine,
        compiler="gnu",
        real_baseline_name="master",
        baseline_root=None,
        update_success=False,
        check_throughput=False,
        check_memory=False,
        ignore_memleak=False,
        ignore_namelists=False,
        ignore_diffs=False,
        save_timing=False,
        pes_file=None,
        jenkins_id=None,
        queue=None,
        driver=None,
        use_existing_test_id="myexisting123",
    )
    kwargs.update(overrides)
    return jenkins_generic_job.jenkins_generic_job(**kwargs)


@pytest.fixture
def scratch_root():
    with tempfile.TemporaryDirectory() as tmp:
        yield tmp


def test_timeout_wraps_wait_for_tests(scratch_root):
    # Context
    machine = _make_machine(scratch_root)

    # Mocks
    with mock.patch(
        "CIME.wait_for_tests.wait_for_tests", return_value=True
    ) as wait_for_tests, mock.patch(
        "CIME.wait_for_tests.set_up_signal_handlers"
    ), mock.patch(
        "CIME.jenkins_generic_job.glob.glob",
        return_value=[f"{scratch_root}/J/case.mymachine_gnu.myexisting123/TestStatus"],
    ), mock.patch(
        "CIME.jenkins_generic_job.time.time", return_value=0
    ), mock.patch("CIME.jenkins_generic_job.Timeout") as timeout_context:
        # Act
        result = _call(scratch_root, machine, timeout=42)

    # Assert
    assert result is True
    wait_for_tests.assert_called_once()
    timeout_context.assert_called_once_with(
        42, action=jenkins_generic_job.CIME.wait_for_tests.signal_handler
    )
    timeout_context.return_value.__enter__.assert_called_once()


def test_timeout_defaults_to_none(scratch_root):
    machine = _make_machine(scratch_root)
    with mock.patch(
        "CIME.wait_for_tests.wait_for_tests", return_value=True
    ) as wait_for_tests, mock.patch(
        "CIME.wait_for_tests.set_up_signal_handlers"
    ), mock.patch(
        "CIME.jenkins_generic_job.glob.glob",
        return_value=[f"{scratch_root}/J/case.mymachine_gnu.myexisting123/TestStatus"],
    ):
        result = _call(scratch_root, machine)

    assert result is True
    wait_for_tests.assert_called_once()
    assert wait_for_tests.call_args.kwargs["timeout"] is None
