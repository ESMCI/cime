import logging
import subprocess

import pytest

from CIME import get_timing
from CIME.gitinterface import GitInterface

LID = "123456-654321"


@pytest.fixture
def case_repo(tmp_path, monkeypatch):
    # append_case_status writes CaseStatus into the working directory, which is the
    # case root when the model runs
    monkeypatch.chdir(tmp_path)
    # Commits need an identity, which a CI machine may not have configured
    for var in ("GIT_AUTHOR", "GIT_COMMITTER"):
        monkeypatch.setenv(var + "_NAME", "test")
        monkeypatch.setenv(var + "_EMAIL", "test@example.com")
    (tmp_path / "timing").mkdir()
    return tmp_path


def _committed_files(caseroot):
    return subprocess.run(
        ["git", "-C", str(caseroot), "ls-tree", "-r", "--name-only", "HEAD"],
        capture_output=True,
        text=True,
    ).stdout.split()


@pytest.mark.parametrize("use_gitpython", [True, False])
def test_timing_files_for_this_run_are_committed(case_repo, monkeypatch, use_gitpython):
    gitinterface = GitInterface(str(case_repo), logging.getLogger(__name__))
    if not gitinterface._defined:
        pytest.skip("git 2.28 or newer is required")
    if use_gitpython and not gitinterface._use_module:
        pytest.skip("GitPython is not installed")
    # _use_module is how GitInterface chooses between GitPython and the shell
    monkeypatch.setattr(gitinterface, "_use_module", use_gitpython)
    timing_file = "cesm_timing.case." + LID
    (case_repo / "timing" / timing_file).touch()

    get_timing._report_timing_files(str(case_repo), gitinterface, LID)

    assert "timing/" + timing_file in _committed_files(case_repo)


@pytest.mark.parametrize(
    "older_timing_files", [[], ["cesm.ESMF_Profile.summary.000000-000000"]]
)
def test_no_timing_files_for_this_run_commits_nothing(case_repo, older_timing_files):
    for name in older_timing_files:
        (case_repo / "timing" / name).touch()
    gitinterface = GitInterface(str(case_repo), logging.getLogger(__name__))
    if not gitinterface._defined:
        pytest.skip("git 2.28 or newer is required")

    get_timing._report_timing_files(str(case_repo), gitinterface, LID)

    assert _committed_files(case_repo) == []
