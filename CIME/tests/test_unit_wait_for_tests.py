#!/usr/bin/env python3

"""Unit tests for the CDash submission helpers in :mod:`CIME.wait_for_tests`.

``ctest -D NightlySubmit`` uploads the XML files in ``Testing/<tag>/`` one at
a time and aborts on the first failure. Files accepted before the failure are
already part of the CDash build, and CDash appends (rather than replaces)
tests submitted for an existing build, so blindly retrying the whole
submission duplicates every test on the dashboard. These tests verify that
retries only resend the files that were not yet accepted.
"""

import pytest

from CIME import wait_for_tests

CTEST_PARTIAL_FAILURE = """\
Submit files
   SubmitURL: https://my.cdash.org/submit.php?project=E3SM
   Upload file: /tmp/x/Testing/20261117-1352/Configure.xml to https://my.cdash.org/submit.php Size: 419
   Uploaded: /tmp/x/Testing/20261117-1352/Configure.xml
   Upload file: /tmp/x/Testing/20261117-1352/Build.xml to https://my.cdash.org/submit.php Size: 10722
   Uploaded: /tmp/x/Testing/20261117-1352/Build.xml
   Upload file: /tmp/x/Testing/20261117-1352/Test.xml to https://my.cdash.org/submit.php Size: 3904797
   Uploaded: /tmp/x/Testing/20261117-1352/Test.xml
   Upload file: /tmp/x/Testing/20261117-1352/Notes.xml to https://my.cdash.org/submit.php Size: 517
   Error when uploading file: /tmp/x/Testing/20261117-1352/Notes.xml
   Error message was: OpenSSL SSL_connect: Connection reset by peer in connection to my.cdash.org:443
   Problems when submitting via HTTP
Errors while running CTest
"""

CTEST_NOTES_UPLOADED_FAILURE = """\
   Uploaded: /tmp/x/Testing/20261117-1352/Configure.xml
   Uploaded: /tmp/x/Testing/20261117-1352/Build.xml
   Uploaded: /tmp/x/Testing/20261117-1352/Test.xml
   Uploaded: /tmp/x/Testing/20261117-1352/Notes.xml
   Error when uploading file: /tmp/x/Testing/20261117-1352/Upload.xml
   Problems when submitting via HTTP
"""

CTEST_SUCCESS = """\
   Uploaded: /tmp/x/Testing/20261117-1352/Upload.xml
   Uploaded: /tmp/x/Testing/20261117-1352/Done.xml
   Submission successful
"""

XML_FILES = ("Configure.xml", "Build.xml", "Test.xml", "Upload.xml")


class FakeRunner:
    """Scripted stand-in for ``run_cmd`` that records what ctest would see."""

    def __init__(self, results, testtime_dir):
        self._results = list(results)
        self._testtime_dir = testtime_dir
        self.commands = []
        self.from_dirs = []
        self.files_seen = []
        self.drop_methods = []

    def __call__(self, cmd, combine_output=False, from_dir=None):
        self.commands.append(cmd)
        self.from_dirs.append(from_dir)
        self.files_seen.append(sorted(p.name for p in self._testtime_dir.iterdir()))
        dart = (self._testtime_dir.parent.parent / "DartConfiguration.tcl").read_text()
        self.drop_methods.append(
            [
                line.split(":", 1)[1].strip()
                for line in dart.splitlines()
                if line.startswith("DropMethod:")
            ][0]
        )
        stat, out = self._results.pop(0)
        return stat, out, ""


@pytest.fixture
def cdash_tree(tmp_path):
    """Create a fake ctest tree ``<tmp>/Testing/<tag>/`` populated with XML files."""
    testtime_dir = tmp_path / "Testing" / "20261117-1352"
    testtime_dir.mkdir(parents=True)
    for name in XML_FILES:
        (testtime_dir / name).write_text(f"<{name}/>")
    (tmp_path / "notes.txt").write_text("notes\n")
    return tmp_path, testtime_dir


def _submit(tmp_path, testtime_dir, runner, uploaded):
    return wait_for_tests.submit_cdash_files(
        tmp_path,
        testtime_dir,
        cdash_build_name="build",
        cdash_project="E3SM",
        hostname="chrysalis",
        cdash_timestamp="13:52:00",
        uploaded=uploaded,
        run_cmd_func=runner,
    )


def test_parse_uploaded_files_returns_basenames():
    # Act
    uploaded = wait_for_tests.parse_uploaded_files(CTEST_PARTIAL_FAILURE)

    # Assert
    assert uploaded == {"Configure.xml", "Build.xml", "Test.xml"}


def test_parse_uploaded_files_ignores_failed_and_unrelated_lines():
    # Context
    output = "   Upload file: /tmp/x/Test.xml to https://host Size: 1\n   Error when uploading file: /tmp/x/Test.xml\n"

    # Act
    uploaded = wait_for_tests.parse_uploaded_files(output)

    # Assert
    assert uploaded == set()


def test_parse_uploaded_files_empty_output():
    # Act / Assert
    assert wait_for_tests.parse_uploaded_files("") == set()


def test_prune_uploaded_files_removes_only_uploaded(cdash_tree):
    # Context
    _, testtime_dir = cdash_tree
    uploaded = {"Configure.xml", "Test.xml", "Notes.xml"}

    # Act
    removed = wait_for_tests.prune_uploaded_files(testtime_dir, uploaded)

    # Assert
    assert removed == ["Configure.xml", "Test.xml"]
    assert sorted(p.name for p in testtime_dir.iterdir()) == ["Build.xml", "Upload.xml"]


def test_prune_uploaded_files_nothing_uploaded(cdash_tree):
    # Context
    _, testtime_dir = cdash_tree

    # Act
    removed = wait_for_tests.prune_uploaded_files(testtime_dir, set())

    # Assert
    assert removed == []
    assert sorted(p.name for p in testtime_dir.iterdir()) == sorted(XML_FILES)


def test_submit_cdash_files_success_first_try(cdash_tree):
    # Context
    tmp_path, testtime_dir = cdash_tree
    runner = FakeRunner([(0, CTEST_SUCCESS)], testtime_dir)
    uploaded = set()

    # Act
    result = _submit(tmp_path, testtime_dir, runner, uploaded)

    # Assert
    assert result is True
    assert len(runner.commands) == 1
    assert runner.drop_methods == ["https"]
    assert runner.from_dirs == [str(tmp_path)]
    assert "-A notes.txt" in runner.commands[0]
    assert runner.files_seen[0] == sorted(XML_FILES)
    assert uploaded == {"Upload.xml", "Done.xml"}


def test_submit_cdash_files_retry_does_not_resend_uploaded_files(cdash_tree):
    # Context
    tmp_path, testtime_dir = cdash_tree
    runner = FakeRunner([(1, CTEST_PARTIAL_FAILURE), (0, CTEST_SUCCESS)], testtime_dir)
    uploaded = set()

    # Act
    result = _submit(tmp_path, testtime_dir, runner, uploaded)

    # Assert
    assert result is True
    assert runner.drop_methods == ["https", "http"]
    assert runner.files_seen[0] == sorted(XML_FILES)
    # Test.xml (and friends) were accepted over https; the http retry must not see them.
    assert runner.files_seen[1] == ["Upload.xml"]
    # Notes.xml was never accepted so ctest must regenerate it.
    assert all("-A notes.txt" in cmd for cmd in runner.commands)
    assert uploaded == {
        "Configure.xml",
        "Build.xml",
        "Test.xml",
        "Upload.xml",
        "Done.xml",
    }


def test_submit_cdash_files_retry_skips_notes_when_already_uploaded(cdash_tree):
    # Context
    tmp_path, testtime_dir = cdash_tree
    runner = FakeRunner(
        [(1, CTEST_NOTES_UPLOADED_FAILURE), (0, CTEST_SUCCESS)], testtime_dir
    )
    uploaded = set()

    # Act
    result = _submit(tmp_path, testtime_dir, runner, uploaded)

    # Assert
    assert result is True
    assert "-A notes.txt" in runner.commands[0]
    assert "-A notes.txt" not in runner.commands[1]
    assert runner.files_seen[1] == ["Upload.xml"]


def test_submit_cdash_files_honors_previously_uploaded_set(cdash_tree):
    # Context: a prior attempt (e.g. from another tmproot) already delivered Test.xml.
    tmp_path, testtime_dir = cdash_tree
    runner = FakeRunner([(0, CTEST_SUCCESS)], testtime_dir)
    uploaded = {"Configure.xml", "Build.xml", "Test.xml"}

    # Act
    result = _submit(tmp_path, testtime_dir, runner, uploaded)

    # Assert
    assert result is True
    assert runner.files_seen[0] == ["Upload.xml"]


def test_submit_cdash_files_all_attempts_fail(cdash_tree):
    # Context
    tmp_path, testtime_dir = cdash_tree
    runner = FakeRunner(
        [(1, CTEST_PARTIAL_FAILURE), (1, "Problems when submitting via HTTP")],
        testtime_dir,
    )
    uploaded = set()

    # Act
    result = _submit(tmp_path, testtime_dir, runner, uploaded)

    # Assert
    assert result is False
    assert runner.drop_methods == ["https", "http"]
    assert runner.files_seen[1] == ["Upload.xml"]
    # Progress is retained so a later attempt from another tmproot will not resend these.
    assert uploaded == {"Configure.xml", "Build.xml", "Test.xml"}


def test_submit_cdash_files_writes_dart_config(cdash_tree):
    # Context
    tmp_path, testtime_dir = cdash_tree
    runner = FakeRunner([(0, CTEST_SUCCESS)], testtime_dir)

    # Act
    _submit(tmp_path, testtime_dir, runner, set())

    # Assert
    dart = (tmp_path / "DartConfiguration.tcl").read_text()
    assert "BuildName: build" in dart
    assert "Site: chrysalis" in dart
    assert "DropLocation: /submit.php?project=E3SM" in dart
    assert "NightlyStartTime: 13:52:00 UTC" in dart
