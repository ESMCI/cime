#!/usr/bin/env python3

"""Unit tests for the ``--timeout`` handling of :mod:`CIME.jenkins_generic_job`.

These tests verify that a timeout provided to
:func:`CIME.jenkins_generic_job.jenkins_generic_job` bounds both create_test
and :func:`CIME.wait_for_tests.wait_for_tests`, that the user is told about the
budget at each stage and that a timed-out job is clearly reported as a failure.
"""

import logging
import signal
import tempfile
from unittest import mock

import pytest

import CIME.wait_for_tests
from CIME import jenkins_generic_job
from CIME.jenkins_generic_job import JobTimeout


class FakeClock:
    """Deterministic, manually advanced replacement for ``time.time``."""

    def __init__(self, now=0):
        self.now = now

    def __call__(self):
        return self.now


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


@pytest.fixture(autouse=True)
def reset_signal_received():
    CIME.wait_for_tests.SIGNAL_RECEIVED = False
    yield
    CIME.wait_for_tests.SIGNAL_RECEIVED = False


@pytest.fixture
def clock():
    with mock.patch("CIME.jenkins_generic_job.time.time", FakeClock()) as fake:
        yield fake


@pytest.fixture
def common_mocks(scratch_root):
    """Patch the collaborators shared by every job invocation."""
    with mock.patch(
        "CIME.wait_for_tests.wait_for_tests", return_value=True
    ) as wait_for_tests, mock.patch(
        "CIME.wait_for_tests.set_up_signal_handlers"
    ), mock.patch(
        "CIME.jenkins_generic_job.glob.glob",
        return_value=[f"{scratch_root}/J/case.mymachine_gnu.myexisting123/TestStatus"],
    ):
        yield wait_for_tests


# ---------------------------------------------------------------------------
# JobTimeout
# ---------------------------------------------------------------------------


def test_job_timeout_disabled_when_seconds_is_none():
    # Context
    clock = FakeClock(now=5)
    job_timeout = JobTimeout(None, clock=clock)

    # Act
    clock.now = 500

    # Assert
    assert not job_timeout.enabled
    assert job_timeout.time_left() is None
    assert job_timeout.describe() == "no timeout"
    assert job_timeout.elapsed() == 495
    assert not job_timeout.timed_out


def test_job_timeout_time_left_tracks_clock():
    # Context
    clock = FakeClock(now=10)
    job_timeout = JobTimeout(100, clock=clock)

    # Act
    clock.now = 40

    # Assert
    assert job_timeout.enabled
    assert job_timeout.time_left() == 70
    assert job_timeout.elapsed() == 30
    assert job_timeout.describe().startswith("100 seconds (00:01:40), deadline ")


def test_job_timeout_expire_records_first_stage_and_stops_waiting(caplog):
    # Context
    job_timeout = JobTimeout(60, clock=FakeClock())

    # Act
    with caplog.at_level(logging.WARNING):
        job_timeout.expire("create_test")
        job_timeout.expire("wait_for_tests")

    # Assert
    assert job_timeout.timed_out
    assert job_timeout.expired_stage == "create_test"
    assert CIME.wait_for_tests.SIGNAL_RECEIVED is True
    timeout_warnings = [r for r in caplog.records if "exceeded during" in r.message]
    assert len(timeout_warnings) == 1
    assert "exceeded during create_test" in timeout_warnings[0].message
    assert "00:01:00" in timeout_warnings[0].message


def test_job_timeout_handler_is_usable_as_signal_handler():
    # Context
    job_timeout = JobTimeout(60, clock=FakeClock())

    # Act
    job_timeout.handler("wait_for_tests")(signal.SIGALRM, None)

    # Assert
    assert job_timeout.expired_stage == "wait_for_tests"
    assert CIME.wait_for_tests.SIGNAL_RECEIVED is True


@pytest.mark.parametrize(
    "seconds,expired,expected,fragment",
    [
        (60, True, True, "reported as FAILED"),
        (60, False, False, "within its timeout"),
        (None, False, False, None),
    ],
)
def test_job_timeout_log_summary(caplog, seconds, expired, expected, fragment):
    # Context
    job_timeout = JobTimeout(seconds, clock=FakeClock())
    if expired:
        job_timeout.expire("wait_for_tests")
    caplog.clear()

    # Act
    with caplog.at_level(logging.INFO):
        result = job_timeout.log_summary()

    # Assert
    assert result is expected
    if fragment is None:
        assert not [r for r in caplog.records if "TIMEOUT" in r.message]
    else:
        assert any(fragment in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# jenkins_generic_job wiring
# ---------------------------------------------------------------------------


def test_timeout_wraps_wait_for_tests(scratch_root, clock, common_mocks):
    # Context
    machine = _make_machine(scratch_root)

    # Mocks
    with mock.patch("CIME.jenkins_generic_job.Timeout") as timeout_context:
        # Act
        result = _call(scratch_root, machine, timeout=42)

    # Assert
    assert result is True
    common_mocks.assert_called_once()
    timeout_context.assert_called_once_with(42, action=mock.ANY)
    timeout_context.return_value.__enter__.assert_called_once()

    # The alarm action must flag the timeout so wait_for_tests stops waiting
    action = timeout_context.call_args.kwargs["action"]
    action(signal.SIGALRM, None)
    assert CIME.wait_for_tests.SIGNAL_RECEIVED is True


def test_timeout_defaults_to_23_hours(scratch_root, clock, common_mocks):
    # Context
    machine = _make_machine(scratch_root)

    # Mocks
    with mock.patch("CIME.jenkins_generic_job.Timeout") as timeout_context:
        # Act
        result = _call(scratch_root, machine)

    # Assert
    assert result is True
    common_mocks.assert_called_once()
    timeout_context.assert_called_once_with(82800, action=mock.ANY)
    timeout_context.return_value.__enter__.assert_called_once()


def test_timeout_zero_disables_timeout(scratch_root, clock, common_mocks, caplog):
    # Context
    machine = _make_machine(scratch_root)

    # Mocks
    with mock.patch(
        "CIME.jenkins_generic_job.Timeout"
    ) as timeout_context, caplog.at_level(logging.INFO):
        # Act
        result = _call(scratch_root, machine, timeout=0)

    # Assert
    assert result is True
    timeout_context.assert_called_once_with(None, action=mock.ANY)
    assert any("job timeout is no timeout" in r.message for r in caplog.records)
    assert CIME.wait_for_tests.SIGNAL_RECEIVED is False


def test_timeout_logs_budget_at_each_stage(scratch_root, clock, common_mocks, caplog):
    # Context
    machine = _make_machine(scratch_root)

    # Mocks
    with caplog.at_level(logging.INFO):
        # Act
        result = _call(scratch_root, machine, timeout=42)

    # Assert
    assert result is True
    messages = [r.message for r in caplog.records if r.message.startswith("TIMEOUT")]
    assert any("job timeout is 42 seconds (00:00:42), deadline" in m for m in messages)
    assert any(
        "starting wait_for_tests with 0s elapsed, 42s remaining of 42s" in m
        for m in messages
    )
    assert any("within its timeout of 42s" in m for m in messages)


def test_timeout_firing_during_wait_for_tests_fails_job(
    scratch_root, clock, common_mocks, caplog
):
    # Context
    machine = _make_machine(scratch_root)

    def fire_alarm_on_enter(seconds, action=None, **_):
        context = mock.MagicMock()
        context.__enter__.side_effect = lambda: action(signal.SIGALRM, None)
        return context

    # Mocks
    with mock.patch(
        "CIME.jenkins_generic_job.Timeout", side_effect=fire_alarm_on_enter
    ), caplog.at_level(logging.INFO):
        # Act
        result = _call(scratch_root, machine, timeout=42)

    # Assert
    assert result is False
    assert CIME.wait_for_tests.SIGNAL_RECEIVED is True
    assert common_mocks.call_args.kwargs["no_wait"] is True
    messages = [r.message for r in caplog.records]
    assert any("exceeded during wait_for_tests" in m for m in messages)
    assert any("reported as FAILED" in m for m in messages)
    assert not any("RECEIVED SIGNAL" in m for m in messages)


def test_timeout_already_expired_before_wait_for_tests(
    scratch_root, clock, common_mocks, caplog
):
    # Context
    machine = _make_machine(scratch_root)
    test_status = f"{scratch_root}/J/case.mymachine_gnu.myexisting123/TestStatus"

    def spend_budget_then_glob(*_):
        # Called right before the pre-wait check, after the budget started at t=0
        clock.now = 100
        return [test_status]

    # Mocks
    with mock.patch(
        "CIME.jenkins_generic_job.Timeout", wraps=jenkins_generic_job.Timeout
    ) as timeout_context, mock.patch(
        "CIME.jenkins_generic_job.glob.glob", side_effect=spend_budget_then_glob
    ), caplog.at_level(
        logging.INFO
    ):
        # Act
        result = _call(scratch_root, machine, timeout=10)

    # Assert
    assert result is False
    assert CIME.wait_for_tests.SIGNAL_RECEIVED is True
    # No alarm is armed once the budget is already spent
    timeout_context.assert_called_once_with(None, action=mock.ANY)
    assert common_mocks.call_args.kwargs["no_wait"] is True
    assert any(
        "exceeded during wait_for_tests after 100s" in r.message for r in caplog.records
    )


def test_create_test_timeout_is_detected_and_fails_job(
    scratch_root, clock, common_mocks, caplog
):
    # Context
    machine = _make_machine(scratch_root)

    def fake_run_cmd(*_, **kwargs):
        # run_cmd only returns once the budget is spent and create_test is killed
        assert kwargs["timeout"] == 10
        clock.now = 10
        return (-signal.SIGTERM, "", "")

    # Mocks
    with mock.patch(
        "CIME.utils.run_cmd", side_effect=fake_run_cmd
    ) as run_cmd, mock.patch(
        "CIME.jenkins_generic_job.threading.Thread"
    ) as thread, caplog.at_level(
        logging.INFO
    ):
        # Act
        result = _call(scratch_root, machine, use_existing_test_id=None, timeout=10)

    # Assert
    assert result is False
    run_cmd.assert_called_once()
    assert CIME.wait_for_tests.SIGNAL_RECEIVED is True
    assert common_mocks.call_args.kwargs["no_wait"] is True
    messages = [r.message for r in caplog.records]
    assert any(
        "starting create_test with 0s elapsed, 10s remaining" in m for m in messages
    )
    assert any("exceeded during create_test after 10s" in m for m in messages)
    assert any("during create_test" in m and "FAILED" in m for m in messages)
    # The archiver is not waited on once we have timed out
    thread.return_value.join.assert_not_called()


def test_create_test_killed_by_signal_before_timeout_is_reported(
    scratch_root, clock, common_mocks, caplog
):
    # Context
    machine = _make_machine(scratch_root)

    def fake_run_cmd(*_, **__):
        clock.now = 3
        return (-signal.SIGKILL, "", "")

    # Mocks
    with mock.patch("CIME.utils.run_cmd", side_effect=fake_run_cmd), mock.patch(
        "CIME.jenkins_generic_job.threading.Thread"
    ), caplog.at_level(logging.INFO):
        # Act
        result = _call(scratch_root, machine, use_existing_test_id=None, timeout=10)

    # Assert
    assert result is True
    assert CIME.wait_for_tests.SIGNAL_RECEIVED is False
    assert any(
        "create_test was terminated by signal SIGKILL after 3s" in r.message
        for r in caplog.records
    )
    assert not any("exceeded during" in r.message for r in caplog.records)


def test_archiver_timeout_is_reported_without_failing_job(
    scratch_root, clock, common_mocks, caplog
):
    # Context
    machine = _make_machine(scratch_root)

    # Mocks
    with mock.patch("CIME.utils.run_cmd", return_value=(0, "", "")), mock.patch(
        "CIME.jenkins_generic_job.threading.Thread"
    ) as thread, caplog.at_level(logging.INFO):
        # Simulate the archiver alarm firing while blocked in join()
        thread.return_value.join.side_effect = RuntimeError(
            "Timeout 'archiver wait' of 10 expired"
        )

        # Act
        result = _call(scratch_root, machine, use_existing_test_id=None, timeout=10)

    # Assert
    assert result is True
    thread.return_value.join.assert_called_once()
    messages = [r.message for r in caplog.records]
    assert any(
        "starting archiver wait with 0s elapsed, 10s remaining" in m for m in messages
    )
    assert any("gave up waiting for the archiver thread" in m for m in messages)
    assert any("within its timeout of 10s" in m for m in messages)
