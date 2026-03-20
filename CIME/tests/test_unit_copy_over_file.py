import os
import stat
import shutil
import tempfile
import unittest
from unittest.mock import patch

from CIME.utils import copy_over_file


class TestCopyOverFile(unittest.TestCase):
    """Unit tests for copy_over_file."""

    SRC_CONTENT = "source content"
    OLD_CONTENT = "old content"

    def setUp(self):
        self._workdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._workdir, ignore_errors=True)

    def _make_file(self, name, content, mode=None):
        path = os.path.join(self._workdir, name)
        with open(path, "w", encoding="utf8") as f:
            f.write(content)
        if mode is not None:
            os.chmod(path, mode)
        return path

    def _read(self, path):
        with open(path, "r", encoding="utf8") as f:
            return f.read()

    def test_copies_content(self):
        """Content is copied correctly (default preserve_meta)."""
        src = self._make_file("src.txt", self.SRC_CONTENT)
        tgt = self._make_file("tgt.txt", self.OLD_CONTENT)

        copy_over_file(src, tgt)

        self.assertEqual(self._read(tgt), self.SRC_CONTENT)

    def test_owned_target_preserve_meta_true_copies_permissions(self):
        """With preserve_meta=True and owned target, permissions are copied from src."""
        src = self._make_file("src.txt", self.SRC_CONTENT, mode=0o644)
        tgt = self._make_file("tgt.txt", self.OLD_CONTENT, mode=0o600)

        copy_over_file(src, tgt, preserve_meta=True)

        self.assertEqual(self._read(tgt), self.SRC_CONTENT)
        tgt_mode = stat.S_IMODE(os.stat(tgt).st_mode)
        src_mode = stat.S_IMODE(os.stat(src).st_mode)
        self.assertEqual(tgt_mode, src_mode)

    def test_readonly_target_owned_overwritten(self):
        """A read-only owned target is made writable and then overwritten."""
        src = self._make_file("src.txt", self.SRC_CONTENT)
        tgt = self._make_file("tgt.txt", self.OLD_CONTENT, mode=0o444)

        copy_over_file(src, tgt, preserve_meta=True)

        self.assertEqual(self._read(tgt), self.SRC_CONTENT)

    def test_readonly_target_not_owned_raises(self):
        """A read-only target that we don't own raises OSError."""
        src = self._make_file("src.txt", self.SRC_CONTENT)
        tgt = self._make_file("tgt.txt", self.OLD_CONTENT, mode=0o444)

        # Simulate being a different user (not the file owner) who cannot write to
        # the read-only target.  We patch both os.getuid (so owner_uid != getuid())
        # and os.access (so the file appears non-writable regardless of whether the
        # test runner is root, which would otherwise make os.access return True for
        # any file and prevent the OSError path from being reached).
        real_uid = os.getuid()
        with patch("CIME.utils.os.getuid", return_value=real_uid + 1):
            with patch("CIME.utils.os.access", return_value=False):
                with self.assertRaises(OSError):
                    copy_over_file(src, tgt, preserve_meta=True)

    def test_not_owner_content_only(self):
        """A non-owned writable target gets content-only copy (no metadata transfer)."""
        src = self._make_file("src.txt", self.SRC_CONTENT, mode=0o644)
        tgt = self._make_file("tgt.txt", self.OLD_CONTENT, mode=0o666)

        real_stat = os.stat(tgt)
        # Build a real os.stat_result with a different uid so copy_over_file thinks
        # we are not the owner.  Using os.stat_result preserves st_ino/st_dev so that
        # shutil.copyfile's internal _samefile check keeps working.
        fake_uid = os.getuid() + 1
        fake_stat_result = os.stat_result(
            (
                real_stat.st_mode,
                real_stat.st_ino,
                real_stat.st_dev,
                real_stat.st_nlink,
                fake_uid,
                real_stat.st_gid,
                real_stat.st_size,
                real_stat.st_atime,
                real_stat.st_mtime,
                real_stat.st_ctime,
            )
        )

        real_os_stat = os.stat

        def fake_stat_fn(path, *args, **kwargs):
            if path == tgt:
                return fake_stat_result
            return real_os_stat(path, *args, **kwargs)

        with patch("CIME.utils.os.stat", side_effect=fake_stat_fn):
            # make target appear writable so we don't hit the read-only branch
            with patch("CIME.utils.os.access", return_value=True):
                copy_over_file(src, tgt, preserve_meta=True)

        self.assertEqual(self._read(tgt), self.SRC_CONTENT)
        # Permissions should NOT have been copied from src (0o644) to tgt (0o666)
        tgt_mode = stat.S_IMODE(os.stat(tgt).st_mode)
        src_mode = stat.S_IMODE(os.stat(src).st_mode)
        self.assertNotEqual(tgt_mode, src_mode)
        self.assertEqual(tgt_mode, stat.S_IMODE(real_stat.st_mode))

    def test_owned_target_preserve_meta_false_does_not_copy_permissions(self):
        """With preserve_meta=False and owned target, permissions are NOT copied from src."""
        # src has restrictive 0o600 permissions; tgt has broader 0o644
        src = self._make_file("src.txt", self.SRC_CONTENT, mode=0o600)
        tgt = self._make_file("tgt.txt", self.OLD_CONTENT, mode=0o644)
        tgt_mode_orig = stat.S_IMODE(os.stat(tgt).st_mode)

        copy_over_file(src, tgt, preserve_meta=False)

        # Content must be copied
        self.assertEqual(self._read(tgt), self.SRC_CONTENT)

        # Permissions must NOT have been taken from src (0o600)
        tgt_mode = stat.S_IMODE(os.stat(tgt).st_mode)
        src_mode = stat.S_IMODE(os.stat(src).st_mode)
        self.assertNotEqual(
            tgt_mode,
            src_mode,
            f"preserve_meta=False should not copy permissions; "
            f"src={oct(src_mode)}, tgt={oct(tgt_mode)}",
        )
        self.assertEqual(
            tgt_mode,
            tgt_mode_orig,
        )

    def test_readonly_owned_target_preserve_meta_false_does_not_copy_permissions(self):
        """Read-only owned target with preserve_meta=False: made writable, content copied,
        permissions NOT transferred from src.
        """
        src = self._make_file("src.txt", self.SRC_CONTENT, mode=0o600)
        tgt = self._make_file("tgt.txt", self.OLD_CONTENT, mode=0o444)

        copy_over_file(src, tgt, preserve_meta=False)

        self.assertEqual(self._read(tgt), self.SRC_CONTENT)

        tgt_mode = stat.S_IMODE(os.stat(tgt).st_mode)
        src_mode = stat.S_IMODE(os.stat(src).st_mode)
        self.assertNotEqual(
            tgt_mode,
            src_mode,
            f"preserve_meta=False should not copy permissions; "
            f"src={oct(src_mode)}, tgt={oct(tgt_mode)}",
        )
