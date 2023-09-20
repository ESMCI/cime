#!/usr/bin/env python3

import os
import tempfile
import gzip
from re import A
import unittest
from unittest import mock
from pathlib import Path

from CIME.SystemTests.system_tests_common import SystemTestsCommon
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


class TestCaseSubmit(unittest.TestCase):
    @mock.patch("CIME.SystemTests.system_tests_common.append_testlog")
    def test_compare_throughput(self, append_testlog):
        with tempfile.TemporaryDirectory() as tempdir:
            case, caseroot, baseline_root, run_dir = create_mock_case(
                tempdir, cpllog_data=CPLLOG
            )

            base_case, base_caseroot, _, _ = create_mock_case(
                tempdir, idx=1, cpllog_data=CPLLOG
            )

            case.get_value.side_effect = (
                str(caseroot),
                "ERIO.ne30_g16_rx1.A.docker_gnu",
                "mct",
                "master/ERIO.ne30_g16_rx1.A.docker_gnu",
                str(baseline_root),
                str(run_dir),
                0.05,
            )

            baseline_dir = baseline_root / "master" / "ERIO.ne30_g16_rx1.A.docker_gnu"
            baseline_dir.mkdir(parents=True, exist_ok=False)
            baseline_mem = baseline_dir / "cpl-mem.log"

            with open(baseline_mem, "w") as fd:
                fd.write(str("1673.89"))

            common = SystemTestsCommon(case)

            common._compare_memory()

            assert common._test_status.get_overall_test_status() == ("PASS", None)

            append_testlog.assert_any_call(
                "MEMCOMP: Memory usage highwater has changed by 0.00% relative to baseline",
                str(caseroot),
            )

    @mock.patch("CIME.SystemTests.system_tests_common.append_testlog")
    def test_compare_throughput_fail(self, append_testlog):
        with tempfile.TemporaryDirectory() as tempdir:
            case, caseroot, baseline_root, run_dir = create_mock_case(
                tempdir, cpllog_data=CPLLOG
            )

            base_case, base_caseroot, _, _ = create_mock_case(
                tempdir, idx=1, cpllog_data=CPLLOG
            )

            case.get_value.side_effect = (
                str(caseroot),
                "ERIO.ne30_g16_rx1.A.docker_gnu",
                "mct",
                "master/ERIO.ne30_g16_rx1.A.docker_gnu",
                str(baseline_root),
                str(run_dir),
                0.05,
            )

            baseline_dir = baseline_root / "master" / "ERIO.ne30_g16_rx1.A.docker_gnu"
            baseline_dir.mkdir(parents=True, exist_ok=False)
            baseline_mem = baseline_dir / "cpl-mem.log"

            with open(baseline_mem, "w") as fd:
                fd.write(str("1473.89"))

            common = SystemTestsCommon(case)

            common._compare_memory()

            assert common._test_status.get_overall_test_status() == ("PASS", None)

            append_testlog.assert_any_call(
                "MEMCOMP: Memory usage highwater has changed by 13.57% relative to baseline",
                str(caseroot),
            )
            append_testlog.assert_any_call(
                "Error: Memory usage increase >5% from baseline's 1473.890000 to 1673.890000",
                str(caseroot),
            )

    @mock.patch("CIME.SystemTests.system_tests_common.append_testlog")
    def test_compare_memory(self, append_testlog):
        with tempfile.TemporaryDirectory() as tempdir:
            case, caseroot, baseline_root, run_dir = create_mock_case(
                tempdir, cpllog_data=CPLLOG
            )

            base_case, base_caseroot, _, _ = create_mock_case(
                tempdir, idx=1, cpllog_data=CPLLOG
            )

            case.get_value.side_effect = (
                str(caseroot),
                "ERIO.ne30_g16_rx1.A.docker_gnu",
                "mct",
                "master/ERIO.ne30_g16_rx1.A.docker_gnu",
                str(baseline_root),
                str(run_dir),
                0.05,
            )

            baseline_dir = baseline_root / "master" / "ERIO.ne30_g16_rx1.A.docker_gnu"
            baseline_dir.mkdir(parents=True, exist_ok=False)
            baseline_tput = baseline_dir / "cpl-tput.log"

            with open(baseline_tput, "w") as fd:
                fd.write(str("719.635"))

            common = SystemTestsCommon(case)

            common._compare_throughput()

            assert common._test_status.get_overall_test_status() == ("PASS", None)

            append_testlog.assert_any_call(
                "TPUTCOMP: Computation time changed by 0.00% relative to baseline",
                str(caseroot),
            )

    @mock.patch("CIME.SystemTests.system_tests_common.append_testlog")
    def test_compare_memory_fail(self, append_testlog):
        with tempfile.TemporaryDirectory() as tempdir:
            case, caseroot, baseline_root, run_dir = create_mock_case(
                tempdir, cpllog_data=CPLLOG
            )

            base_case, base_caseroot, _, _ = create_mock_case(
                tempdir, idx=1, cpllog_data=CPLLOG
            )

            case.get_value.side_effect = (
                str(caseroot),
                "ERIO.ne30_g16_rx1.A.docker_gnu",
                "mct",
                "master/ERIO.ne30_g16_rx1.A.docker_gnu",
                str(baseline_root),
                str(run_dir),
                0.05,
            )

            baseline_dir = baseline_root / "master" / "ERIO.ne30_g16_rx1.A.docker_gnu"
            baseline_dir.mkdir(parents=True, exist_ok=False)
            baseline_tput = baseline_dir / "cpl-tput.log"

            with open(baseline_tput, "w") as fd:
                fd.write(str("900.635"))

            common = SystemTestsCommon(case)

            common._compare_throughput()

            assert common._test_status.get_overall_test_status() == ("PASS", None)

            append_testlog.assert_any_call(
                "TPUTCOMP: Computation time changed by 20.10% relative to baseline",
                str(caseroot),
            )
            append_testlog.assert_any_call(
                "Error: TPUTCOMP: Computation time increase > 5% from baseline",
                str(caseroot),
            )

    def test_generate_baseline(self):
        with tempfile.TemporaryDirectory() as tempdir:
            case, caseroot, baseline_root, run_dir = create_mock_case(
                tempdir, cpllog_data=CPLLOG
            )

            case.get_value.side_effect = (
                str(caseroot),
                "ERIO.ne30_g16_rx1.A.docker_gnu",
                "mct",
                str(run_dir),
                "case.std",
                str(baseline_root),
                "master/ERIO.ne30_g16_rx1.A.docker_gnu",
                "ERIO.ne30_g16_rx1.A.docker_gnu.G.20230919_193255_z9hg2w",
                "mct",
                str(run_dir),
                "ERIO",
                "ERIO.ne30_g16_rx1.A.docker_gnu",
                os.getcwd(),
                "master/ERIO.ne30_g16_rx1.A.docker_gnu",
                str(baseline_root),
                "master/ERIO.ne30_g16_rx1.A.docker_gnu",
                str(run_dir),
            )

            common = SystemTestsCommon(case)

            common._generate_baseline()

            baseline_dir = baseline_root / "master" / "ERIO.ne30_g16_rx1.A.docker_gnu"

            assert (baseline_dir / "cpl.log.gz").exists()
            assert (baseline_dir / "cpl-tput.log").exists()
            assert (baseline_dir / "cpl-mem.log").exists()
            assert (baseline_dir / "cpl.hi.2023-01-01.nc").exists()

            with open(baseline_dir / "cpl-tput.log") as fd:
                lines = fd.readlines()

            assert len(lines) == 3
            assert lines[-1] == "719.635"

            with open(baseline_dir / "cpl-mem.log") as fd:
                lines = fd.readlines()

            assert len(lines) == 3
            assert lines[-1] == "1673.89"

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

    def test_dry_run(self):
        case = mock.MagicMock()

        case.get_value.side_effect = (
            "/caseroot",
            "SMS.f19_g16.S",
            "cpl",
            "/caseroot",
            "SMS.f19_g16.S",
        )

        orig = SystemTestsCompareTwo._setup_cases_if_not_yet_done

        SystemTestsCompareTwo._setup_cases_if_not_yet_done = mock.MagicMock()

        system_test = SystemTestsCompareTwo(case, dry_run=True)

        system_test._setup_cases_if_not_yet_done.assert_not_called()

        case = mock.MagicMock()

        case.get_value.side_effect = (
            "/caseroot",
            "SMS.f19_g16.S",
            "cpl",
            "/caseroot",
            "SMS.f19_g16.S",
        )

        system_test = SystemTestsCompareTwo(case)

        system_test._setup_cases_if_not_yet_done.assert_called()

        SystemTestsCompareTwo._setup_cases_if_not_yet_done = orig

        orig = SystemTestsCompareN._setup_cases_if_not_yet_done

        SystemTestsCompareN._setup_cases_if_not_yet_done = mock.MagicMock()

        case = mock.MagicMock()

        case.get_value.side_effect = (
            "/caseroot",
            "SMS.f19_g16.S",
            "cpl",
            "/caseroot",
            "SMS.f19_g16.S",
        )

        system_test = SystemTestsCompareN(case, dry_run=True)

        system_test._setup_cases_if_not_yet_done.assert_not_called()

        case = mock.MagicMock()

        case.get_value.side_effect = (
            "/caseroot",
            "SMS.f19_g16.S",
            "cpl",
            "/caseroot",
            "SMS.f19_g16.S",
        )

        system_test = SystemTestsCompareN(case)

        system_test._setup_cases_if_not_yet_done.assert_called()

        SystemTestsCompareN._setup_cases_if_not_yet_done = orig
