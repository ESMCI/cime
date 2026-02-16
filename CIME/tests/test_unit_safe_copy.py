import os
import stat
import shutil
import tempfile

import unittest
from CIME.utils import safe_copy


class TestSafeCopy(unittest.TestCase):
    # Test content constants
    TEST_CONTENT = "test content"
    NEW_CONTENT = "new content"
    OLD_CONTENT = "old content"
    CONTENT_1 = "content1"
    CONTENT_2 = "content2"
    ROOT_CONTENT = "root content"
    NESTED_CONTENT = "nested content"
    SCRIPT_CONTENT = "#!/bin/bash\necho test"

    # Permission constants
    PERM_RW_R_R = 0o644  # rw-r--r-- (owner: read/write, group/others: read)
    PERM_RW_ONLY = 0o600  # rw------- (owner: read/write only)
    PERM_EXECUTABLE = 0o755  # rwxr-xr-x (owner: rwx, group/others: rx)
    PERM_READONLY = 0o444  # r--r--r-- (all: read only)

    # Filename constants
    SRC_FILE = "source.txt"
    TGT_FILE = "target.txt"
    SRC_DIR = "source_dir"
    TGT_DIR = "target_dir"
    SCRIPT_FILE = "script.sh"
    SCRIPT_COPY = "script_copy.sh"
    FILE_1 = "file1.txt"
    FILE_2 = "file2.txt"
    SINGLE_FILE = "file.txt"
    SUBDIR = "subdir"
    NESTED_FILE = "nested.txt"

    def setUp(self):
        self._workdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._workdir, ignore_errors=True)

    def _create_file(self, path, content):
        """Helper method to create a file with given content"""
        with open(path, "w", encoding="utf8") as f:
            f.write(content)

    def _read_file(self, path):
        """Helper method to read file content"""
        with open(path, "r", encoding="utf8") as f:
            return f.read()

    def test_safe_copy_basic_file(self):
        """Test basic file copy to a new location"""
        src_file = os.path.join(self._workdir, self.SRC_FILE)
        tgt_file = os.path.join(self._workdir, self.TGT_FILE)

        self._create_file(src_file, self.TEST_CONTENT)

        safe_copy(src_file, tgt_file)

        self.assertTrue(os.path.isfile(tgt_file))
        self.assertEqual(self._read_file(tgt_file), self.TEST_CONTENT)

    def test_safe_copy_to_directory(self):
        """Test copying a file to a directory (should use basename)"""
        src_file = os.path.join(self._workdir, self.SRC_FILE)
        tgt_dir = os.path.join(self._workdir, self.TGT_DIR)
        os.makedirs(tgt_dir)

        self._create_file(src_file, self.TEST_CONTENT)

        safe_copy(src_file, tgt_dir)

        expected_file = os.path.join(tgt_dir, self.SRC_FILE)
        self.assertTrue(os.path.isfile(expected_file))
        self.assertEqual(self._read_file(expected_file), self.TEST_CONTENT)

    def test_safe_copy_overwrite_existing(self):
        """Test overwriting an existing file"""
        src_file = os.path.join(self._workdir, self.SRC_FILE)
        tgt_file = os.path.join(self._workdir, self.TGT_FILE)

        self._create_file(src_file, self.NEW_CONTENT)
        self._create_file(tgt_file, self.OLD_CONTENT)

        safe_copy(src_file, tgt_file)

        self.assertEqual(self._read_file(tgt_file), self.NEW_CONTENT)

    def test_safe_copy_readonly_file(self):
        """Test overwriting a read-only file (when we own it)"""
        src_file = os.path.join(self._workdir, self.SRC_FILE)
        tgt_file = os.path.join(self._workdir, self.TGT_FILE)

        self._create_file(src_file, self.NEW_CONTENT)
        self._create_file(tgt_file, self.OLD_CONTENT)

        # Make target read-only
        os.chmod(tgt_file, self.PERM_READONLY)

        safe_copy(src_file, tgt_file)

        self.assertEqual(self._read_file(tgt_file), self.NEW_CONTENT)

    def test_safe_copy_preserve_meta_true(self):
        """Test that metadata is preserved when preserve_meta=True"""
        src_file = os.path.join(self._workdir, self.SRC_FILE)
        tgt_file = os.path.join(self._workdir, self.TGT_FILE)

        self._create_file(src_file, self.TEST_CONTENT)

        # Set specific permissions on source
        os.chmod(src_file, self.PERM_RW_R_R)
        src_stat = os.stat(src_file)

        safe_copy(src_file, tgt_file, preserve_meta=True)

        tgt_stat = os.stat(tgt_file)
        # Check that permissions are preserved (masking out file type bits)
        self.assertEqual(stat.S_IMODE(src_stat.st_mode), stat.S_IMODE(tgt_stat.st_mode))

    def test_safe_copy_preserve_meta_false(self):
        """
        Test that metadata is not preserved when preserve_meta=False.

        This test is currently failing: The safe_copy docstring indicates that we do NOT want
        permissions preserved when preserve_meta is False, but it looks like they *are* preserved
        due to the use of copy(), which according to the Python docs (and this test) *does* preserve
        permissions.
        """
        src_file = os.path.join(self._workdir, self.SRC_FILE)
        tgt_file = os.path.join(self._workdir, self.TGT_FILE)

        self._create_file(src_file, self.TEST_CONTENT)

        # Set specific permissions on source
        os.chmod(src_file, self.PERM_RW_ONLY)
        src_stat = os.stat(src_file)

        safe_copy(src_file, tgt_file, preserve_meta=False)

        # File should exist with content copied correctly
        self.assertTrue(os.path.isfile(tgt_file))
        self.assertEqual(self._read_file(tgt_file), self.TEST_CONTENT)

        # Verify that permissions are NOT preserved (should be different from source): This is the
        # intended behavior with preserve_meta=False according to the safe_copy docstring.
        tgt_stat = os.stat(tgt_file)
        self.assertNotEqual(
            stat.S_IMODE(src_stat.st_mode), stat.S_IMODE(tgt_stat.st_mode)
        )

    def test_safe_copy_executable_file(self):
        """Test that executable bit is preserved for executable files"""
        src_file = os.path.join(self._workdir, self.SCRIPT_FILE)
        tgt_file = os.path.join(self._workdir, self.SCRIPT_COPY)

        self._create_file(src_file, self.SCRIPT_CONTENT)

        # Make source executable
        os.chmod(src_file, self.PERM_EXECUTABLE)

        safe_copy(src_file, tgt_file)

        # Check that target is also executable
        self.assertTrue(os.access(tgt_file, os.X_OK))

    def test_safe_copy_directory(self):
        """Test copying a directory"""
        src_dir = os.path.join(self._workdir, self.SRC_DIR)
        tgt_dir = os.path.join(self._workdir, self.TGT_DIR)
        os.makedirs(src_dir)

        # Create some files in source directory
        self._create_file(os.path.join(src_dir, self.FILE_1), self.CONTENT_1)
        self._create_file(os.path.join(src_dir, self.FILE_2), self.CONTENT_2)

        safe_copy(src_dir, tgt_dir)

        # Check that directory and files were copied
        self.assertTrue(os.path.isdir(tgt_dir))
        self.assertTrue(os.path.isfile(os.path.join(tgt_dir, self.FILE_1)))
        self.assertTrue(os.path.isfile(os.path.join(tgt_dir, self.FILE_2)))

        self.assertEqual(
            self._read_file(os.path.join(tgt_dir, self.FILE_1)), self.CONTENT_1
        )

    def test_safe_copy_directory_preserve_meta_false(self):
        """
        Test copying a directory with preserve_meta=False.

        This test is currently passing, unlike test_safe_copy_preserve_meta_false, which is the
        equivalent test for files. This is because when copying a DIRECTORY with
        preserve_meta=False, it uses shutil.copytree with copy_function=shutil.copyfile, which does
        *not* preserve permissions.

        This suggests that using shutil.copyfile instead of shutil.copy when calling safe_copy() on
        a file would fix test_safe_copy_preserve_meta_false.
        """
        src_dir = os.path.join(self._workdir, self.SRC_DIR)
        tgt_dir = os.path.join(self._workdir, self.TGT_DIR)
        os.makedirs(os.path.join(src_dir, self.SUBDIR))

        test_file = os.path.join(src_dir, self.SUBDIR, self.SINGLE_FILE)
        self._create_file(test_file, self.TEST_CONTENT)

        # Set specific permissions on the file
        os.chmod(test_file, self.PERM_RW_ONLY)
        src_stat = os.stat(test_file)

        safe_copy(src_dir, tgt_dir, preserve_meta=False)

        self.assertTrue(os.path.isdir(tgt_dir))
        tgt_file = os.path.join(tgt_dir, self.SUBDIR, self.SINGLE_FILE)
        self.assertTrue(os.path.isfile(tgt_file))

        # Verify that permissions are NOT preserved (should be different from source)
        tgt_stat = os.stat(tgt_file)
        self.assertNotEqual(
            stat.S_IMODE(src_stat.st_mode), stat.S_IMODE(tgt_stat.st_mode)
        )

    def test_safe_copy_nested_directory(self):
        """Test copying a directory with nested subdirectories"""
        src_dir = os.path.join(self._workdir, self.SRC_DIR)
        tgt_dir = os.path.join(self._workdir, self.TGT_DIR)
        os.makedirs(os.path.join(src_dir, self.SUBDIR))

        self._create_file(
            os.path.join(src_dir, self.SUBDIR, self.SINGLE_FILE), self.ROOT_CONTENT
        )
        self._create_file(
            os.path.join(src_dir, self.SUBDIR, self.NESTED_FILE), self.NESTED_CONTENT
        )

        safe_copy(src_dir, tgt_dir)

        self.assertTrue(os.path.isdir(tgt_dir))
        self.assertTrue(
            os.path.isfile(os.path.join(tgt_dir, self.SUBDIR, self.SINGLE_FILE))
        )
        self.assertTrue(os.path.isdir(os.path.join(tgt_dir, self.SUBDIR)))
        self.assertTrue(
            os.path.isfile(os.path.join(tgt_dir, self.SUBDIR, self.NESTED_FILE))
        )

        self.assertEqual(
            self._read_file(os.path.join(tgt_dir, self.SUBDIR, self.NESTED_FILE)),
            self.NESTED_CONTENT,
        )
