"""Unit tests for the pytest runner CLI."""

from argparse import Namespace
from contextlib import contextmanager
import importlib.util
from pathlib import Path
from subprocess import CompletedProcess
import sys
from importlib.machinery import SourceFileLoader

import pytest

RUNNER_PATH = Path(__file__).resolve().parents[2] / "devtools" / "run_tests"
RUNNER_LOADER = SourceFileLoader("cime_test_runner", str(RUNNER_PATH))
RUNNER_SPEC = importlib.util.spec_from_loader(RUNNER_LOADER.name, RUNNER_LOADER)
assert RUNNER_SPEC is not None
assert RUNNER_SPEC.loader is not None
run_tests = importlib.util.module_from_spec(RUNNER_SPEC)
sys.modules[RUNNER_SPEC.name] = run_tests
RUNNER_SPEC.loader.exec_module(run_tests)


def test_parse_command_line_accepts_multiple_targets():
    # Context
    argv = [
        "unit",
        "--backend",
        "host",
        "--",
        "CIME/tests/test_unit_a.py",
        "CIME/tests/test_unit_b.py::TestB::test_case",
    ]

    # Act
    args = run_tests.parse_command_line(argv)

    # Assert
    assert args.suite == "unit"
    assert args.targets == [
        "CIME/tests/test_unit_a.py",
        "CIME/tests/test_unit_b.py::TestB::test_case",
    ]


def test_parse_command_line_accepts_all_suite():
    # Context
    argv = ["all"]

    # Act
    args = run_tests.parse_command_line(argv)

    # Assert
    assert args.suite == "all"


def test_suite_patterns_select_unit_and_system_tests_for_all():
    # Context
    suite = "all"

    # Act
    patterns = run_tests._suite_patterns(suite)

    # Assert
    assert patterns == ("unit", "sys")


def test_model_checkout_detects_e3sm(tmp_path):
    # Context
    cime_root = tmp_path / "cime"
    model_root = tmp_path
    (model_root / "cime_config").mkdir()
    (model_root / "components").mkdir()

    # Act
    detected_root, model = run_tests._model_checkout(cime_root)

    # Assert
    assert detected_root == model_root
    assert model == "e3sm"


def test_model_checkout_rejects_unsupported_model(tmp_path):
    # Context
    cime_root = tmp_path / "cime"
    (tmp_path / "cime_config").mkdir()
    (tmp_path / "components").mkdir()
    (tmp_path / ".cime_model_id").write_text("noresm\n")

    # Act / Assert
    with pytest.raises(run_tests.RunnerError, match="supports E3SM and CESM"):
        run_tests._model_checkout(cime_root)


def test_machine_list_reads_current_machine():
    # Context
    listing = CompletedProcess(
        args=[],
        returncode=0,
        stdout="Machine(s)\n\n  linux-generic : generic\n  WSL2 : WSL\n",
        stderr="",
    )
    current_machine = CompletedProcess(
        args=[],
        returncode=0,
        stdout="Machine(s)\n\n  WSL2 (current) : WSL\n",
        stderr="",
    )
    results = iter([listing, current_machine])
    commands = []

    def fake_run(command, **kwargs):
        commands.append(command)
        return next(results)

    # Act
    names, current = run_tests._machine_list(Path("/tmp/cime"), run=fake_run)

    # Assert
    assert names == {"linux-generic", "WSL2"}
    assert current == "WSL2"
    assert commands == [
        ["/tmp/cime/scripts/query_config", "--machines"],
        ["/tmp/cime/scripts/query_config", "--machines", "current"],
    ]


def test_machine_list_reports_query_failure():
    # Context
    result = CompletedProcess(args=[], returncode=1, stdout="", stderr="bad config")

    # Act / Assert
    with pytest.raises(run_tests.RunnerError, match="bad config"):
        run_tests._machine_list(Path("/tmp/cime"), run=lambda *a, **k: result)


def test_machine_list_reports_current_machine_query_failure():
    # Context
    listing = CompletedProcess(
        args=[], returncode=0, stdout="Machine(s)\n  WSL2 : local\n", stderr=""
    )
    current_query = CompletedProcess(
        args=[], returncode=1, stdout="", stderr="unexpected query failure"
    )
    results = iter([listing, current_query])

    # Act / Assert
    with pytest.raises(run_tests.RunnerError, match="unexpected query failure"):
        run_tests._machine_list(Path("/tmp/cime"), run=lambda *a, **k: next(results))


def test_machine_list_handles_machine_query_output_without_current_marker():
    # Context
    listing = CompletedProcess(
        args=[], returncode=0, stdout="Machine(s)\n  WSL2 : local\n", stderr=""
    )
    machine_query = CompletedProcess(
        args=[], returncode=1, stdout="", stderr="No machine None found"
    )
    results = iter([listing, machine_query])

    # Act
    names, current = run_tests._machine_list(
        Path("/tmp/cime"), run=lambda *a, **k: next(results)
    )

    # Assert
    assert names == {"WSL2"}
    assert current is None


def test_find_host_python_accepts_python_310(monkeypatch):
    # Context
    monkeypatch.setattr(run_tests.shutil, "which", lambda _: "/usr/bin/python3")
    monkeypatch.setattr(
        run_tests.subprocess,
        "run",
        lambda *a, **k: CompletedProcess(args=[], returncode=0, stdout="3.10\n"),
    )

    # Act
    python = run_tests._find_host_python()

    # Assert
    assert python == "/usr/bin/python3"


def test_find_host_python_rejects_python_39(monkeypatch):
    # Context
    monkeypatch.setattr(run_tests.shutil, "which", lambda _: "/usr/bin/python3")
    monkeypatch.setattr(
        run_tests.subprocess,
        "run",
        lambda *a, **k: CompletedProcess(args=[], returncode=0, stdout="3.9\n"),
    )

    # Act / Assert
    with pytest.raises(run_tests.RunnerError, match="Python 3.10 or newer"):
        run_tests._find_host_python()


def test_choose_backend_prefers_matching_host(monkeypatch, tmp_path):
    # Context
    args = Namespace(backend="auto", suite="unit", build_image=False)
    listing = CompletedProcess(
        args=[],
        returncode=0,
        stdout="Machine(s)\n  WSL2 (current) : local\n",
        stderr="",
    )
    monkeypatch.setattr(run_tests.shutil, "which", lambda _: "/usr/bin/docker")
    results = iter(
        [
            listing,
            CompletedProcess(
                args=[],
                returncode=0,
                stdout="Machine(s)\n  WSL2 (current) : local\n",
                stderr="",
            ),
        ]
    )

    # Act
    backend, machine, names = run_tests._choose_backend(
        args,
        tmp_path / "cime",
        run=lambda *a, **k: next(results),
    )

    # Assert
    assert (backend, machine) == ("host", "WSL2")
    assert names == {"WSL2"}


def test_choose_backend_rejects_system_without_host_or_runtime(monkeypatch, tmp_path):
    # Context
    args = Namespace(backend="auto", suite="system", build_image=False)
    listing = CompletedProcess(
        args=[], returncode=0, stdout="Machine(s)\n  cluster : remote\n", stderr=""
    )
    no_current_machine = CompletedProcess(
        args=[],
        returncode=1,
        stdout="",
        stderr="No machine None found",
    )
    monkeypatch.setattr(run_tests.shutil, "which", lambda _: None)
    results = iter(
        [
            listing,
            no_current_machine,
        ]
    )

    # Act / Assert
    with pytest.raises(run_tests.RunnerError, match="System tests require"):
        run_tests._choose_backend(
            args,
            tmp_path / "cime",
            run=lambda *a, **k: next(results),
        )


def test_choose_backend_build_image_requires_docker(monkeypatch, tmp_path):
    # Context
    args = Namespace(backend="auto", suite="unit", build_image=True)
    listing = CompletedProcess(
        args=[], returncode=0, stdout="Machine(s)\n  cluster : remote\n", stderr=""
    )
    no_current_machine = CompletedProcess(
        args=[],
        returncode=1,
        stdout="",
        stderr="No machine None found",
    )
    results = iter(
        [
            listing,
            no_current_machine,
        ]
    )
    monkeypatch.setattr(run_tests.shutil, "which", lambda _: None)

    # Act / Assert
    with pytest.raises(run_tests.RunnerError, match="requires Docker"):
        run_tests._choose_backend(
            args,
            tmp_path / "cime",
            run=lambda *a, **k: next(results),
        )


def test_container_targets_accept_multiple_node_ids(tmp_path):
    # Context
    targets = [
        "CIME/tests/test_unit_a.py",
        "CIME/tests/test_unit_b.py::TestB::test_case",
    ]

    # Act
    selected = run_tests._container_targets(tmp_path, targets, "unit")

    # Assert
    assert selected == targets


def test_container_targets_include_both_suites_for_all(tmp_path):
    # Context
    (tmp_path / "CIME" / "tests").mkdir(parents=True)
    (tmp_path / "CIME" / "tests" / "test_unit_example.py").touch()
    (tmp_path / "CIME" / "tests" / "test_sys_example.py").touch()

    # Act
    selected = run_tests._container_targets(tmp_path, [], "all")

    # Assert
    assert selected == [
        "CIME/tests/test_sys_example.py",
        "CIME/tests/test_unit_example.py",
    ]


def test_container_targets_reject_paths_outside_checkout(tmp_path):
    # Context
    outside = tmp_path.parent / "outside.py"

    # Act / Assert
    with pytest.raises(run_tests.RunnerError, match="inside the CIME checkout"):
        run_tests._container_targets(tmp_path, [str(outside)], "unit")


def test_container_command_mounts_input_data_for_system_suite(tmp_path):
    # Context
    model_root = tmp_path / "model"
    cime_root = model_root / "cime"
    cime_root.mkdir(parents=True)
    artifacts = tmp_path / "artifacts"
    inputdata = tmp_path / "inputdata"

    # Act
    command = run_tests._container_command(
        "docker",
        "cime:test",
        "e3sm",
        model_root,
        cime_root,
        artifacts,
        inputdata,
        "system",
        ["CIME/tests/test_sys_a.py", "CIME/tests/test_sys_b.py::test_b"],
    )

    # Assert
    assert command.count(f"{inputdata}:/root/storage/inputdata") == 1
    assert "--platform" in command
    assert command[command.index("--platform") + 1] == "linux/amd64"
    assert command.index(f"{inputdata}:/root/storage/inputdata") < command.index(
        "cime:test"
    )
    assert "--no-teardown" in command
    assert "--no-batch" in command
    assert "--cov=CIME" in command
    assert "--cov-branch" in command
    assert "--cov-report=term-missing" in command
    assert not any(argument.startswith("--junitxml") for argument in command)
    assert command[-2:] == [
        "CIME/tests/test_sys_a.py",
        "CIME/tests/test_sys_b.py::test_b",
    ]


def test_container_command_combines_suites_and_uses_total_coverage(tmp_path):
    # Context
    model_root = tmp_path / "model"
    cime_root = model_root / "cime"
    cime_root.mkdir(parents=True)
    (cime_root / "CIME" / "tests").mkdir(parents=True)
    (cime_root / "CIME" / "tests" / "test_unit_example.py").touch()
    (cime_root / "CIME" / "tests" / "test_sys_example.py").touch()
    inputdata = tmp_path / "inputdata"

    # Act
    command = run_tests._container_command(
        "docker",
        "cime:test",
        "e3sm",
        model_root,
        cime_root,
        tmp_path / "artifacts",
        inputdata,
        "all",
        [],
    )

    # Assert
    assert "--shm-size=1g" in command
    assert f"{inputdata}:/root/storage/inputdata" in command
    assert "--cov=CIME" in command
    assert "--cov-branch" in command
    assert "--cov-report=term-missing" in command
    assert "CIME/tests/test_unit_example.py" in command
    assert "CIME/tests/test_sys_example.py" in command
    assert any(
        argument.startswith("--deselect=CIME/tests/test_sys_full_system.py")
        for argument in command
    )


def test_container_command_does_not_mount_input_data_for_unit_suite(tmp_path):
    # Context
    model_root = tmp_path / "model"
    cime_root = model_root / "cime"
    cime_root.mkdir(parents=True)
    inputdata = tmp_path / "inputdata"

    # Act
    command = run_tests._container_command(
        "docker",
        "cime:test",
        "e3sm",
        model_root,
        cime_root,
        tmp_path / "artifacts",
        inputdata,
        "unit",
        ["CIME/tests/test_unit_a.py"],
    )

    # Assert
    assert f"{inputdata}:/root/storage/inputdata" not in command


def test_inputdata_cache_is_populated_and_reused(tmp_path):
    # Context
    cime_root = tmp_path / "cime"
    (cime_root / "docker").mkdir(parents=True)
    (cime_root / "docker" / "INPUTDATA_VERSION").write_text("2\n")
    calls = []

    def fake_run(command, cwd, capture_output=False, env=None):
        calls.append(command)
        if command[1] == "create":
            return CompletedProcess(command, 0, stdout="container-id\n", stderr="")
        if command[1] == "cp":
            destination = Path(command[-1])
            (destination / "share").mkdir()
            (destination / "share" / "domain.nc").write_text("data")
        return CompletedProcess(command, 0, stdout="", stderr="")

    # Act
    cache = run_tests._populate_inputdata(
        "docker", cime_root, tmp_path / "cache", run=fake_run
    )
    reused_cache = run_tests._populate_inputdata(
        "docker", cime_root, tmp_path / "cache", run=fake_run
    )

    # Assert
    assert cache == reused_cache
    assert (cache / "share" / "domain.nc").read_text() == "data"
    assert len(calls) == 4
    assert calls[-1] == ["docker", "rm", "container-id"]


def test_inputdata_cache_reuses_cache_published_while_waiting_for_lock(
    monkeypatch, tmp_path
):
    # Context
    cime_root = tmp_path / "cime"
    (cime_root / "docker").mkdir(parents=True)
    (cime_root / "docker" / "INPUTDATA_VERSION").write_text("2\n")
    cache = tmp_path / "cache" / "inputdata" / "v2"
    calls = []

    @contextmanager
    def publish_cache_before_lock(_cache):
        cache.mkdir(parents=True)
        (cache / "share").mkdir()
        (cache / "share" / "domain.nc").write_text("data")
        (cache / ".cime-inputdata-complete").write_text("image=test\n")
        yield

    def fake_run(command, cwd, capture_output=False, env=None):
        calls.append(command)
        return CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(run_tests, "_inputdata_cache_lock", publish_cache_before_lock)

    # Act
    result = run_tests._populate_inputdata(
        "docker", cime_root, tmp_path / "cache", run=fake_run
    )

    # Assert
    assert result == cache
    assert (cache / "share" / "domain.nc").read_text() == "data"
    assert calls == []


def test_inputdata_cache_extraction_failure_preserves_existing_cache(tmp_path):
    # Context
    cime_root = tmp_path / "cime"
    (cime_root / "docker").mkdir(parents=True)
    (cime_root / "docker" / "INPUTDATA_VERSION").write_text("2\n")
    cache = tmp_path / "cache" / "inputdata" / "v2"
    cache.mkdir(parents=True)
    (cache / "existing.txt").write_text("old cache")
    calls = []

    def failed_copy(command, cwd, capture_output=False, env=None):
        calls.append(command)
        if command[1] == "create":
            return CompletedProcess(command, 0, stdout="container-id\n", stderr="")
        if command[1] == "cp":
            return CompletedProcess(command, 1, stdout="", stderr="copy failed")
        return CompletedProcess(command, 0, stdout="", stderr="")

    # Act / Assert
    with pytest.raises(run_tests.RunnerError, match="extract input data"):
        run_tests._populate_inputdata(
            "docker", cime_root, tmp_path / "cache", run=failed_copy
        )

    # Assert prior usable cache is left intact and temp container is removed.
    assert (cache / "existing.txt").read_text() == "old cache"
    assert calls[-1] == ["docker", "rm", "container-id"]


def test_artifact_dir_rejects_existing_override(tmp_path):
    # Context
    artifacts = tmp_path / "existing"
    artifacts.mkdir()

    # Act / Assert
    with pytest.raises(run_tests.RunnerError, match="already exists"):
        run_tests._artifact_dir(artifacts)


def test_system_host_batch_requires_approval(monkeypatch, tmp_path):
    # Context
    args = Namespace(
        suite="system",
        backend="auto",
        artifact_dir=tmp_path / "artifacts",
        allow_batch=False,
        python=None,
        cache_dir=tmp_path / "cache",
        targets=[],
        build_image=False,
        image="ghcr.io/esmci/cime:latest",
    )
    monkeypatch.setattr(
        run_tests, "_model_checkout", lambda root: (root.parent, "e3sm")
    )
    monkeypatch.setattr(
        run_tests, "_choose_backend", lambda *a, **k: ("host", "batch-host", set())
    )
    monkeypatch.setattr(run_tests, "_host_has_batch", lambda *a, **k: True)

    # Act / Assert
    with pytest.raises(run_tests.RunnerError, match="Ask the user for approval"):
        run_tests.run_tests(args, cime_root=tmp_path / "cime")


def test_system_host_batch_runs_after_approval(monkeypatch, tmp_path):
    # Context
    args = Namespace(
        suite="system",
        backend="auto",
        artifact_dir=tmp_path / "artifacts",
        allow_batch=True,
        python="python3",
        cache_dir=tmp_path / "cache",
        targets=["CIME/tests/test_sys_a.py"],
        build_image=False,
        image="ghcr.io/esmci/cime:latest",
    )
    monkeypatch.setattr(
        run_tests, "_model_checkout", lambda root: (root.parent, "e3sm")
    )
    monkeypatch.setattr(
        run_tests, "_choose_backend", lambda *a, **k: ("host", "batch-host", set())
    )
    monkeypatch.setattr(run_tests, "_host_has_batch", lambda *a, **k: True)
    monkeypatch.setattr(
        run_tests, "_host_environment", lambda *a, **k: "/venv/bin/python"
    )
    commands = []

    def fake_run(command, cwd):
        commands.append(command)
        return CompletedProcess(command, 0)

    # Act
    status = run_tests.run_tests(args, cime_root=tmp_path / "cime", run=fake_run)

    # Assert
    assert status == 0
    assert len(commands) == 1
    assert "--no-batch" not in commands[0]
