import tempfile
import unittest
from unittest import mock
from pathlib import Path

from CIME import locked_files
from CIME.utils import CIMEError
from CIME.XML.env_case import EnvCase


class TestLockedFiles(unittest.TestCase):
    def test_check_lockedfile(self):
        with tempfile.TemporaryDirectory() as tempdir:
            src_case = EnvCase(tempdir)

            src_case.set_value("USER", "root")

            src_case.write(force_write=True)

    def test_is_locked(self):
        with tempfile.TemporaryDirectory() as tempdir:
            src_path = Path(tempdir, locked_files.LOCKED_DIR, "env_case.xml")

            src_path.parent.mkdir(parents=True)

            src_path.touch()

            assert locked_files.is_locked("env_case.xml", tempdir)

            src_path.unlink()

            assert not locked_files.is_locked("env_case.xml", tempdir)

    def test_unlock_file_error_path(self):
        with tempfile.TemporaryDirectory() as tempdir:
            src_path = Path(tempdir, locked_files.LOCKED_DIR, "env_case.xml")

            src_path.parent.mkdir(parents=True)

            src_path.touch()

            with self.assertRaises(CIMEError):
                locked_files.unlock_file("/env_case.xml", tempdir)

    def test_unlock_file(self):
        with tempfile.TemporaryDirectory() as tempdir:
            src_path = Path(tempdir, locked_files.LOCKED_DIR, "env_case.xml")

            src_path.parent.mkdir(parents=True)

            src_path.touch()

            locked_files.unlock_file("env_case.xml", tempdir)

            assert not src_path.exists()

    def test_lock_file_newname(self):
        with tempfile.TemporaryDirectory() as tempdir:
            src_path = Path(tempdir, "env_case.xml")

            src_path.touch()

            locked_files.lock_file("env_case.xml", tempdir, newname="env_case-old.xml")

            dst_path = Path(tempdir, locked_files.LOCKED_DIR, "env_case-old.xml")

            assert dst_path.exists()

    def test_lock_file_error_path(self):
        with tempfile.TemporaryDirectory() as tempdir:
            src_path = Path(tempdir, "env_case.xml")

            src_path.touch()

            with self.assertRaises(CIMEError):
                locked_files.lock_file("/env_case.xml", tempdir)

    def test_lock_file(self):
        with tempfile.TemporaryDirectory() as tempdir:
            src_path = Path(tempdir, "env_case.xml")

            src_path.touch()

            locked_files.lock_file("env_case.xml", tempdir)

            dst_path = Path(tempdir, locked_files.LOCKED_DIR, "env_case.xml")

            assert dst_path.exists()
