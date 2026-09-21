#!/usr/bin/env python3

"""Unit tests for ``check_input_data._download_if_in_repo``.

These tests cover the file and directory download paths, which download
to a temporary path and atomically rename it into place, so a
destination already present (from a prior download, or a concurrent
test case sharing the same DIN_LOC_ROOT racing to fetch the same path)
is treated as success instead of failing the underlying server export.
"""

from unittest import mock
import os

from CIME.case.check_input_data import _download_if_in_repo


def _make_server(getfile_side_effect):
    server = mock.MagicMock()
    server.fileexists.return_value = True
    server.getfile.side_effect = getfile_side_effect
    return server


def test_download_if_in_repo_file_missing_download_succeeds(tmp_path):
    """Happy path: destination absent, download succeeds, file renamed into place."""

    def getfile(rel_path, tmp_path_arg):
        with open(tmp_path_arg, "w") as fd:
            fd.write("data")
        return True

    server = _make_server(getfile)

    success = _download_if_in_repo(server, str(tmp_path), "foo.nc")

    assert success is True
    dest = tmp_path / "foo.nc"
    assert dest.is_file()
    assert dest.read_text() == "data"
    assert not (tmp_path / "foo.nc.tmp").exists()


def test_download_if_in_repo_file_already_present_skips_download(tmp_path):
    """If the destination already exists, treat as success without downloading."""
    dest = tmp_path / "foo.nc"
    dest.write_text("already here")

    server = _make_server(getfile_side_effect=AssertionError("should not be called"))

    success = _download_if_in_repo(server, str(tmp_path), "foo.nc")

    assert success is True
    server.getfile.assert_not_called()
    assert dest.read_text() == "already here"


def test_download_if_in_repo_concurrent_download_wins_race(tmp_path):
    """
    A concurrent download (e.g. another test case sharing DIN_LOC_ROOT) can
    create the destination file while our own download is in flight. Our
    temp copy must be discarded rather than overwriting the winner's file,
    and the call must still report success.
    """
    dest = tmp_path / "foo.nc"

    def getfile(rel_path, tmp_path_arg):
        # Simulate a concurrent downloader finishing first.
        dest.write_text("winner")
        with open(tmp_path_arg, "w") as fd:
            fd.write("loser")
        return True

    server = _make_server(getfile)

    success = _download_if_in_repo(server, str(tmp_path), "foo.nc")

    assert success is True
    assert dest.read_text() == "winner"
    assert not (tmp_path / "foo.nc.tmp").exists()


def test_download_if_in_repo_download_fails_cleans_up_temp(tmp_path):
    """A failed download must not leave a stray .tmp file or a destination file."""

    def getfile(rel_path, tmp_path_arg):
        with open(tmp_path_arg, "w") as fd:
            fd.write("partial")
        return False

    server = _make_server(getfile)

    success = _download_if_in_repo(server, str(tmp_path), "foo.nc")

    assert success is False
    assert not (tmp_path / "foo.nc").exists()
    assert not (tmp_path / "foo.nc.tmp").exists()


def test_download_if_in_repo_download_fails_without_temp_file(tmp_path):
    """A failed download that never wrote a temp file must not raise."""
    server = _make_server(getfile_side_effect=lambda rel_path, tmp_path_arg: False)

    success = _download_if_in_repo(server, str(tmp_path), "foo.nc")

    assert success is False
    assert not (tmp_path / "foo.nc").exists()
    assert not (tmp_path / "foo.nc.tmp").exists()


def test_download_if_in_repo_file_creates_missing_parent_dir(tmp_path):
    """The destination's parent directory is created if it does not exist."""

    def getfile(rel_path, tmp_path_arg):
        with open(tmp_path_arg, "w") as fd:
            fd.write("data")
        return True

    server = _make_server(getfile)

    success = _download_if_in_repo(server, str(tmp_path), "nested/dir/foo.nc")

    assert success is True
    dest = tmp_path / "nested" / "dir" / "foo.nc"
    assert dest.read_text() == "data"


def test_download_if_in_repo_empty_rel_path_and_not_on_server_returns_false(tmp_path):
    """No rel_path and the server does not report the file present -> False."""
    server = mock.MagicMock()
    server.fileexists.return_value = False

    success = _download_if_in_repo(server, str(tmp_path), "")

    assert success is False
    server.getfile.assert_not_called()


def test_download_if_in_repo_directory_missing_download_succeeds(tmp_path):
    """Happy path: directory absent, download succeeds, renamed into place."""

    def getdirectory(rel_path, tmp_dest):
        with open(os.path.join(tmp_dest, "inner.txt"), "w") as fd:
            fd.write("data")
        return True

    server = mock.MagicMock()
    server.fileexists.return_value = True
    server.getdirectory.side_effect = getdirectory

    success = _download_if_in_repo(server, str(tmp_path), "somedir/", isdirectory=True)

    assert success is True
    dest = tmp_path / "somedir"
    assert dest.is_dir()
    assert (dest / "inner.txt").read_text() == "data"
    assert not (tmp_path / "somedir.tmp").exists()


def test_download_if_in_repo_directory_already_present_skips_download(tmp_path):
    """If the destination directory already exists, skip the download entirely."""
    dest = tmp_path / "somedir"
    dest.mkdir()
    (dest / "existing.txt").write_text("already here")

    server = mock.MagicMock()
    server.fileexists.return_value = True

    success = _download_if_in_repo(server, str(tmp_path), "somedir/", isdirectory=True)

    assert success is True
    server.getdirectory.assert_not_called()
    assert (dest / "existing.txt").read_text() == "already here"


def test_download_if_in_repo_directory_concurrent_download_wins_race(tmp_path):
    """A concurrent directory download finishing first must win the race."""
    dest = tmp_path / "somedir"

    def getdirectory(rel_path, tmp_dest):
        dest.mkdir()
        (dest / "winner.txt").write_text("winner")
        with open(os.path.join(tmp_dest, "loser.txt"), "w") as fd:
            fd.write("loser")
        return True

    server = mock.MagicMock()
    server.fileexists.return_value = True
    server.getdirectory.side_effect = getdirectory

    success = _download_if_in_repo(server, str(tmp_path), "somedir/", isdirectory=True)

    assert success is True
    assert (dest / "winner.txt").exists()
    assert not (dest / "loser.txt").exists()
    assert not (tmp_path / "somedir.tmp").exists()


def test_download_if_in_repo_directory_download_fails_cleans_up_temp(tmp_path):
    """A failed directory download must not leave a stray .tmp dir or destination."""

    def getdirectory(rel_path, tmp_dest):
        with open(os.path.join(tmp_dest, "partial.txt"), "w") as fd:
            fd.write("partial")
        return False

    server = mock.MagicMock()
    server.fileexists.return_value = True
    server.getdirectory.side_effect = getdirectory

    success = _download_if_in_repo(server, str(tmp_path), "somedir/", isdirectory=True)

    assert success is False
    assert not (tmp_path / "somedir").exists()
    assert not (tmp_path / "somedir.tmp").exists()
