import re
import unittest
import tempfile
from unittest import mock
from pathlib import Path

from CIME.bless_test_results import (
    bless_test_results,
    _bless_throughput,
    _bless_memory,
    bless_history,
    bless_namelists,
    is_bless_needed,
)


class TestUnitBlessTestResults(unittest.TestCase):
    @mock.patch("CIME.bless_test_results.generate_baseline")
    @mock.patch("CIME.bless_test_results.compare_baseline")
    def test_bless_history_fail(self, compare_baseline, generate_baseline):
        generate_baseline.return_value = (False, "")

        compare_baseline.return_value = (False, "")

        case = mock.MagicMock()
        case.get_value.side_effect = [
            "USER",
            "SMS.f19_g16.S",
            "/tmp/run",
        ]

        success, comment = bless_history(
            "SMS.f19_g16.S", case, "master", "/tmp/baselines", False, True
        )

        assert not success
        assert comment == "Generate baseline failed: "

    @mock.patch("CIME.bless_test_results.generate_baseline")
    @mock.patch("CIME.bless_test_results.compare_baseline")
    def test_bless_history_force(self, compare_baseline, generate_baseline):
        generate_baseline.return_value = (True, "")

        compare_baseline.return_value = (False, "")

        case = mock.MagicMock()
        case.get_value.side_effect = [
            "USER",
            "SMS.f19_g16.S",
            "/tmp/run",
        ]

        success, comment = bless_history(
            "SMS.f19_g16.S", case, "master", "/tmp/baselines", False, True
        )

        assert success
        assert comment is None

    @mock.patch("CIME.bless_test_results.compare_baseline")
    def test_bless_history(self, compare_baseline):
        compare_baseline.return_value = (True, "")

        case = mock.MagicMock()
        case.get_value.side_effect = [
            "USER",
            "SMS.f19_g16.S",
            "/tmp/run",
        ]

        success, comment = bless_history(
            "SMS.f19_g16.S", case, "master", "/tmp/baselines", True, False
        )

        assert success
        assert comment is None

    def test_bless_namelists_report_only(self):
        success, comment = bless_namelists(
            "SMS.f19_g16.S",
            True,
            False,
            None,
            "master",
            "/tmp/baselines",
        )

        assert success
        assert comment is None

    @mock.patch("CIME.bless_test_results.get_scripts_root")
    @mock.patch("CIME.bless_test_results.run_cmd")
    def test_bless_namelists_pes_file(self, run_cmd, get_scripts_root):
        get_scripts_root.return_value = "/tmp/cime"

        run_cmd.return_value = [1, None, None]

        success, comment = bless_namelists(
            "SMS.f19_g16.S",
            False,
            True,
            "/tmp/pes/new_layout.xml",
            "master",
            "/tmp/baselines",
        )

        assert not success
        assert comment == "Namelist regen failed: 'None'"

        call = run_cmd.call_args_list[0]

        assert re.match(
            r"/tmp/cime/create_test SMS.f19_g16.S --namelists-only  -g (?:-b )?master  --pesfile /tmp/pes/new_layout.xml --baseline-root /tmp/baselines -o",
            call[0][0],
        )

    @mock.patch("CIME.bless_test_results.get_scripts_root")
    @mock.patch("CIME.bless_test_results.run_cmd")
    def test_bless_namelists_new_test_id(self, run_cmd, get_scripts_root):
        get_scripts_root.return_value = "/tmp/cime"

        run_cmd.return_value = [1, None, None]

        success, comment = bless_namelists(
            "SMS.f19_g16.S",
            False,
            True,
            None,
            "master",
            "/tmp/baselines",
            new_test_root="/tmp/other-test-root",
            new_test_id="hello",
        )

        assert not success
        assert comment == "Namelist regen failed: 'None'"

        call = run_cmd.call_args_list[0]

        assert re.match(
            r"/tmp/cime/create_test SMS.f19_g16.S --namelists-only  -g (?:-b )?master  --test-root=/tmp/other-test-root --output-root=/tmp/other-test-root  -t hello --baseline-root /tmp/baselines -o",
            call[0][0],
        )

    @mock.patch("CIME.bless_test_results.get_scripts_root")
    @mock.patch("CIME.bless_test_results.run_cmd")
    def test_bless_namelists_new_test_root(self, run_cmd, get_scripts_root):
        get_scripts_root.return_value = "/tmp/cime"

        run_cmd.return_value = [1, None, None]

        success, comment = bless_namelists(
            "SMS.f19_g16.S",
            False,
            True,
            None,
            "master",
            "/tmp/baselines",
            new_test_root="/tmp/other-test-root",
        )

        assert not success
        assert comment == "Namelist regen failed: 'None'"

        call = run_cmd.call_args_list[0]

        assert re.match(
            r"/tmp/cime/create_test SMS.f19_g16.S --namelists-only  -g (?:-b )?master  --test-root=/tmp/other-test-root --output-root=/tmp/other-test-root  --baseline-root /tmp/baselines -o",
            call[0][0],
        )

    @mock.patch("CIME.bless_test_results.get_scripts_root")
    @mock.patch("CIME.bless_test_results.run_cmd")
    def test_bless_namelists_fail(self, run_cmd, get_scripts_root):
        get_scripts_root.return_value = "/tmp/cime"

        run_cmd.return_value = [1, None, None]

        success, comment = bless_namelists(
            "SMS.f19_g16.S",
            False,
            True,
            None,
            "master",
            "/tmp/baselines",
        )

        assert not success
        assert comment == "Namelist regen failed: 'None'"

        call = run_cmd.call_args_list[0]

        assert re.match(
            r"/tmp/cime/create_test SMS.f19_g16.S --namelists-only  -g (?:-b )?master  --baseline-root /tmp/baselines -o",
            call[0][0],
        )

    @mock.patch("CIME.bless_test_results.get_scripts_root")
    @mock.patch("CIME.bless_test_results.run_cmd")
    def test_bless_namelists_force(self, run_cmd, get_scripts_root):
        get_scripts_root.return_value = "/tmp/cime"

        run_cmd.return_value = [0, None, None]

        success, comment = bless_namelists(
            "SMS.f19_g16.S",
            False,
            True,
            None,
            "master",
            "/tmp/baselines",
        )

        assert success
        assert comment is None

        call = run_cmd.call_args_list[0]

        assert re.match(
            r"/tmp/cime/create_test SMS.f19_g16.S --namelists-only  -g (?:-b )?master  --baseline-root /tmp/baselines -o",
            call[0][0],
        )

    @mock.patch("CIME.bless_test_results.perf_write_baseline")
    @mock.patch("CIME.bless_test_results.perf_compare_memory_baseline")
    def test_bless_memory_force_error(
        self, perf_compare_memory_baseline, perf_write_baseline
    ):
        perf_write_baseline.side_effect = Exception

        perf_compare_memory_baseline.return_value = (False, "")

        case = mock.MagicMock()

        success, comment = _bless_memory(
            case, "SMS.f19_g16.S", "/tmp/baselines", "master", False, True
        )

        assert not success
        assert (
            comment
            == "Failed to write baseline memory usage for test 'SMS.f19_g16.S': "
        )
        perf_write_baseline.assert_called()

    @mock.patch("CIME.bless_test_results.perf_write_baseline")
    @mock.patch("CIME.bless_test_results.perf_compare_memory_baseline")
    def test_bless_memory_force(
        self, perf_compare_memory_baseline, perf_write_baseline
    ):
        perf_compare_memory_baseline.return_value = (False, "")

        case = mock.MagicMock()

        success, comment = _bless_memory(
            case, "SMS.f19_g16.S", "/tmp/baselines", "master", False, True
        )

        assert success
        assert comment is None
        perf_write_baseline.assert_called()

    @mock.patch("CIME.bless_test_results.perf_compare_memory_baseline")
    def test_bless_memory_report_only(self, perf_compare_memory_baseline):
        perf_compare_memory_baseline.return_value = (True, "")

        case = mock.MagicMock()

        success, comment = _bless_memory(
            case, "SMS.f19_g16.S", "/tmp/baselines", "master", True, False
        )

        assert success
        assert comment is None

    @mock.patch("CIME.bless_test_results.perf_write_baseline")
    @mock.patch("CIME.bless_test_results.perf_compare_memory_baseline")
    def test_bless_memory_general_error(
        self, perf_compare_memory_baseline, perf_write_baseline
    ):
        perf_compare_memory_baseline.side_effect = Exception

        case = mock.MagicMock()

        success, comment = _bless_memory(
            case, "SMS.f19_g16.S", "/tmp/baselines", "master", False, True
        )

        assert success
        assert comment is None

    @mock.patch("CIME.bless_test_results.perf_write_baseline")
    @mock.patch("CIME.bless_test_results.perf_compare_memory_baseline")
    def test_bless_memory_file_not_found_error(
        self, perf_compare_memory_baseline, perf_write_baseline
    ):
        perf_compare_memory_baseline.side_effect = FileNotFoundError

        case = mock.MagicMock()

        success, comment = _bless_memory(
            case, "SMS.f19_g16.S", "/tmp/baselines", "master", False, True
        )

        assert success
        assert comment is None

    @mock.patch("CIME.bless_test_results.perf_compare_memory_baseline")
    def test_bless_memory(self, perf_compare_memory_baseline):
        perf_compare_memory_baseline.return_value = (True, "")

        case = mock.MagicMock()

        success, comment = _bless_memory(
            case, "SMS.f19_g16.S", "/tmp/baselines", "master", False, False
        )

        assert success

    @mock.patch("CIME.bless_test_results.perf_write_baseline")
    @mock.patch("CIME.bless_test_results.perf_compare_throughput_baseline")
    def test_bless_throughput_force_error(
        self, perf_compare_throughput_baseline, perf_write_baseline
    ):
        perf_write_baseline.side_effect = Exception

        perf_compare_throughput_baseline.return_value = (False, "")

        case = mock.MagicMock()

        success, comment = _bless_throughput(
            case, "SMS.f19_g16.S", "/tmp/baselines", "master", False, True
        )

        assert not success
        assert comment == "Failed to write baseline throughput for 'SMS.f19_g16.S': "
        perf_write_baseline.assert_called()

    @mock.patch("CIME.bless_test_results.perf_write_baseline")
    @mock.patch("CIME.bless_test_results.perf_compare_throughput_baseline")
    def test_bless_throughput_force(
        self, perf_compare_throughput_baseline, perf_write_baseline
    ):
        perf_compare_throughput_baseline.return_value = (False, "")

        case = mock.MagicMock()

        success, comment = _bless_throughput(
            case, "SMS.f19_g16.S", "/tmp/baselines", "master", False, True
        )

        assert success
        assert comment is None
        perf_write_baseline.assert_called()

    @mock.patch("CIME.bless_test_results.perf_compare_throughput_baseline")
    def test_bless_throughput_report_only(self, perf_compare_throughput_baseline):
        perf_compare_throughput_baseline.return_value = (True, "")

        case = mock.MagicMock()

        success, comment = _bless_throughput(
            case, "SMS.f19_g16.S", "/tmp/baselines", "master", True, False
        )

        assert success
        assert comment is None

    @mock.patch("CIME.bless_test_results.perf_compare_throughput_baseline")
    def test_bless_throughput_general_error(self, perf_compare_throughput_baseline):
        perf_compare_throughput_baseline.side_effect = Exception

        case = mock.MagicMock()

        success, comment = _bless_throughput(
            case, "SMS.f19_g16.S", "/tmp/baselines", "master", False, True
        )

        assert success
        assert comment is None

    @mock.patch("CIME.bless_test_results.perf_write_baseline")
    @mock.patch("CIME.bless_test_results.perf_compare_throughput_baseline")
    def test_bless_throughput_file_not_found_error(
        self,
        perf_compare_throughput_baseline,
        perf_write_baseline,
    ):
        perf_compare_throughput_baseline.side_effect = FileNotFoundError

        case = mock.MagicMock()

        success, comment = _bless_throughput(
            case, "SMS.f19_g16.S", "/tmp/baselines", "master", False, True
        )

        assert success
        assert comment is None

    @mock.patch("CIME.bless_test_results.perf_compare_throughput_baseline")
    def test_bless_throughput(self, perf_compare_throughput_baseline):
        perf_compare_throughput_baseline.return_value = (True, "")

        case = mock.MagicMock()

        success, comment = _bless_throughput(
            case, "SMS.f19_g16.S", "/tmp/baselines", "master", False, False
        )

        assert success

    @mock.patch("CIME.bless_test_results._bless_throughput")
    @mock.patch("CIME.bless_test_results._bless_memory")
    @mock.patch("CIME.bless_test_results.Case")
    @mock.patch("CIME.bless_test_results.TestStatus")
    @mock.patch("CIME.bless_test_results.get_test_status_files")
    def test_bless_perf(
        self,
        get_test_status_files,
        TestStatus,
        Case,
        _bless_memory,
        _bless_throughput,
    ):
        get_test_status_files.return_value = [
            "/tmp/cases/SMS.f19_g16.S.docker_gnu/TestStatus",
        ]

        ts = TestStatus.return_value
        ts.get_name.return_value = "SMS.f19_g16.S.docker_gnu"
        ts.get_overall_test_status.return_value = ("PASS", "RUN")
        ts.get_status.side_effect = ["PASS", "PASS", "PASS", "FAIL", "FAIL"]

        case = Case.return_value.__enter__.return_value

        _bless_memory.return_value = (True, "")

        _bless_throughput.return_value = (True, "")

        success = bless_test_results(
            "master",
            "/tmp/baseline",
            "/tmp/cases",
            "gnu",
            force=True,
            bless_perf=True,
        )

        assert success
        _bless_memory.assert_called()
        _bless_throughput.assert_called()

    @mock.patch("CIME.bless_test_results._bless_throughput")
    @mock.patch("CIME.bless_test_results._bless_memory")
    @mock.patch("CIME.bless_test_results.Case")
    @mock.patch("CIME.bless_test_results.TestStatus")
    @mock.patch("CIME.bless_test_results.get_test_status_files")
    def test_bless_memory_only(
        self,
        get_test_status_files,
        TestStatus,
        Case,
        _bless_memory,
        _bless_throughput,
    ):
        get_test_status_files.return_value = [
            "/tmp/cases/SMS.f19_g16.S.docker_gnu/TestStatus",
        ]

        ts = TestStatus.return_value
        ts.get_name.return_value = "SMS.f19_g16.S.docker_gnu"
        ts.get_overall_test_status.return_value = ("PASS", "RUN")
        ts.get_status.side_effect = ["PASS", "PASS", "PASS", "FAIL"]

        case = Case.return_value.__enter__.return_value

        _bless_memory.return_value = (True, "")

        success = bless_test_results(
            "master",
            "/tmp/baseline",
            "/tmp/cases",
            "gnu",
            force=True,
            bless_mem=True,
        )

        assert success
        _bless_memory.assert_called()
        _bless_throughput.assert_not_called()

    @mock.patch("CIME.bless_test_results._bless_throughput")
    @mock.patch("CIME.bless_test_results._bless_memory")
    @mock.patch("CIME.bless_test_results.Case")
    @mock.patch("CIME.bless_test_results.TestStatus")
    @mock.patch("CIME.bless_test_results.get_test_status_files")
    def test_bless_throughput_only(
        self,
        get_test_status_files,
        TestStatus,
        Case,
        _bless_memory,
        _bless_throughput,
    ):
        get_test_status_files.return_value = [
            "/tmp/cases/SMS.f19_g16.S.docker_gnu/TestStatus",
        ]

        ts = TestStatus.return_value
        ts.get_name.return_value = "SMS.f19_g16.S.docker_gnu"
        ts.get_overall_test_status.return_value = ("PASS", "RUN")
        ts.get_status.side_effect = ["PASS", "PASS", "PASS", "FAIL"]

        case = Case.return_value.__enter__.return_value

        _bless_throughput.return_value = (True, "")

        success = bless_test_results(
            "master",
            "/tmp/baseline",
            "/tmp/cases",
            "gnu",
            force=True,
            bless_tput=True,
        )

        assert success
        _bless_memory.assert_not_called()
        _bless_throughput.assert_called()

    @mock.patch("CIME.bless_test_results.bless_namelists")
    @mock.patch("CIME.bless_test_results.Case")
    @mock.patch("CIME.bless_test_results.TestStatus")
    @mock.patch("CIME.bless_test_results.get_test_status_files")
    def test_bless_namelists_only(
        self,
        get_test_status_files,
        TestStatus,
        Case,
        bless_namelists,
    ):
        get_test_status_files.return_value = [
            "/tmp/cases/SMS.f19_g16.S.docker_gnu/TestStatus",
        ]

        ts = TestStatus.return_value
        ts.get_name.return_value = "SMS.f19_g16.S.docker_gnu"
        ts.get_overall_test_status.return_value = ("PASS", "RUN")
        ts.get_status.side_effect = ["FAIL", "PASS", "PASS"]

        case = Case.return_value.__enter__.return_value

        bless_namelists.return_value = (True, "")

        success = bless_test_results(
            "master",
            "/tmp/baseline",
            "/tmp/cases",
            "gnu",
            force=True,
            namelists_only=True,
        )

        assert success
        bless_namelists.assert_called()

    @mock.patch("CIME.bless_test_results.bless_history")
    @mock.patch("CIME.bless_test_results.Case")
    @mock.patch("CIME.bless_test_results.TestStatus")
    @mock.patch("CIME.bless_test_results.get_test_status_files")
    def test_bless_hist_only(
        self,
        get_test_status_files,
        TestStatus,
        Case,
        bless_history,
    ):
        get_test_status_files.return_value = [
            "/tmp/cases/SMS.f19_g16.S.docker_gnu/TestStatus",
        ]

        ts = TestStatus.return_value
        ts.get_name.return_value = "SMS.f19_g16.S.docker_gnu"
        ts.get_overall_test_status.return_value = ("PASS", "RUN")
        ts.get_status.side_effect = ["PASS", "FAIL"]

        case = Case.return_value.__enter__.return_value

        bless_history.return_value = (True, "")

        success = bless_test_results(
            "master",
            "/tmp/baseline",
            "/tmp/cases",
            "gnu",
            force=True,
            hist_only=True,
        )

        assert success
        bless_history.assert_called()

    @mock.patch("CIME.bless_test_results.Case")
    @mock.patch("CIME.bless_test_results.TestStatus")
    @mock.patch("CIME.bless_test_results.get_test_status_files")
    def test_specific(self, get_test_status_files, TestStatus, Case):
        get_test_status_files.return_value = [
            "/tmp/cases/SMS.f19_g16.S.docker_gnu.12345/TestStatus",
            "/tmp/cases/PET.f19_g16.S.docker-gnu.12345/TestStatus",
        ]

        ts = TestStatus.return_value
        ts.get_name.return_value = "SMS.f19_g16.S.docker_gnu"
        ts.get_overall_test_status.return_value = ("PASS", "RUN")
        ts.get_status.side_effect = ["PASS"] * 10

        case = Case.return_value.__enter__.return_value

        success = bless_test_results(
            "master",
            "/tmp/baseline",
            "/tmp/cases",
            "gnu",
            force=True,
            bless_tests=["SMS"],
        )

        assert success

    @mock.patch("CIME.bless_test_results._bless_memory")
    @mock.patch("CIME.bless_test_results._bless_throughput")
    @mock.patch("CIME.bless_test_results.bless_history")
    @mock.patch("CIME.bless_test_results.bless_namelists")
    @mock.patch("CIME.bless_test_results.Case")
    @mock.patch("CIME.bless_test_results.TestStatus")
    @mock.patch("CIME.bless_test_results.get_test_status_files")
    def test_bless_tests_results_homme(
        self,
        get_test_status_files,
        TestStatus,
        Case,
        bless_namelists,
        bless_history,
        _bless_throughput,
        _bless_memory,
    ):
        _bless_memory.return_value = (False, "")

        _bless_throughput.return_value = (False, "")

        bless_history.return_value = (False, "")

        bless_namelists.return_value = (False, "")

        get_test_status_files.return_value = [
            "/tmp/cases/SMS.f19_g16.S.docker_gnu.12345/TestStatus",
            "/tmp/cases/PET.f19_g16.S.docker-gnu.12345/TestStatus",
        ]

        ts = TestStatus.return_value
        ts.get_name.return_value = "SMS.f19_g16.HOMME.docker_gnu"
        ts.get_overall_test_status.return_value = ("PASS", "RUN")
        ts.get_status.side_effect = ["PASS", "PASS", "PASS", "PASS", "PASS"]

        case = Case.return_value.__enter__.return_value

        success = bless_test_results(
            "master",
            "/tmp/baseline",
            "/tmp/cases",
            "gnu",
            force=True,
            no_skip_pass=True,
        )

        assert not success

    @mock.patch("CIME.bless_test_results._bless_memory")
    @mock.patch("CIME.bless_test_results._bless_throughput")
    @mock.patch("CIME.bless_test_results.bless_history")
    @mock.patch("CIME.bless_test_results.bless_namelists")
    @mock.patch("CIME.bless_test_results.Case")
    @mock.patch("CIME.bless_test_results.TestStatus")
    @mock.patch("CIME.bless_test_results.get_test_status_files")
    def test_bless_tests_results_fail(
        self,
        get_test_status_files,
        TestStatus,
        Case,
        bless_namelists,
        bless_history,
        _bless_throughput,
        _bless_memory,
    ):
        _bless_memory.return_value = (False, "")

        _bless_throughput.return_value = (False, "")

        bless_history.return_value = (False, "")

        bless_namelists.return_value = (False, "")

        get_test_status_files.return_value = [
            "/tmp/cases/SMS.f19_g16.S.docker_gnu.12345/TestStatus",
            "/tmp/cases/PET.f19_g16.S.docker-gnu.12345/TestStatus",
        ]

        ts = TestStatus.return_value
        ts.get_name.return_value = "SMS.f19_g16.S.docker_gnu"
        ts.get_overall_test_status.return_value = ("PASS", "RUN")
        ts.get_status.side_effect = ["PASS", "PASS", "PASS", "PASS", "PASS"]

        case = Case.return_value.__enter__.return_value

        success = bless_test_results(
            "master",
            "/tmp/baseline",
            "/tmp/cases",
            "gnu",
            force=True,
            no_skip_pass=True,
        )

        assert not success

    @mock.patch("CIME.bless_test_results._bless_memory")
    @mock.patch("CIME.bless_test_results._bless_throughput")
    @mock.patch("CIME.bless_test_results.bless_history")
    @mock.patch("CIME.bless_test_results.bless_namelists")
    @mock.patch("CIME.bless_test_results.Case")
    @mock.patch("CIME.bless_test_results.TestStatus")
    @mock.patch("CIME.bless_test_results.get_test_status_files")
    def test_no_skip_pass(
        self,
        get_test_status_files,
        TestStatus,
        Case,
        bless_namelists,
        bless_history,
        _bless_throughput,
        _bless_memory,
    ):
        _bless_memory.return_value = (True, "")

        _bless_throughput.return_value = (True, "")

        bless_history.return_value = (True, "")

        bless_namelists.return_value = (True, "")

        get_test_status_files.return_value = [
            "/tmp/cases/SMS.f19_g16.S.docker_gnu.12345/TestStatus",
            "/tmp/cases/PET.f19_g16.S.docker-gnu.12345/TestStatus",
        ]

        ts = TestStatus.return_value
        ts.get_name.return_value = "SMS.f19_g16.S.docker_gnu"
        ts.get_overall_test_status.return_value = ("PASS", "RUN")
        ts.get_status.side_effect = ["PASS", "PASS", "PASS", "PASS", "PASS"]

        case = Case.return_value.__enter__.return_value

        success = bless_test_results(
            "master",
            "/tmp/baseline",
            "/tmp/cases",
            "gnu",
            force=True,
            no_skip_pass=True,
        )

        assert success

    @mock.patch("CIME.bless_test_results.Case")
    @mock.patch("CIME.bless_test_results.TestStatus")
    @mock.patch("CIME.bless_test_results.get_test_status_files")
    def test_baseline_root_none(self, get_test_status_files, TestStatus, Case):
        get_test_status_files.return_value = [
            "/tmp/cases/SMS.f19_g16.S.docker_gnu.12345/TestStatus",
            "/tmp/cases/PET.f19_g16.S.docker-gnu.12345/TestStatus",
        ]

        ts = TestStatus.return_value
        ts.get_name.return_value = "SMS.f19_g16.S.docker_gnu"
        ts.get_overall_test_status.return_value = ("PASS", "RUN")
        ts.get_status.side_effect = ["FAIL"] + ["PASS"] * 9

        case = Case.return_value.__enter__.return_value
        case.get_value.side_effect = [None, None]

        success = bless_test_results(
            "master",
            None,
            "/tmp/cases",
            "gnu",
            force=True,
        )

        assert not success

    @mock.patch("CIME.bless_test_results.bless_namelists")
    @mock.patch("CIME.bless_test_results.Case")
    @mock.patch("CIME.bless_test_results.TestStatus")
    @mock.patch("CIME.bless_test_results.get_test_status_files")
    def test_baseline_name_none(
        self, get_test_status_files, TestStatus, Case, bless_namelists
    ):
        bless_namelists.return_value = (True, "")

        get_test_status_files.return_value = [
            "/tmp/cases/SMS.f19_g16.S.docker_gnu.12345/TestStatus",
        ]

        ts = TestStatus.return_value
        ts.get_name.return_value = "SMS.f19_g16.S.docker_gnu"
        ts.get_overall_test_status.return_value = ("PASS", "RUN")
        ts.get_status.side_effect = ["FAIL"] + ["PASS"] * 9

        case = Case.return_value.__enter__.return_value
        case.get_value.side_effect = [None, None]

        success = bless_test_results(
            None,
            "/tmp/baselines",
            "/tmp/cases",
            "gnu",
            force=True,
        )

        assert success

    @mock.patch("CIME.bless_test_results.Case")
    @mock.patch("CIME.bless_test_results.TestStatus")
    @mock.patch("CIME.bless_test_results.get_test_status_files")
    def test_exclude(self, get_test_status_files, TestStatus, Case):
        get_test_status_files.return_value = [
            "/tmp/cases/SMS.f19_g16.S.docker_gnu.12345/TestStatus",
            "/tmp/cases/PET.f19_g16.S.docker-gnu.12345/TestStatus",
        ]

        ts = TestStatus.return_value
        ts.get_name.return_value = "SMS.f19_g16.S.docker_gnu"
        ts.get_overall_test_status.return_value = ("PASS", "RUN")
        ts.get_status.side_effect = ["PASS", "PASS", "PASS", "PASS", "PASS"]

        case = Case.return_value.__enter__.return_value

        success = bless_test_results(
            "master",
            "/tmp/baseline",
            "/tmp/cases",
            "gnu",
            force=True,
            exclude="SMS",
        )

        assert success

    @mock.patch("CIME.bless_test_results.Case")
    @mock.patch("CIME.bless_test_results.TestStatus")
    @mock.patch("CIME.bless_test_results.get_test_status_files")
    def test_multiple_files(self, get_test_status_files, TestStatus, Case):
        get_test_status_files.return_value = [
            "/tmp/cases/SMS.f19_g16.S.docker_gnu.12345/TestStatus",
            "/tmp/cases/SMS.f19_g16.S.docker-gnu.23456/TestStatus",
        ]

        ts = TestStatus.return_value
        ts.get_name.return_value = "SMS.f19_g16.S.docker_gnu"
        ts.get_overall_test_status.return_value = ("PASS", "RUN")
        ts.get_status.side_effect = ["PASS", "PASS", "PASS", "PASS", "PASS"]

        case = Case.return_value.__enter__.return_value

        success = bless_test_results(
            "master",
            "/tmp/baseline",
            "/tmp/cases",
            "gnu",
            force=True,
        )

        assert success

    @mock.patch("CIME.bless_test_results.Case")
    @mock.patch("CIME.bless_test_results.TestStatus")
    @mock.patch("CIME.bless_test_results.get_test_status_files")
    def test_bless_tests_no_match(self, get_test_status_files, TestStatus, Case):
        get_test_status_files.return_value = [
            "/tmp/cases/SMS.f19_g16.S.docker_gnu/TestStatus",
            "/tmp/cases/PET.f19_g16.S.docker_gnu/TestStatus",
        ]

        ts = TestStatus.return_value
        ts.get_name.return_value = "SMS.f19_g16.S.docker_gnu"
        ts.get_overall_test_status.return_value = ("PASS", "RUN")
        ts.get_status.side_effect = ["PASS"] * 10

        case = Case.return_value.__enter__.return_value

        success = bless_test_results(
            "master",
            "/tmp/baseline",
            "/tmp/cases",
            "gnu",
            force=True,
            bless_tests=["SEQ"],
        )

        assert success

    @mock.patch("CIME.bless_test_results.Case")
    @mock.patch("CIME.bless_test_results.TestStatus")
    @mock.patch("CIME.bless_test_results.get_test_status_files")
    def test_bless_all(self, get_test_status_files, TestStatus, Case):
        get_test_status_files.return_value = [
            "/tmp/cases/SMS.f19_g16.S.docker_gnu/TestStatus",
        ]

        ts = TestStatus.return_value
        ts.get_name.return_value = "SMS.f19_g16.S.docker_gnu"
        ts.get_overall_test_status.return_value = ("PASS", "RUN")
        ts.get_status.side_effect = ["PASS", "PASS", "PASS", "PASS", "PASS"]

        case = Case.return_value.__enter__.return_value

        success = bless_test_results(
            "master",
            "/tmp/baseline",
            "/tmp/cases",
            "gnu",
            force=True,
        )

        assert success

    def test_is_bless_needed_no_skip_fail(self):
        ts = mock.MagicMock()
        ts.get_status.side_effect = [
            "PASS",
        ]

        broken_blesses = []

        needed = is_bless_needed(
            "SMS.f19_g16.A", ts, broken_blesses, "PASS", True, "RUN"
        )

        assert needed
        assert broken_blesses == []

    def test_is_bless_needed_overall_fail(self):
        ts = mock.MagicMock()
        ts.get_status.side_effect = [
            "PASS",
        ]

        broken_blesses = []

        needed = is_bless_needed(
            "SMS.f19_g16.A", ts, broken_blesses, "FAIL", False, "RUN"
        )

        assert not needed
        assert broken_blesses == [("SMS.f19_g16.A", "test did not pass")]

    def test_is_bless_needed_baseline_fail(self):
        ts = mock.MagicMock()
        ts.get_status.side_effect = ["PASS", "FAIL"]

        broken_blesses = []

        needed = is_bless_needed(
            "SMS.f19_g16.A", ts, broken_blesses, "PASS", False, "RUN"
        )

        assert needed
        assert broken_blesses == []

    def test_is_bless_needed_run_phase_fail(self):
        ts = mock.MagicMock()
        ts.get_status.side_effect = [
            "FAIL",
        ]

        broken_blesses = []

        needed = is_bless_needed(
            "SMS.f19_g16.A", ts, broken_blesses, "PASS", False, "RUN"
        )

        assert not needed
        assert broken_blesses == [("SMS.f19_g16.A", "run phase did not pass")]

    def test_is_bless_needed_no_run_phase(self):
        ts = mock.MagicMock()
        ts.get_status.side_effect = [None]

        broken_blesses = []

        needed = is_bless_needed(
            "SMS.f19_g16.A", ts, broken_blesses, "PASS", False, "RUN"
        )

        assert not needed
        assert broken_blesses == [("SMS.f19_g16.A", "no run phase")]

    def test_is_bless_needed(self):
        ts = mock.MagicMock()
        ts.get_status.side_effect = ["PASS", "PASS"]

        broken_blesses = []

        needed = is_bless_needed(
            "SMS.f19_g16.A", ts, broken_blesses, "PASS", False, "RUN"
        )

        assert not needed
