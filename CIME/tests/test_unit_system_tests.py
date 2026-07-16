#!/usr/bin/env python3

import os
import tempfile
import gzip
import re
from re import A
from unittest import mock
from pathlib import Path

from CIME.config import Config
from CIME.SystemTests.system_tests_common import (
    SystemTestsCommon,
    _format_elapsed_model_time,
    _days_in_month,
)
from CIME.SystemTests.system_tests_compare_two import SystemTestsCompareTwo
from CIME.SystemTests.system_tests_compare_n import SystemTestsCompareN

CPLLOG = """
 tStamp_write: model date =   00010102       0 wall clock = 2023-09-19 19:39:42 avg dt =     0.33 dt =     0.33
 memory_write: model date =   00010102       0 memory =    1673.89 MB (highwater)        387.77 MB (usage)  (pe=    0 comps= cpl ATM LND ICE OCN GLC ROF WAV IAC ESP)
 tStamp_write: model date =   00010103       0 wall clock = 2023-09-19 19:39:42 avg dt =     0.33 dt =     0.33
 memory_write: model date =   00010103       0 memory =    1673.89 MB (highwater)        390.09 MB (usage)  (pe=    0 comps= cpl ATM LND ICE OCN GLC ROF WAV IAC ESP)
 tStamp_write: model date =   00010104       0 wall clock = 2023-09-19 19:39:42 avg dt =     0.33 dt =     0.33
 memory_write: model date =   00010104       0 memory =    1673.89 MB (highwater)        391.64 MB (usage)  (pe=    0 comps= cpl ATM LND ICE OCN GLC ROF WAV IAC ESP)
 tStamp_write: model date =   00010105       0 wall clock = 2023-09-19 19:39:43 avg dt =     0.33 dt =     0.33
 memory_write: model date =   00010105       0 memory =    1673.89 MB (highwater)        392.67 MB (usage)  (pe=    0 comps= cpl ATM LND ICE OCN GLC ROF WAV IAC ESP)
 tStamp_write: model date =   00010106       0 wall clock = 2023-09-19 19:39:43 avg dt =     0.33 dt =     0.33
 memory_write: model date =   00010106       0 memory =    1673.89 MB (highwater)        393.44 MB (usage)  (pe=    0 comps= cpl ATM LND ICE OCN GLC ROF WAV IAC ESP)

(seq_mct_drv): ===============          SUCCESSFUL TERMINATION OF CPL7-e3sm ===============
(seq_mct_drv): ===============        at YMD,TOD =   00010106       0       ===============
(seq_mct_drv): ===============  # simulated days (this run) =        5.000  ===============
(seq_mct_drv): ===============  compute time (hrs)          =        0.000  ===============
(seq_mct_drv): ===============  # simulated years / cmp-day =      719.635  ===============
(seq_mct_drv): ===============  pes min memory highwater  (MB)     851.957  ===============
(seq_mct_drv): ===============  pes max memory highwater  (MB)    1673.891  ===============
(seq_mct_drv): ===============  pes min memory last usage (MB)     182.742  ===============
(seq_mct_drv): ===============  pes max memory last usage (MB)     393.441  ===============
"""


def setup_generate_baseline_mock(tempdir):
    """Set up a mock case for _generate_baseline tests, returning (case, baseline_root)."""
    case, caseroot, baseline_root, run_dir = create_mock_case(
        tempdir, cpllog_data=CPLLOG
    )

    get_value_calls = [
        str(caseroot),
        "ERIO.ne30_g16.A.docker_gnu",
        "mct",
        None,
        str(run_dir),
        "case.std",
        str(baseline_root),
        "master/ERIO.ne30_g16.A.docker_gnu",
        "ERIO.ne30_g16.A.docker_gnu.G.20230919_193255_z9hg2w",
        "ERIO",
        "mct",
        str(run_dir),
        "ERIO",
        "ERIO.ne30_g16.A.docker_gnu",
        "master/ERIO.ne30_g16.A.docker_gnu",
        str(baseline_root),
        "master/ERIO.ne30_g16.A.docker_gnu",
        str(run_dir),
        "mct",
        "/tmp/components/cpl",
        str(run_dir),
        "mct",
        str(run_dir),
        "mct",
    ]

    if Config.instance().create_bless_log:
        get_value_calls.insert(12, os.getcwd())

    case.get_value.side_effect = get_value_calls

    return case, baseline_root


def create_mock_case(tempdir, idx=None, cpllog_data=None):
    if idx is None:
        idx = 0

    case = mock.MagicMock()

    caseroot = Path(tempdir, str(idx), "caseroot")
    baseline_root = caseroot.parent / "baselines"
    run_dir = caseroot / "run"
    run_dir.mkdir(parents=True, exist_ok=False)

    if cpllog_data is not None:
        cpllog = run_dir / "cpl.log.gz"

        with gzip.open(cpllog, "w") as fd:
            fd.write(cpllog_data.encode("utf-8"))

        case.get_latest_cpl_log.return_value = str(cpllog)

    hist_file = run_dir / "cpl.hi.2023-01-01.nc"
    hist_file.touch()

    case.get_env.return_value.get_latest_hist_files.return_value = [str(hist_file)]

    case.get_compset_components.return_value = []

    return case, caseroot, baseline_root, run_dir


class TestUnitSystemTests:
    @mock.patch("CIME.SystemTests.system_tests_common.load_coupler_customization")
    @mock.patch("CIME.SystemTests.system_tests_common.append_testlog")
    @mock.patch("CIME.SystemTests.system_tests_common.perf_get_memory_list")
    @mock.patch("CIME.SystemTests.system_tests_common.get_latest_cpl_logs")
    def test_check_for_memleak_runtime_error(
        self,
        get_latest_cpl_logs,
        perf_get_memory_list,
        append_testlog,
        load_coupler_customization,
    ):
        load_coupler_customization.return_value.perf_check_for_memory_leak.side_effect = (
            AttributeError
        )

        perf_get_memory_list.side_effect = RuntimeError

        with tempfile.TemporaryDirectory() as tempdir:
            caseroot = Path(tempdir) / "caseroot"
            caseroot.mkdir(parents=True, exist_ok=False)

            rundir = caseroot / "run"
            rundir.mkdir(parents=True, exist_ok=False)

            cpllog = rundir / "cpl.log.gz"

            get_latest_cpl_logs.return_value = [
                str(cpllog),
            ]

            case = mock.MagicMock()
            case.get_value.side_effect = (
                str(caseroot),
                "ERIO.ne30_g16.A.docker_gnu",
                "mct",
                "rpointer.cpl",
                0.01,
            )

            common = SystemTestsCommon(case)

            common._test_status = mock.MagicMock()

            common._check_for_memleak()

            common._test_status.set_status.assert_any_call(
                "MEMLEAK", "PASS", comments="insufficient data for memleak test"
            )

            append_testlog.assert_not_called()

    @mock.patch("CIME.SystemTests.system_tests_common.load_coupler_customization")
    @mock.patch("CIME.SystemTests.system_tests_common.append_testlog")
    @mock.patch("CIME.SystemTests.system_tests_common.perf_get_memory_list")
    @mock.patch("CIME.SystemTests.system_tests_common.get_latest_cpl_logs")
    def test_check_for_memleak_not_enough_samples(
        self,
        get_latest_cpl_logs,
        perf_get_memory_list,
        append_testlog,
        load_coupler_customization,
    ):
        load_coupler_customization.return_value.perf_check_for_memory_leak.side_effect = (
            AttributeError
        )

        perf_get_memory_list.return_value = [
            (10102, 1000.0),  # year 1, Jan 2
            (10104, 0),  # year 1, Jan 4  (originalmem=0 → insufficient data)
        ]

        with tempfile.TemporaryDirectory() as tempdir:
            caseroot = Path(tempdir) / "caseroot"
            caseroot.mkdir(parents=True, exist_ok=False)

            rundir = caseroot / "run"
            rundir.mkdir(parents=True, exist_ok=False)

            cpllog = rundir / "cpl.log.gz"

            get_latest_cpl_logs.return_value = [
                str(cpllog),
            ]

            case = mock.MagicMock()
            case.get_value.side_effect = (
                str(caseroot),
                "ERIO.ne30_g16.A.docker_gnu",
                "mct",
                None,
                0.01,
            )

            common = SystemTestsCommon(case)

            common._test_status = mock.MagicMock()

            common._check_for_memleak()

            common._test_status.set_status.assert_any_call(
                "MEMLEAK", "PASS", comments="data for memleak test is insufficient"
            )

            append_testlog.assert_not_called()

    @mock.patch("CIME.SystemTests.system_tests_common.load_coupler_customization")
    @mock.patch("CIME.SystemTests.system_tests_common.append_testlog")
    @mock.patch("CIME.SystemTests.system_tests_common.perf_get_memory_list")
    @mock.patch("CIME.SystemTests.system_tests_common.get_latest_cpl_logs")
    def test_check_for_memleak_found(
        self,
        get_latest_cpl_logs,
        perf_get_memory_list,
        append_testlog,
        load_coupler_customization,
    ):
        load_coupler_customization.return_value.perf_check_for_memory_leak.side_effect = (
            AttributeError
        )

        perf_get_memory_list.return_value = [
            (10102, 1000.0),  # year 1, Jan 2  – skipped (init sample)
            (10104, 2000.0),  # year 1, Jan 4  – originalmem
            (10106, 3000.0),  # year 1, Jan 6
            (10108, 3000.0),  # year 1, Jan 8  – finalmem  (memdiff = 0.5 > tol)
        ]

        with tempfile.TemporaryDirectory() as tempdir:
            caseroot = Path(tempdir) / "caseroot"
            caseroot.mkdir(parents=True, exist_ok=False)

            rundir = caseroot / "run"
            rundir.mkdir(parents=True, exist_ok=False)

            cpllog = rundir / "cpl.log.gz"

            get_latest_cpl_logs.return_value = [
                str(cpllog),
            ]

            case = mock.MagicMock()
            case.get_value.side_effect = (
                str(caseroot),
                "ERIO.ne30_g16.A.docker_gnu",
                "mct",
                None,
                0.01,
                "GREGORIAN",  # CALENDAR, consumed only when a leak is found
            )

            common = SystemTestsCommon(case)

            common._test_status = mock.MagicMock()

            common._check_for_memleak()

            expected_comment = "memleak detected, memory went from 2000.000000 to 3000.000000 in 4 days"

            common._test_status.set_status.assert_any_call(
                "MEMLEAK", "FAIL", comments=expected_comment
            )

            append_testlog.assert_any_call(expected_comment, str(caseroot))

    @mock.patch("CIME.SystemTests.system_tests_common.load_coupler_customization")
    @mock.patch("CIME.SystemTests.system_tests_common.append_testlog")
    @mock.patch("CIME.SystemTests.system_tests_common.perf_get_memory_list")
    @mock.patch("CIME.SystemTests.system_tests_common.get_latest_cpl_logs")
    def test_check_for_memleak(
        self,
        get_latest_cpl_logs,
        perf_get_memory_list,
        append_testlog,
        load_coupler_customization,
    ):
        load_coupler_customization.return_value.perf_check_for_memory_leak.side_effect = (
            AttributeError
        )

        perf_get_memory_list.return_value = [
            (10102, 3040.0),  # year 1, Jan 2  – skipped (init sample)
            (10104, 3002.0),  # year 1, Jan 4  – originalmem
            (10106, 3030.0),  # year 1, Jan 6
            (10108, 3008.0),  # year 1, Jan 8  – finalmem  (memdiff ≈ 0.002 < tol)
        ]

        with tempfile.TemporaryDirectory() as tempdir:
            caseroot = Path(tempdir) / "caseroot"
            caseroot.mkdir(parents=True, exist_ok=False)

            rundir = caseroot / "run"
            rundir.mkdir(parents=True, exist_ok=False)

            cpllog = rundir / "cpl.log.gz"

            get_latest_cpl_logs.return_value = [
                str(cpllog),
            ]

            case = mock.MagicMock()
            case.get_value.side_effect = (
                str(caseroot),
                "ERIO.ne30_g16.A.docker_gnu",
                "mct",
                None,
                0.01,
            )

            common = SystemTestsCommon(case)

            common._test_status = mock.MagicMock()

            common._check_for_memleak()

            common._test_status.set_status.assert_any_call(
                "MEMLEAK", "PASS", comments=""
            )

            append_testlog.assert_not_called()

    @mock.patch("CIME.SystemTests.system_tests_common.perf_compare_throughput_baseline")
    @mock.patch("CIME.SystemTests.system_tests_common.append_testlog")
    def test_compare_throughput(self, append_testlog, perf_compare_throughput_baseline):
        perf_compare_throughput_baseline.return_value = (
            True,
            "TPUTCOMP: Computation time changed by 2.00% relative to baseline",
        )

        with tempfile.TemporaryDirectory() as tempdir:
            caseroot = Path(tempdir) / "caseroot"
            caseroot.mkdir(parents=True, exist_ok=False)

            case = mock.MagicMock()
            case.get_value.side_effect = (
                str(Path(tempdir) / "caseroot"),
                "ERIO.ne30_g16.A.docker_gnu",
                "mct",
                None,
            )

            common = SystemTestsCommon(case)

            common._compare_throughput()

        assert common._test_status.get_overall_test_status() == ("PASS", None)

        append_testlog.assert_any_call(
            "TPUTCOMP: Computation time changed by 2.00% relative to baseline",
            str(caseroot),
        )

    @mock.patch("CIME.SystemTests.system_tests_common.perf_compare_throughput_baseline")
    @mock.patch("CIME.SystemTests.system_tests_common.append_testlog")
    def test_compare_throughput_error_diff(
        self, append_testlog, perf_compare_throughput_baseline
    ):
        perf_compare_throughput_baseline.return_value = (None, "Error diff value")

        with tempfile.TemporaryDirectory() as tempdir:
            caseroot = Path(tempdir) / "caseroot"
            caseroot.mkdir(parents=True, exist_ok=False)

            case = mock.MagicMock()
            case.get_value.side_effect = (
                str(Path(tempdir) / "caseroot"),
                "ERIO.ne30_g16.A.docker_gnu",
                "mct",
                "rpointer.cpl.0001-01-01",
            )

            common = SystemTestsCommon(case)

            common._compare_throughput()

        assert common._test_status.get_overall_test_status() == ("PASS", None)

        append_testlog.assert_not_called()

    @mock.patch("CIME.SystemTests.system_tests_common.perf_compare_throughput_baseline")
    @mock.patch("CIME.SystemTests.system_tests_common.append_testlog")
    def test_compare_throughput_fail(
        self, append_testlog, perf_compare_throughput_baseline
    ):
        perf_compare_throughput_baseline.return_value = (
            False,
            "Error: TPUTCOMP: Computation time increase > 5% from baseline",
        )

        with tempfile.TemporaryDirectory() as tempdir:
            caseroot = Path(tempdir) / "caseroot"
            caseroot.mkdir(parents=True, exist_ok=False)

            case = mock.MagicMock()
            case.get_value.side_effect = (
                str(Path(tempdir) / "caseroot"),
                "ERIO.ne30_g16.A.docker_gnu",
                "mct",
                None,
            )

            common = SystemTestsCommon(case)

            common._compare_throughput()

        assert common._test_status.get_overall_test_status() == ("PASS", None)

        append_testlog.assert_any_call(
            "Error: TPUTCOMP: Computation time increase > 5% from baseline",
            str(caseroot),
        )

    @mock.patch("CIME.SystemTests.system_tests_common.perf_compare_memory_baseline")
    @mock.patch("CIME.SystemTests.system_tests_common.append_testlog")
    def test_compare_memory(self, append_testlog, perf_compare_memory_baseline):
        perf_compare_memory_baseline.return_value = (
            True,
            "MEMCOMP: Memory usage highwater has changed by 2.00% relative to baseline",
        )

        with tempfile.TemporaryDirectory() as tempdir:
            caseroot = Path(tempdir) / "caseroot"
            caseroot.mkdir(parents=True, exist_ok=False)

            case = mock.MagicMock()
            case.get_value.side_effect = (
                str(caseroot),
                "ERIO.ne30_g16.A.docker_gnu",
                "mct",
                "rpointer.cpl",
            )

            common = SystemTestsCommon(case)

            common._compare_memory()

        assert common._test_status.get_overall_test_status() == ("PASS", None)

        append_testlog.assert_any_call(
            "MEMCOMP: Memory usage highwater has changed by 2.00% relative to baseline",
            str(caseroot),
        )

    @mock.patch("CIME.SystemTests.system_tests_common.perf_compare_memory_baseline")
    @mock.patch("CIME.SystemTests.system_tests_common.append_testlog")
    def test_compare_memory_error_diff(
        self, append_testlog, perf_compare_memory_baseline
    ):
        perf_compare_memory_baseline.return_value = (None, "Error diff value")

        with tempfile.TemporaryDirectory() as tempdir:
            caseroot = Path(tempdir) / "caseroot"
            caseroot.mkdir(parents=True, exist_ok=False)

            case = mock.MagicMock()
            case.get_value.side_effect = (
                str(caseroot),
                "ERIO.ne30_g16.A.docker_gnu",
                "mct",
                None,
            )

            common = SystemTestsCommon(case)

            common._compare_memory()

        assert common._test_status.get_overall_test_status() == ("PASS", None)

        append_testlog.assert_not_called()

    @mock.patch("CIME.SystemTests.system_tests_common.perf_compare_memory_baseline")
    @mock.patch("CIME.SystemTests.system_tests_common.append_testlog")
    def test_compare_memory_error_fail(
        self, append_testlog, perf_compare_memory_baseline
    ):
        perf_compare_memory_baseline.return_value = (
            False,
            "Error: Memory usage increase >5% from baseline's 1000.000000 to 1002.000000",
        )

        with tempfile.TemporaryDirectory() as tempdir:
            caseroot = Path(tempdir) / "caseroot"
            caseroot.mkdir(parents=True, exist_ok=False)

            case = mock.MagicMock()
            case.get_value.side_effect = (
                str(caseroot),
                "ERIO.ne30_g16.A.docker_gnu",
                "mct",
                "rpointer.cpl",
            )

            common = SystemTestsCommon(case)

            common._compare_memory()

        assert common._test_status.get_overall_test_status() == ("PASS", None)

        append_testlog.assert_any_call(
            "Error: Memory usage increase >5% from baseline's 1000.000000 to 1002.000000",
            str(caseroot),
        )

    def test_generate_baseline(self):
        with tempfile.TemporaryDirectory() as tempdir:
            case, baseline_root = setup_generate_baseline_mock(tempdir)

            common = SystemTestsCommon(case)

            # Patch additional_baseline_generation() so we can check it was called
            with mock.patch.object(
                common, "additional_baseline_generation"
            ) as mock_generate_baseline_phase:
                common._generate_baseline()

            baseline_dir = baseline_root / "master" / "ERIO.ne30_g16.A.docker_gnu"
            assert (baseline_dir / "cpl.log.gz").exists()
            assert (baseline_dir / "cpl-tput.log").exists()
            assert (baseline_dir / "cpl-mem.log").exists()
            assert (baseline_dir / "cpl.hi.2023-01-01.nc").exists()

            with open(baseline_dir / "cpl-tput.log") as fd:
                lines = fd.readlines()

            assert len(lines) == 1
            assert re.match("sha:.* date:.* (\d+\.\d+)", lines[0])

            with open(baseline_dir / "cpl-mem.log") as fd:
                lines = fd.readlines()

            assert len(lines) == 1
            assert re.match("sha:.* date:.* (\d+\.\d+)", lines[0])

            # Check that additional_baseline_generation() was called
            expected_basegen_dir = str(
                baseline_root / "master" / "ERIO.ne30_g16.A.docker_gnu"
            )
            mock_generate_baseline_phase.assert_called_once_with(expected_basegen_dir)

    def test_generate_baseline_phase_subclass_called(self):
        """Check that child classes can extend additional_baseline_generation() such that it gets called"""

        class _SubTest(SystemTestsCommon):
            def __init__(self, case):
                super().__init__(case)
                self.phase_called_with = None
                self.abc123 = None

            def additional_baseline_generation(self, basegen_dir):
                self.phase_called_with = basegen_dir
                self.abc123 = 1987

        with tempfile.TemporaryDirectory() as tempdir:
            case, baseline_root = setup_generate_baseline_mock(tempdir)

            common = _SubTest(case)

            common._generate_baseline()

            expected_basegen_dir = str(
                baseline_root / "master" / "ERIO.ne30_g16.A.docker_gnu"
            )
            assert common.phase_called_with == expected_basegen_dir
            assert common.abc123 == 1987

    def test_kwargs(self):
        case = mock.MagicMock()

        case.get_value.side_effect = (
            "/caseroot",
            "SMS.f19_g16.S",
            "cpl",
            "/caseroot",
            "SMS.f19_g16.S",
        )

        _ = SystemTestsCommon(case, something="random")

        case = mock.MagicMock()

        case.get_value.side_effect = (
            "/caseroot",
            "SMS.f19_g16.S",
            "cpl",
            "/caseroot",
            "SMS.f19_g16.S",
        )

        orig1 = SystemTestsCompareTwo._get_caseroot
        orig2 = SystemTestsCompareTwo._get_caseroot2

        SystemTestsCompareTwo._get_caseroot = mock.MagicMock()
        SystemTestsCompareTwo._get_caseroot2 = mock.MagicMock()

        _ = SystemTestsCompareTwo(case, something="random")

        SystemTestsCompareTwo._get_caseroot = orig1
        SystemTestsCompareTwo._get_caseroot2 = orig2

        case = mock.MagicMock()

        case.get_value.side_effect = (
            "/caseroot",
            "SMS.f19_g16.S",
            "cpl",
            "/caseroot",
            "SMS.f19_g16.S",
        )

        orig = SystemTestsCompareN._get_caseroots

        SystemTestsCompareN._get_caseroots = mock.MagicMock()

        _ = SystemTestsCompareN(case, something="random")

        SystemTestsCompareN._get_caseroots = orig


# ---------------------------------------------------------------------------
# pytest-style tests for _format_elapsed_model_time
# ---------------------------------------------------------------------------


class TestFormatElapsedModelTime:
    """Unit tests for _format_elapsed_model_time helper.

    The helper converts two YYYYMMDD-encoded model-date stamps (stored as
    float/int by the coupler-log parser) into a human-readable elapsed-time
    string.  Month/year borrows are exact for the case's calendar
    (``NO_LEAP`` or ``GREGORIAN``), which is passed in from the case
    ``CALENDAR`` variable; the default is ``NO_LEAP``.
    """

    # ------------------------------------------------------------------
    # same-date / zero cases
    # ------------------------------------------------------------------

    def test_same_day_returns_zero_days(self):
        """Same start and end stamp produces '0 days'."""
        assert _format_elapsed_model_time(10115, 10115) == "0 days"

    def test_zero_components_after_borrowing_returns_zero_days(self):
        """Edge case where all computed components are zero."""
        # year=0, month=0, day=0 after arithmetic → fall through to default
        assert _format_elapsed_model_time(0, 0) == "0 days"

    # ------------------------------------------------------------------
    # days-only cases
    # ------------------------------------------------------------------

    def test_one_day_singular(self):
        """A one-day difference uses the singular 'day'."""
        assert _format_elapsed_model_time(10101, 10102) == "1 day"

    def test_multiple_days_same_month(self):
        """Several days within the same month are reported correctly."""
        assert _format_elapsed_model_time(10104, 10108) == "4 days"

    def test_many_days_no_month_borrow_needed(self):
        """Large day delta that does not require borrowing."""
        assert _format_elapsed_model_time(10101, 10128) == "27 days"

    # ------------------------------------------------------------------
    # months-only cases
    # ------------------------------------------------------------------

    def test_one_month_singular(self):
        """Exactly one month difference, same day, uses singular 'month'."""
        assert _format_elapsed_model_time(10201, 10301) == "1 month"

    def test_multiple_months_same_year(self):
        """Several months within the same year, same day-of-month."""
        assert _format_elapsed_model_time(10101, 10601) == "5 months"

    # ------------------------------------------------------------------
    # years-only cases
    # ------------------------------------------------------------------

    def test_one_year_singular(self):
        """Exactly one year difference, same month/day, uses singular 'year'."""
        assert _format_elapsed_model_time(10101, 20101) == "1 year"

    def test_multiple_years_same_month_day(self):
        """Several full years, no residual months or days."""
        assert _format_elapsed_model_time(10101, 30101) == "2 years"

    # ------------------------------------------------------------------
    # combined-component cases
    # ------------------------------------------------------------------

    def test_years_months_days_all_present(self):
        """All three components non-zero."""
        # start: year=1, month=1, day=2  →  end: year=5, month=12, day=31
        # years=4, months=11, days=29
        assert _format_elapsed_model_time(10102, 51231) == "4 years, 11 months, 29 days"

    def test_all_singular_components(self):
        """Each component equals 1 (singular forms in every slot)."""
        # start: year=1, month=1, day=1  →  end: year=2, month=2, day=2
        # years=1, months=1, days=1
        assert _format_elapsed_model_time(10101, 20202) == "1 year, 1 month, 1 day"

    def test_years_and_months_no_days(self):
        """Year and month components present but days component is zero."""
        # start: year=1, month=3, day=15  →  end: year=3, month=7, day=15
        # years=2, months=4, days=0
        assert _format_elapsed_model_time(10315, 30715) == "2 years, 4 months"

    def test_years_and_days_no_months(self):
        """Year and day components present but months component is zero."""
        # start: year=1, month=6, day=1  →  end: year=4, month=6, day=10
        # years=3, months=0, days=9
        assert _format_elapsed_model_time(10601, 40610) == "3 years, 9 days"

    def test_months_and_days_no_years(self):
        """Month and day components present but years component is zero."""
        # start: year=1, month=2, day=10  →  end: year=1, month=5, day=15
        # years=0, months=3, days=5
        assert _format_elapsed_model_time(10210, 10515) == "3 months, 5 days"

    # ------------------------------------------------------------------
    # borrow cases
    # ------------------------------------------------------------------

    def test_day_borrow_from_month(self):
        """End day less than start day borrows the true length of Feb."""
        # start: year=1, month=2, day=5  →  end: year=1, month=3, day=1
        # raw: years=0, months=1, days=-4
        # borrow Feb (NO_LEAP → 28): days = -4 + 28 = 24, months = 0
        assert _format_elapsed_model_time(10205, 10301) == "24 days"

    def test_month_borrow_from_year(self):
        """End month less than start month triggers a 12-month borrow from years."""
        # start: year=1, month=12, day=1  →  end: year=2, month=1, day=1
        # raw: years=1, months=-11, days=0  →  months=1, years=0
        assert _format_elapsed_model_time(11201, 20101) == "1 month"

    def test_both_day_and_month_borrow(self):
        """Both day and month borrows occur in the same calculation."""
        # start: year=2, month=12, day=20  →  end: year=3, month=1, day=5
        # raw: years=1, months=-11, days=-15
        # day borrow (Dec → 31 days): days = -15 + 31 = 16, months = -12
        # month borrow: months = 0, years = 0
        # result: "16 days"
        assert _format_elapsed_model_time(21220, 30105) == "16 days"

    # ------------------------------------------------------------------
    # calendar-aware borrow cases
    # ------------------------------------------------------------------

    def test_february_borrow_no_leap(self):
        """A borrow across February on a NO_LEAP calendar uses 28 days."""
        # start: year=4, month=2, day=5  →  end: year=4, month=3, day=1
        # borrow Feb (NO_LEAP → 28): days = -4 + 28 = 24
        assert _format_elapsed_model_time(40205, 40301, "NO_LEAP") == "24 days"

    def test_february_borrow_gregorian_leap_year(self):
        """A borrow across a leap-year February on GREGORIAN uses 29 days."""
        # start: year=2000, month=2, day=5  →  end: year=2000, month=3, day=1
        # borrow Feb (GREGORIAN, 2000 is leap → 29): days = -4 + 29 = 25
        assert _format_elapsed_model_time(20000205, 20000301, "GREGORIAN") == "25 days"

    def test_february_borrow_gregorian_non_leap_year(self):
        """A borrow across a non-leap February on GREGORIAN uses 28 days."""
        # start: year=2001, month=2, day=5  →  end: year=2001, month=3, day=1
        # borrow Feb (GREGORIAN, 2001 not leap → 28): days = -4 + 28 = 24
        assert _format_elapsed_model_time(20010205, 20010301, "GREGORIAN") == "24 days"

    def test_calendar_type_is_case_insensitive(self):
        """The calendar name is matched case-insensitively."""
        assert _format_elapsed_model_time(20000205, 20000301, "gregorian") == "25 days"

    def test_calendar_defaults_to_no_leap(self):
        """Omitting the calendar defaults to NO_LEAP behavior."""
        assert _format_elapsed_model_time(40205, 40301) == "24 days"

    # ------------------------------------------------------------------
    # float input (mirrors how the coupler log stores the stamp)
    # ------------------------------------------------------------------

    def test_float_stamps_accepted(self):
        """Stamps stored as float by the coupler-log parser are handled."""
        assert (
            _format_elapsed_model_time(10102.0, 51231.0)
            == "4 years, 11 months, 29 days"
        )

    # ------------------------------------------------------------------
    # large / long-run case
    # ------------------------------------------------------------------

    def test_century_scale_run(self):
        """Stamps spanning many decades produce a sensible result."""
        # start: year=1 Jan 1  →  end: year=100 Jan 1  →  99 years
        assert _format_elapsed_model_time(10101, 1000101) == "99 years"


# ---------------------------------------------------------------------------
# pytest-style tests for _days_in_month
# ---------------------------------------------------------------------------


class TestDaysInMonth:
    """Unit tests for the calendar-aware _days_in_month helper."""

    def test_thirty_one_day_month(self):
        """January always has 31 days."""
        assert _days_in_month(2000, 1, "GREGORIAN") == 31

    def test_thirty_day_month(self):
        """April always has 30 days."""
        assert _days_in_month(2000, 4, "GREGORIAN") == 30

    def test_february_no_leap_calendar(self):
        """February is always 28 days on a NO_LEAP calendar, even a leap year."""
        assert _days_in_month(2000, 2, "NO_LEAP") == 28

    def test_february_gregorian_leap_year(self):
        """February gains a day in a Gregorian leap year."""
        assert _days_in_month(2000, 2, "GREGORIAN") == 29

    def test_february_gregorian_non_leap_year(self):
        """February has 28 days in a Gregorian non-leap year."""
        assert _days_in_month(2001, 2, "GREGORIAN") == 28

    def test_february_gregorian_century_non_leap(self):
        """A non-400 century year is not a leap year under the Gregorian rule."""
        assert _days_in_month(1900, 2, "GREGORIAN") == 28

    def test_february_gregorian_400_year_leap(self):
        """A year divisible by 400 is a leap year under the Gregorian rule."""
        assert _days_in_month(2000, 2, "GREGORIAN") == 29

    def test_calendar_case_insensitive(self):
        """Calendar name comparison is case-insensitive."""
        assert _days_in_month(2000, 2, "gregorian") == 29

    def test_unknown_calendar_treated_as_no_leap(self):
        """Any non-GREGORIAN calendar name falls back to no-leap behavior."""
        assert _days_in_month(2000, 2, "360_day") == 28

    def test_default_calendar_is_no_leap(self):
        """Omitting the calendar defaults to no-leap February."""
        assert _days_in_month(2000, 2) == 28
