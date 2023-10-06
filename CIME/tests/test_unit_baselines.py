#!/usr/bin/env python3

import gzip
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from CIME import baselines
from CIME.tests.test_unit_system_tests import CPLLOG


def create_mock_case(tempdir, get_latest_cpl_logs):
    caseroot = Path(tempdir, "0", "caseroot")

    rundir = caseroot / "run"

    get_latest_cpl_logs.return_value = (str(rundir / "cpl.log.gz"),)

    baseline_root = Path(tempdir, "baselines")

    baseline_root.mkdir(parents=True, exist_ok=False)

    case = mock.MagicMock()

    return case, caseroot, rundir, baseline_root


class TestUnitBaseline(unittest.TestCase):
    def test_get_cpl_throughput_no_file(self):
        throughput = baselines.get_cpl_throughput("/tmp/cpl.log")

        assert throughput is None

    def test_get_cpl_throughput(self):
        with tempfile.TemporaryDirectory() as tempdir:
            cpl_log_path = Path(tempdir, "cpl.log.gz")

            with gzip.open(cpl_log_path, "w") as fd:
                fd.write(CPLLOG.encode("utf-8"))

            throughput = baselines.get_cpl_throughput(str(cpl_log_path))

        assert throughput == 719.635

    def test_get_cpl_mem_usage_gz(self):
        with tempfile.TemporaryDirectory() as tempdir:
            cpl_log_path = Path(tempdir, "cpl.log.gz")

            with gzip.open(cpl_log_path, "w") as fd:
                fd.write(CPLLOG.encode("utf-8"))

            mem_usage = baselines.get_cpl_mem_usage(str(cpl_log_path))

        assert mem_usage == [
            (10102.0, 1673.89),
            (10103.0, 1673.89),
            (10104.0, 1673.89),
            (10105.0, 1673.89),
        ]

    @mock.patch("CIME.baselines.os.path.isfile")
    def test_get_cpl_mem_usage(self, isfile):
        isfile.return_value = True

        with mock.patch(
            "builtins.open", mock.mock_open(read_data=CPLLOG.encode("utf-8"))
        ) as mock_file:
            mem_usage = baselines.get_cpl_mem_usage("/tmp/cpl.log")

        assert mem_usage == [
            (10102.0, 1673.89),
            (10103.0, 1673.89),
            (10104.0, 1673.89),
            (10105.0, 1673.89),
        ]

    def test_read_baseline_mem_empty(self):
        with mock.patch("builtins.open", mock.mock_open(read_data="")) as mock_file:
            baseline = baselines.read_baseline_mem("/tmp/cpl-mem.log")

        assert baseline == []

    def test_read_baseline_mem_none(self):
        with mock.patch("builtins.open", mock.mock_open(read_data="-1")) as mock_file:
            baseline = baselines.read_baseline_mem("/tmp/cpl-mem.log")

        assert baseline == ["-1"]

    def test_read_baseline_mem(self):
        with mock.patch("builtins.open", mock.mock_open(read_data="200")) as mock_file:
            baseline = baselines.read_baseline_mem("/tmp/cpl-mem.log")

        assert baseline == ["200"]

    def test_read_baseline_tput_empty(self):
        with mock.patch("builtins.open", mock.mock_open(read_data="")) as mock_file:
            baseline = baselines.read_baseline_tput("/tmp/cpl-tput.log")

        assert baseline == []

    def test_read_baseline_tput_none(self):
        with mock.patch("builtins.open", mock.mock_open(read_data="-1")) as mock_file:
            baseline = baselines.read_baseline_tput("/tmp/cpl-tput.log")

        assert baseline == ["-1"]

    def test_read_baseline_tput(self):
        with mock.patch("builtins.open", mock.mock_open(read_data="200")) as mock_file:
            baseline = baselines.read_baseline_tput("/tmp/cpl-tput.log")

        assert baseline == ["200"]

    def test_write_baseline_mem_no_value(self):
        with mock.patch("builtins.open", mock.mock_open()) as mock_file:
            baselines.write_baseline_mem("/tmp", "-1")

        mock_file.assert_called_with("/tmp/cpl-mem.log", "w")
        mock_file.return_value.write.assert_called_with("-1")

    def test_write_baseline_mem(self):
        with mock.patch("builtins.open", mock.mock_open()) as mock_file:
            baselines.write_baseline_mem("/tmp", "200")

        mock_file.assert_called_with("/tmp/cpl-mem.log", "w")
        mock_file.return_value.write.assert_called_with("200")

    def test_write_baseline_tput_no_value(self):
        with mock.patch("builtins.open", mock.mock_open()) as mock_file:
            baselines.write_baseline_tput("/tmp", "-1")

        mock_file.assert_called_with("/tmp/cpl-tput.log", "w")
        mock_file.return_value.write.assert_called_with("-1")

    def test_write_baseline_tput(self):
        with mock.patch("builtins.open", mock.mock_open()) as mock_file:
            baselines.write_baseline_tput("/tmp", "200")

        mock_file.assert_called_with("/tmp/cpl-tput.log", "w")
        mock_file.return_value.write.assert_called_with("200")

    @mock.patch("CIME.baselines.get_cpl_throughput")
    @mock.patch("CIME.baselines.get_latest_cpl_logs")
    def test_default_get_throughput(self, get_latest_cpl_logs, get_cpl_throughput):
        get_cpl_throughput.side_effect = FileNotFoundError()

        with tempfile.TemporaryDirectory() as tempdir:
            case, _, _, baseline_root = create_mock_case(tempdir, get_latest_cpl_logs)

            tput = baselines.default_get_throughput(case)

            assert tput == None

    @mock.patch("CIME.baselines.get_cpl_mem_usage")
    @mock.patch("CIME.baselines.get_latest_cpl_logs")
    def test_default_get_mem_usage(self, get_latest_cpl_logs, get_cpl_mem_usage):
        get_cpl_mem_usage.side_effect = FileNotFoundError()

        with tempfile.TemporaryDirectory() as tempdir:
            case, _, _, baseline_root = create_mock_case(tempdir, get_latest_cpl_logs)

            mem = baselines.default_get_mem_usage(case)

            assert mem == None

    @mock.patch("CIME.baselines.get_cpl_mem_usage")
    @mock.patch("CIME.baselines.get_latest_cpl_logs")
    def test_write_baseline(self, get_latest_cpl_logs, get_cpl_mem_usage):
        with tempfile.TemporaryDirectory() as tempdir:
            case, _, _, baseline_root = create_mock_case(tempdir, get_latest_cpl_logs)

            get_cpl_mem_usage.return_value = [
                (1, 1000.0),
                (2, 1001.0),
                (3, 1002.0),
                (4, 1003.0),
            ]

            baselines.write_baseline(
                case, baseline_root, get_latest_cpl_logs.return_value
            )

    @mock.patch("CIME.baselines.get_cpl_throughput")
    @mock.patch("CIME.baselines.read_baseline_tput")
    @mock.patch("CIME.baselines.get_latest_cpl_logs")
    def test_compare_throughput_no_baseline_file(
        self, get_latest_cpl_logs, read_baseline_tput, get_cpl_throughput
    ):
        read_baseline_tput.side_effect = FileNotFoundError

        get_cpl_throughput.return_value = 504

        with tempfile.TemporaryDirectory() as tempdir:
            case, _, _, baseline_root = create_mock_case(tempdir, get_latest_cpl_logs)

            case.get_value.side_effect = (
                str(baseline_root),
                "master/ERIO.ne30_g16_rx1.A.docker_gnu",
                "/tmp/components/cpl",
                0.05,
            )

            (below_tolerance, comment) = baselines.compare_throughput(case)

        assert below_tolerance is None
        assert comment == "Could not read baseline throughput file: "

    @mock.patch("CIME.baselines.default_get_throughput")
    @mock.patch("CIME.baselines.read_baseline_tput")
    @mock.patch("CIME.baselines.get_latest_cpl_logs")
    def test_compare_throughput_no_baseline(
        self, get_latest_cpl_logs, read_baseline_tput, default_get_throughput
    ):
        read_baseline_tput.return_value = None

        default_get_throughput.return_value = 504

        with tempfile.TemporaryDirectory() as tempdir:
            case, _, _, baseline_root = create_mock_case(tempdir, get_latest_cpl_logs)

            case.get_baseline_dir.return_value = str(
                baseline_root / "master" / "ERIO.ne30_g16_rx1.A.docker_gnu"
            )

            case.get_value.side_effect = (
                "/tmp/components/cpl",
                0.05,
            )

            (below_tolerance, comment) = baselines.compare_throughput(case)

        assert below_tolerance is None
        assert comment == "Could not determine diff with baseline None and current 504"

    @mock.patch("CIME.baselines.default_get_throughput")
    @mock.patch("CIME.baselines.read_baseline_tput")
    @mock.patch("CIME.baselines.get_latest_cpl_logs")
    def test_compare_throughput_no_tolerance(
        self, get_latest_cpl_logs, read_baseline_tput, default_get_throughput
    ):
        read_baseline_tput.return_value = 500

        default_get_throughput.return_value = 504

        with tempfile.TemporaryDirectory() as tempdir:
            case, _, _, baseline_root = create_mock_case(tempdir, get_latest_cpl_logs)

            case.get_baseline_dir.return_value = str(
                baseline_root / "master" / "ERIO.ne30_g16_rx1.A.docker_gnu"
            )

            case.get_value.side_effect = (
                "/tmp/components/cpl",
                None,
            )

            (below_tolerance, comment) = baselines.compare_throughput(case)

        assert below_tolerance
        assert (
            comment
            == "TPUTCOMP: Computation time changed by -0.80% relative to baseline"
        )

    @mock.patch("CIME.baselines.default_get_throughput")
    @mock.patch("CIME.baselines.read_baseline_tput")
    @mock.patch("CIME.baselines.get_latest_cpl_logs")
    def test_compare_throughput_above_threshold(
        self, get_latest_cpl_logs, read_baseline_tput, default_get_throughput
    ):
        read_baseline_tput.return_value = 1000

        default_get_throughput.return_value = 504

        with tempfile.TemporaryDirectory() as tempdir:
            case, _, _, baseline_root = create_mock_case(tempdir, get_latest_cpl_logs)

            case.get_baseline_dir.return_value = str(
                baseline_root / "master" / "ERIO.ne30_g16_rx1.A.docker_gnu"
            )

            case.get_value.side_effect = (
                "/tmp/components/cpl",
                0.05,
            )

            (below_tolerance, comment) = baselines.compare_throughput(case)

        assert not below_tolerance
        assert (
            comment == "Error: TPUTCOMP: Computation time increase > 5% from baseline"
        )

    @mock.patch("CIME.baselines.default_get_throughput")
    @mock.patch("CIME.baselines.read_baseline_tput")
    @mock.patch("CIME.baselines.get_latest_cpl_logs")
    def test_compare_throughput(
        self, get_latest_cpl_logs, read_baseline_tput, default_get_throughput
    ):
        read_baseline_tput.return_value = 500

        default_get_throughput.return_value = 504

        with tempfile.TemporaryDirectory() as tempdir:
            case, _, _, baseline_root = create_mock_case(tempdir, get_latest_cpl_logs)

            case.get_baseline_dir.return_value = str(
                baseline_root / "master" / "ERIO.ne30_g16_rx1.A.docker_gnu"
            )

            case.get_value.side_effect = (
                "/tmp/components/cpl",
                0.05,
            )

            (below_tolerance, comment) = baselines.compare_throughput(case)

        assert below_tolerance
        assert (
            comment
            == "TPUTCOMP: Computation time changed by -0.80% relative to baseline"
        )

    @mock.patch("CIME.baselines.get_cpl_mem_usage")
    @mock.patch("CIME.baselines.read_baseline_mem")
    @mock.patch("CIME.baselines.get_latest_cpl_logs")
    def test_compare_memory_no_baseline(
        self, get_latest_cpl_logs, read_baseline_mem, get_cpl_mem_usage
    ):
        read_baseline_mem.return_value = None

        get_cpl_mem_usage.return_value = [
            (1, 1000.0),
            (2, 1001.0),
            (3, 1002.0),
            (4, 1003.0),
        ]

        with tempfile.TemporaryDirectory() as tempdir:
            case, _, _, baseline_root = create_mock_case(tempdir, get_latest_cpl_logs)

            case.get_baseline_dir.return_value = str(
                baseline_root / "master" / "ERIO.ne30_g16_rx1.A.docker_gnu"
            )

            case.get_value.side_effect = (
                "/tmp/components/cpl",
                0.05,
            )

            (below_tolerance, comment) = baselines.compare_memory(case)

        assert below_tolerance
        assert (
            comment
            == "MEMCOMP: Memory usage highwater has changed by 0.00% relative to baseline"
        )

    @mock.patch("CIME.baselines.get_cpl_mem_usage")
    @mock.patch("CIME.baselines.read_baseline_mem")
    @mock.patch("CIME.baselines.get_latest_cpl_logs")
    def test_compare_memory_not_enough_samples(
        self, get_latest_cpl_logs, read_baseline_mem, get_cpl_mem_usage
    ):
        read_baseline_mem.return_value = 1000.0

        get_cpl_mem_usage.return_value = [
            (1, 1000.0),
            (2, 1001.0),
        ]

        with tempfile.TemporaryDirectory() as tempdir:
            case, _, _, baseline_root = create_mock_case(tempdir, get_latest_cpl_logs)

            case.get_value.side_effect = (
                str(baseline_root),
                "master/ERIO.ne30_g16_rx1.A.docker_gnu",
                "/tmp/components/cpl",
                0.05,
            )

            (below_tolerance, comment) = baselines.compare_memory(case)

        assert below_tolerance is None
        assert comment == "Found 2 memory usage samples, need atleast 4"

    @mock.patch("CIME.baselines.get_cpl_mem_usage")
    @mock.patch("CIME.baselines.read_baseline_mem")
    @mock.patch("CIME.baselines.get_latest_cpl_logs")
    def test_compare_memory_no_baseline_file(
        self, get_latest_cpl_logs, read_baseline_mem, get_cpl_mem_usage
    ):
        read_baseline_mem.side_effect = FileNotFoundError

        get_cpl_mem_usage.return_value = [
            (1, 1000.0),
            (2, 1001.0),
            (3, 1002.0),
            (4, 1003.0),
        ]

        with tempfile.TemporaryDirectory() as tempdir:
            case, _, _, baseline_root = create_mock_case(tempdir, get_latest_cpl_logs)

            case.get_value.side_effect = (
                str(baseline_root),
                "master/ERIO.ne30_g16_rx1.A.docker_gnu",
                "/tmp/components/cpl",
                0.05,
            )

            (below_tolerance, comment) = baselines.compare_memory(case)

        assert below_tolerance is None
        assert comment == "Could not read baseline memory usage: "

    @mock.patch("CIME.baselines.get_cpl_mem_usage")
    @mock.patch("CIME.baselines.read_baseline_mem")
    @mock.patch("CIME.baselines.get_latest_cpl_logs")
    def test_compare_memory_no_tolerance(
        self, get_latest_cpl_logs, read_baseline_mem, get_cpl_mem_usage
    ):
        read_baseline_mem.return_value = 1000.0

        get_cpl_mem_usage.return_value = [
            (1, 1000.0),
            (2, 1001.0),
            (3, 1002.0),
            (4, 1003.0),
        ]

        with tempfile.TemporaryDirectory() as tempdir:
            case, _, _, baseline_root = create_mock_case(tempdir, get_latest_cpl_logs)

            case.get_baseline_dir.return_value = str(
                baseline_root / "master" / "ERIO.ne30_g16_rx1.A.docker_gnu"
            )

            case.get_value.side_effect = (
                "/tmp/components/cpl",
                None,
            )

            (below_tolerance, comment) = baselines.compare_memory(case)

        assert below_tolerance
        assert (
            comment
            == "MEMCOMP: Memory usage highwater has changed by 0.30% relative to baseline"
        )

    @mock.patch("CIME.baselines.get_cpl_mem_usage")
    @mock.patch("CIME.baselines.read_baseline_mem")
    @mock.patch("CIME.baselines.get_latest_cpl_logs")
    def test_compare_memory_above_threshold(
        self, get_latest_cpl_logs, read_baseline_mem, get_cpl_mem_usage
    ):
        read_baseline_mem.return_value = 1000.0

        get_cpl_mem_usage.return_value = [
            (1, 2000.0),
            (2, 2001.0),
            (3, 2002.0),
            (4, 2003.0),
        ]

        with tempfile.TemporaryDirectory() as tempdir:
            case, _, _, baseline_root = create_mock_case(tempdir, get_latest_cpl_logs)

            case.get_baseline_dir.return_value = str(
                baseline_root / "master" / "ERIO.ne30_g16_rx1.A.docker_gnu"
            )

            case.get_value.side_effect = (
                "/tmp/components/cpl",
                0.05,
            )

            (below_tolerance, comment) = baselines.compare_memory(case)

        assert not below_tolerance
        assert (
            comment
            == "Error: Memory usage increase >5% from baseline's 1000.000000 to 2003.000000"
        )

    @mock.patch("CIME.baselines.get_cpl_mem_usage")
    @mock.patch("CIME.baselines.read_baseline_mem")
    @mock.patch("CIME.baselines.get_latest_cpl_logs")
    def test_compare_memory(
        self, get_latest_cpl_logs, read_baseline_mem, get_cpl_mem_usage
    ):
        read_baseline_mem.return_value = 1000.0

        get_cpl_mem_usage.return_value = [
            (1, 1000.0),
            (2, 1001.0),
            (3, 1002.0),
            (4, 1003.0),
        ]

        with tempfile.TemporaryDirectory() as tempdir:
            case, _, _, baseline_root = create_mock_case(tempdir, get_latest_cpl_logs)

            case.get_baseline_dir.return_value = str(
                baseline_root / "master" / "ERIO.ne30_g16_rx1.A.docker_gnu"
            )

            case.get_value.side_effect = (
                "/tmp/components/cpl",
                0.05,
            )

            (below_tolerance, comment) = baselines.compare_memory(case)

        assert below_tolerance
        assert (
            comment
            == "MEMCOMP: Memory usage highwater has changed by 0.30% relative to baseline"
        )

    def test_get_latest_cpl_logs_found_multiple(self):
        with tempfile.TemporaryDirectory() as tempdir:
            run_dir = Path(tempdir) / "run"
            run_dir.mkdir(parents=True, exist_ok=False)

            cpl_log_path = run_dir / "cpl.log.gz"
            cpl_log_path.touch()

            cpl_log_2_path = run_dir / "cpl-2023-01-01.log.gz"
            cpl_log_2_path.touch()

            case = mock.MagicMock()
            case.get_value.side_effect = (
                str(run_dir),
                "mct",
            )

            latest_cpl_logs = baselines.get_latest_cpl_logs(case)

        assert len(latest_cpl_logs) == 2
        assert sorted(latest_cpl_logs) == sorted(
            [str(cpl_log_path), str(cpl_log_2_path)]
        )

    def test_get_latest_cpl_logs_found_single(self):
        with tempfile.TemporaryDirectory() as tempdir:
            run_dir = Path(tempdir) / "run"
            run_dir.mkdir(parents=True, exist_ok=False)

            cpl_log_path = run_dir / "cpl.log.gz"
            cpl_log_path.touch()

            case = mock.MagicMock()
            case.get_value.side_effect = (
                str(run_dir),
                "mct",
            )

            latest_cpl_logs = baselines.get_latest_cpl_logs(case)

        assert len(latest_cpl_logs) == 1
        assert latest_cpl_logs[0] == str(cpl_log_path)

    def test_get_latest_cpl_logs(self):
        case = mock.MagicMock()
        case.get_value.side_effect = (
            f"/tmp/run",
            "mct",
        )

        latest_cpl_logs = baselines.get_latest_cpl_logs(case)

        assert len(latest_cpl_logs) == 0
