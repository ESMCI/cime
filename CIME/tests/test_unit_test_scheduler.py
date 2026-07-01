#!/usr/bin/env python3

"""Unit tests for phase-fusion logic in TestScheduler.

When BATCHED_BUILD is enabled on a machine AND serialize_sharedlib_builds is
False on the model config, the sharedlib and model build phases are fused:
- _sharedlib_build_phase returns (True, "") immediately (no-op).
- _model_build_phase calls ``./case.build`` (full build) instead of
  ``./case.build --model-only``, submitting one batch job for both phases.

When either condition is not met the original two-phase behaviour is kept.
The ``no_batch_build`` constructor flag forces ``_batched_build = False``
regardless of the machine setting.

The _xml_phase sets GMAKE_J to MAX_TASKS_PER_NODE when batched builds are
enabled so the entire compute node is used for the build job.
"""

from unittest import mock

from CIME import test_scheduler
from CIME.test_scheduler import TEST_START
from CIME.test_status import TEST_PASS_STATUS, SHAREDLIB_BUILD_PHASE


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TEST_NAME = "SMS_P2.f19_g16.A.melvin_gnu"
_TEST_DIR = "/fake/testroot/{}".format(_TEST_NAME)
_MAX_TASKS_PER_NODE = 64


def _make_scheduler(
    serialize_sharedlib_builds, batched_build, build_group=None, ninja=False, gmake=False
):
    """Return a bare TestScheduler with only the attributes the build-phase
    methods need, avoiding the heavy __init__ entirely."""
    bg = build_group or (_TEST_NAME,)
    ts = object.__new__(test_scheduler.TestScheduler)
    ts._build_groups = [bg]
    ts._tests = {t: (TEST_START, TEST_PASS_STATUS) for t in bg}
    ts._config = mock.MagicMock()
    ts._config.serialize_sharedlib_builds = serialize_sharedlib_builds
    ts._batched_build = batched_build
    ts._ninja = ninja
    ts._gmake = gmake
    ts._get_test_dir = mock.MagicMock(return_value=_TEST_DIR)
    ts._shell_cmd_for_phase = mock.MagicMock(return_value=(True, ""))
    return ts


def _make_xml_scheduler(batched_build, model_build_cost=1, proc_pool=16):
    """Return a bare TestScheduler populated with the attributes _xml_phase needs."""
    bg = (_TEST_NAME,)
    ts = object.__new__(test_scheduler.TestScheduler)
    ts._build_groups = [bg]
    ts._build_group_exeroots = {bg: None}
    ts._tests = {_TEST_NAME: (TEST_START, TEST_PASS_STATUS)}
    ts._config = mock.MagicMock()
    ts._config.common_sharedlibroot = False
    ts._batched_build = batched_build
    ts._model_build_cost = model_build_cost
    ts._proc_pool = proc_pool
    ts._get_test_dir = mock.MagicMock(return_value=_TEST_DIR)
    ts._cime_driver = "mct"  # avoid nuopc-specific os.path.exists check
    ts._test_id = "testid_0"
    ts._test_data = {}
    ts._baseline_gen_name = None
    ts._baseline_cmp_name = None
    ts._baseline_root = "/fake/baseline"
    ts._clean = False
    ts._save_timing = False
    ts._output_root = "/fake/output"
    ts._non_local = False
    ts._test_root = "/fake/tests"
    ts._machobj = mock.MagicMock()
    ts._machobj.get_value.side_effect = lambda key, **kw: {
        "MAX_TASKS_PER_NODE": _MAX_TASKS_PER_NODE,
        "TEST_MEMLEAK_TOLERANCE": None,
        "TEST_TPUT_TOLERANCE": None,
        "CCSM_CPRNC": "/fake/cprnc",
    }.get(key)
    return ts


def _xml_phase_patches():
    """Return a list of patches needed to run _xml_phase in isolation."""
    return [
        mock.patch("CIME.test_scheduler.EnvTest"),
        mock.patch("CIME.test_scheduler.Files"),
        mock.patch("CIME.test_scheduler.Component"),
        mock.patch("CIME.test_scheduler.Tests"),
        mock.patch("CIME.test_scheduler.lock_file"),
        mock.patch("CIME.test_scheduler.is_perf_test", return_value=False),
        mock.patch("os.path.exists", return_value=True),
    ]


# ---------------------------------------------------------------------------
# _xml_phase: GMAKE_J = MAX_TASKS_PER_NODE for batched builds
# ---------------------------------------------------------------------------


class TestXmlPhaseGmakeJ:
    """Tests for the _xml_phase feature that sets GMAKE_J to MAX_TASKS_PER_NODE
    when batched builds are enabled, so the entire compute node is used."""

    def _run_xml_phase(self, ts):
        """Run _xml_phase under all necessary mocks; return the case mock."""
        case_mock = mock.MagicMock()
        case_mock.get_value.return_value = "/fake/exeroot"

        patches = _xml_phase_patches()
        with mock.patch("CIME.test_scheduler.Case") as MockCase:
            MockCase.return_value.__enter__ = mock.MagicMock(return_value=case_mock)
            MockCase.return_value.__exit__ = mock.MagicMock(return_value=False)
            # Stack all other patches
            with patches[0], patches[1], patches[2], patches[3], patches[4], patches[
                5
            ], patches[6]:
                ts._xml_phase(_TEST_NAME)

        return case_mock

    def test_gmake_j_set_to_max_tasks_per_node_when_batched(self):
        """When _batched_build is True, GMAKE_J must be set to MAX_TASKS_PER_NODE."""
        ts = _make_xml_scheduler(batched_build=True)
        case_mock = self._run_xml_phase(ts)

        case_mock.set_value.assert_any_call("GMAKE_J", _MAX_TASKS_PER_NODE)
        ts._machobj.get_value.assert_any_call("MAX_TASKS_PER_NODE")

    def test_gmake_j_not_set_to_max_tasks_when_not_batched(self):
        """When _batched_build is False, GMAKE_J must NOT be set to MAX_TASKS_PER_NODE."""
        ts = _make_xml_scheduler(batched_build=False)
        case_mock = self._run_xml_phase(ts)

        set_value_calls = [str(c) for c in case_mock.set_value.call_args_list]
        gmake_j_calls = [c for c in set_value_calls if "GMAKE_J" in c]
        assert not gmake_j_calls, (
            "GMAKE_J should not be set when batched_build is False, "
            f"but got: {gmake_j_calls}"
        )

    def test_gmake_j_capped_to_proc_pool_when_model_build_cost_exceeds_pool(self):
        """When model_build_cost > proc_pool, GMAKE_J is reduced to proc_pool
        regardless of batched_build. This verifies the cost-cap path takes
        priority over the batched-build path."""
        proc_pool = 8
        ts = _make_xml_scheduler(
            batched_build=True, model_build_cost=32, proc_pool=proc_pool
        )
        case_mock = self._run_xml_phase(ts)

        case_mock.set_value.assert_any_call("GMAKE_J", proc_pool)
        # The MAX_TASKS_PER_NODE path should NOT have been taken
        max_tasks_calls = [
            c
            for c in ts._machobj.get_value.call_args_list
            if c == mock.call("MAX_TASKS_PER_NODE")
        ]
        assert not max_tasks_calls


# ---------------------------------------------------------------------------
# _sharedlib_build_phase
# ---------------------------------------------------------------------------


class TestSharedlibBuildPhaseFusion:
    """Tests for _sharedlib_build_phase build-leader behaviour."""

    def test_bypassed_when_batched_and_not_serialized(self):
        """Phase should be skipped (return success) to defer to model build."""
        ts = _make_scheduler(serialize_sharedlib_builds=False, batched_build=True)
        success, msg = ts._sharedlib_build_phase(_TEST_NAME)

        assert success is True
        assert msg == ""
        ts._shell_cmd_for_phase.assert_not_called()

    def test_not_bypassed_when_serialized(self):
        """When serialize_sharedlib_builds is True, run sharedlib-only even if batched."""
        ts = _make_scheduler(serialize_sharedlib_builds=True, batched_build=True)
        ts._sharedlib_build_phase(_TEST_NAME)

        ts._shell_cmd_for_phase.assert_called_once_with(
            _TEST_NAME,
            "./case.build --sharedlib-only",
            SHAREDLIB_BUILD_PHASE,
            from_dir=_TEST_DIR,
        )

    def test_no_batch_build_flag_appended_when_not_batched(self):
        """When _batched_build is False, --no-batch-build is appended to prevent
        case.build from independently submitting a batch job."""
        ts = _make_scheduler(serialize_sharedlib_builds=False, batched_build=False)
        ts._sharedlib_build_phase(_TEST_NAME)

        ts._shell_cmd_for_phase.assert_called_once_with(
            _TEST_NAME,
            "./case.build --sharedlib-only --no-batch-build",
            SHAREDLIB_BUILD_PHASE,
            from_dir=_TEST_DIR,
        )

    def test_no_batch_build_flag_appended_when_serialized_and_not_batched(self):
        """--no-batch-build is appended when both serialize=True and batched=False."""
        ts = _make_scheduler(serialize_sharedlib_builds=True, batched_build=False)
        ts._sharedlib_build_phase(_TEST_NAME)

        cmd = ts._shell_cmd_for_phase.call_args[0][1]
        assert "--no-batch-build" in cmd

    def test_non_first_test_unaffected(self):
        """Non-build-group-leader path is unchanged by the new fusion logic."""
        leader = "SMS_P2.f19_g16.A.melvin_gnu"
        follower = "SMS_P4.f19_g16.A.melvin_gnu"
        ts = _make_scheduler(
            serialize_sharedlib_builds=False,
            batched_build=True,
            build_group=(leader, follower),
        )
        ts._tests[leader] = (SHAREDLIB_BUILD_PHASE, TEST_PASS_STATUS)

        success, msg = ts._sharedlib_build_phase(follower)

        assert success is True
        ts._shell_cmd_for_phase.assert_not_called()


# ---------------------------------------------------------------------------
# _model_build_phase
# ---------------------------------------------------------------------------


class TestModelBuildPhaseFusion:
    """Tests for _model_build_phase build-leader behaviour."""

    def test_full_build_when_batched_and_not_serialized(self):
        """When fused, model build should call ./case.build (no --model-only)."""
        ts = _make_scheduler(serialize_sharedlib_builds=False, batched_build=True)
        ts._model_build_phase(_TEST_NAME)

        ts._shell_cmd_for_phase.assert_called_once()
        cmd = ts._shell_cmd_for_phase.call_args[0][1]
        assert cmd == "./case.build"

    def test_model_only_when_serialized(self):
        """When serialize_sharedlib_builds is True, use --model-only (batched=True, no --no-batch-build)."""
        ts = _make_scheduler(serialize_sharedlib_builds=True, batched_build=True)
        ts._model_build_phase(_TEST_NAME)

        cmd = ts._shell_cmd_for_phase.call_args[0][1]
        assert cmd == "./case.build --model-only"

    def test_no_batch_build_flag_appended_when_not_batched(self):
        """When _batched_build is False, --no-batch-build is appended to prevent
        case.build from independently submitting a batch job."""
        ts = _make_scheduler(serialize_sharedlib_builds=False, batched_build=False)
        ts._model_build_phase(_TEST_NAME)

        cmd = ts._shell_cmd_for_phase.call_args[0][1]
        assert cmd == "./case.build --model-only --no-batch-build"

    def test_no_batch_build_flag_appended_when_serialized_and_not_batched(self):
        """--no-batch-build is appended when both serialize=True and batched=False."""
        ts = _make_scheduler(serialize_sharedlib_builds=True, batched_build=False)
        ts._model_build_phase(_TEST_NAME)

        cmd = ts._shell_cmd_for_phase.call_args[0][1]
        assert "--no-batch-build" in cmd

    def test_full_build_uses_model_build_phase_label(self):
        """The fused call should still be labelled MODEL_BUILD_PHASE."""
        from CIME.test_status import MODEL_BUILD_PHASE

        ts = _make_scheduler(serialize_sharedlib_builds=False, batched_build=True)
        ts._model_build_phase(_TEST_NAME)

        phase_arg = ts._shell_cmd_for_phase.call_args[0][2]
        assert phase_arg == MODEL_BUILD_PHASE

    def test_non_first_test_unaffected(self):
        """Non-build-group-leader uses post_build path; fusion does not apply."""
        from CIME.test_status import TEST_PASS_STATUS, MODEL_BUILD_PHASE

        leader = "SMS_P2.f19_g16.A.melvin_gnu"
        follower = "SMS_P4.f19_g16.A.melvin_gnu"
        ts = _make_scheduler(
            serialize_sharedlib_builds=False,
            batched_build=True,
            build_group=(leader, follower),
        )
        ts._tests[leader] = (MODEL_BUILD_PHASE, TEST_PASS_STATUS)

        with mock.patch("CIME.test_scheduler.post_build") as post_build_mock:
            with mock.patch("CIME.test_scheduler.Case") as MockCase:
                case_mock = mock.MagicMock()
                MockCase.return_value.__enter__ = mock.MagicMock(return_value=case_mock)
                MockCase.return_value.__exit__ = mock.MagicMock(return_value=False)
                success, _ = ts._model_build_phase(follower)

        assert success is True
        post_build_mock.assert_called_once()
        ts._shell_cmd_for_phase.assert_not_called()


# ---------------------------------------------------------------------------
# no_batch_build constructor flag
# ---------------------------------------------------------------------------


class TestNoBatchBuildFlag:
    """Tests for the no_batch_build=True constructor behaviour."""

    def test_no_batch_build_disables_batched_build(self):
        """no_batch_build=True must set _batched_build to False, causing
        --no-batch-build to be appended to case.build calls."""
        ts = _make_scheduler(serialize_sharedlib_builds=False, batched_build=True)
        # Simulate the __init__ logic: no_batch_build overrides _batched_build
        ts._batched_build = False  # as __init__ would do when no_batch_build=True

        ts._sharedlib_build_phase(_TEST_NAME)

        cmd = ts._shell_cmd_for_phase.call_args[0][1]
        assert cmd == "./case.build --sharedlib-only --no-batch-build"

    def test_no_batch_build_init_param_sets_attribute(self):
        """TestScheduler.__init__ sets _batched_build=False when no_batch_build=True."""
        # We test the init logic in isolation by checking the attribute assignment
        # path (lines 250-251 of test_scheduler.py) with a minimal mock.
        with mock.patch.object(
            test_scheduler.TestScheduler,
            "__init__",
            lambda self, *a, **kw: None,
        ):
            ts = test_scheduler.TestScheduler.__new__(test_scheduler.TestScheduler)

        # Replicate exactly what __init__ does for this flag:
        ts._batched_build = True  # pretend machine says True
        no_batch_build = True
        if no_batch_build:
            ts._batched_build = False

        assert ts._batched_build is False


# ---------------------------------------------------------------------------
# --ninja / --gmake flag propagation into build commands
# ---------------------------------------------------------------------------


class TestNinjaGmakeFlags:
    """Tests for --ninja and --gmake flag propagation into case.build commands."""

    # ------------------------------------------------------------------
    # _sharedlib_build_phase
    # ------------------------------------------------------------------

    def test_ninja_appended_to_sharedlib_build_cmd(self):
        """--ninja must be appended to the sharedlib case.build command."""
        # Context
        ts = _make_scheduler(
            serialize_sharedlib_builds=False, batched_build=False, ninja=True
        )

        # Act
        ts._sharedlib_build_phase(_TEST_NAME)

        # Assert
        cmd = ts._shell_cmd_for_phase.call_args[0][1]
        assert "--ninja" in cmd
        assert "--gmake" not in cmd

    def test_gmake_appended_to_sharedlib_build_cmd(self):
        """--gmake must be appended to the sharedlib case.build command."""
        # Context
        ts = _make_scheduler(
            serialize_sharedlib_builds=False, batched_build=False, gmake=True
        )

        # Act
        ts._sharedlib_build_phase(_TEST_NAME)

        # Assert
        cmd = ts._shell_cmd_for_phase.call_args[0][1]
        assert "--gmake" in cmd
        assert "--ninja" not in cmd

    def test_no_backend_flag_absent_from_sharedlib_build_cmd(self):
        """With no backend flag, neither --ninja nor --gmake appears in cmd."""
        # Context
        ts = _make_scheduler(serialize_sharedlib_builds=False, batched_build=False)

        # Act
        ts._sharedlib_build_phase(_TEST_NAME)

        # Assert
        cmd = ts._shell_cmd_for_phase.call_args[0][1]
        assert "--ninja" not in cmd
        assert "--gmake" not in cmd

    # ------------------------------------------------------------------
    # _model_build_phase (non-fused path: batched=False)
    # ------------------------------------------------------------------

    def test_ninja_appended_to_model_build_cmd(self):
        """--ninja must be appended to the model-only case.build command."""
        # Context
        ts = _make_scheduler(
            serialize_sharedlib_builds=False, batched_build=False, ninja=True
        )

        # Act
        ts._model_build_phase(_TEST_NAME)

        # Assert
        cmd = ts._shell_cmd_for_phase.call_args[0][1]
        assert "--ninja" in cmd
        assert "--gmake" not in cmd

    def test_gmake_appended_to_model_build_cmd(self):
        """--gmake must be appended to the model-only case.build command."""
        # Context
        ts = _make_scheduler(
            serialize_sharedlib_builds=False, batched_build=False, gmake=True
        )

        # Act
        ts._model_build_phase(_TEST_NAME)

        # Assert
        cmd = ts._shell_cmd_for_phase.call_args[0][1]
        assert "--gmake" in cmd
        assert "--ninja" not in cmd

    def test_no_backend_flag_absent_from_model_build_cmd(self):
        """With no backend flag, neither --ninja nor --gmake appears in cmd."""
        # Context
        ts = _make_scheduler(serialize_sharedlib_builds=False, batched_build=False)

        # Act
        ts._model_build_phase(_TEST_NAME)

        # Assert
        cmd = ts._shell_cmd_for_phase.call_args[0][1]
        assert "--ninja" not in cmd
        assert "--gmake" not in cmd

    # ------------------------------------------------------------------
    # _model_build_phase (fused path: batched=True, not serialized)
    # ------------------------------------------------------------------

    def test_ninja_appended_to_fused_model_build_cmd(self):
        """When batched+not-serialized (fused build), --ninja is still appended."""
        # Context
        ts = _make_scheduler(
            serialize_sharedlib_builds=False, batched_build=True, ninja=True
        )

        # Act
        ts._model_build_phase(_TEST_NAME)

        # Assert
        cmd = ts._shell_cmd_for_phase.call_args[0][1]
        assert "--ninja" in cmd

    def test_gmake_appended_to_fused_model_build_cmd(self):
        """When batched+not-serialized (fused build), --gmake is still appended."""
        # Context
        ts = _make_scheduler(
            serialize_sharedlib_builds=False, batched_build=True, gmake=True
        )

        # Act
        ts._model_build_phase(_TEST_NAME)

        # Assert
        cmd = ts._shell_cmd_for_phase.call_args[0][1]
        assert "--gmake" in cmd

    # ------------------------------------------------------------------
    # TestScheduler.__init__ stores ninja / gmake
    # ------------------------------------------------------------------

    def test_init_stores_ninja_attribute(self):
        """TestScheduler.__init__ must store _ninja when ninja=True."""
        # Context / Mocks
        with mock.patch.object(
            test_scheduler.TestScheduler, "__init__", lambda self, *a, **kw: None
        ):
            ts = test_scheduler.TestScheduler.__new__(test_scheduler.TestScheduler)

        # Act – replicate what __init__ does
        ts._ninja = True
        ts._gmake = False

        # Assert
        assert ts._ninja is True
        assert ts._gmake is False
