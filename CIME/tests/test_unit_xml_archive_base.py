#!/usr/bin/env python3

import os
import io
import unittest
import tempfile
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

from CIME.XML.archive_base import ArchiveBase

TEST_CONFIG_ARCHIVE_XML = """<components version="2.0">
  <comp_archive_spec compname="eam" compclass="atm">
    <hist_file_extension>unique\.name\.unique</hist_file_extension>
  </comp_archive_spec>
</components>"""


class TestXMLArchiveBase(unittest.TestCase):
    @contextmanager
    def _setup_environment(self, test_files):
        with tempfile.TemporaryDirectory() as temp_dir:
            for x in test_files:
                Path(temp_dir, x).touch()

            yield temp_dir

    def test_get_all_hist_files(self):
        archiver = ArchiveBase()

        archiver.read_fd(io.StringIO(TEST_CONFIG_ARCHIVE_XML))

        test_files = [
            "casename.eam.0001-01-01-0000.nc",
            "casename.eam.unique.name.unique.0001-01-01-0000.nc",
            "casename.eam.unique.name.unique.some.extra.0001-01-01-0000.nc",
            "casename.eam.unique.name.unique.0001-01-01-0000.nc.base",
            "casename.eam.unique.name.unique.some.extra.0001-01-01-0000.nc.base",
        ]

        with self._setup_environment(test_files) as temp_dir:
            hist_files = archiver.get_all_hist_files(
                "casename", "eam", from_dir=temp_dir
            )

        test_files.sort()
        hist_files.sort()

        assert len(hist_files) == 4

        # assert all match except first
        for x, y in zip(test_files[1:], hist_files):
            assert x == y, f"{x} != {y}"

    def test_get_all_hist_files_with_suffix(self):
        archiver = ArchiveBase()

        archiver.read_fd(io.StringIO(TEST_CONFIG_ARCHIVE_XML))

        test_files = [
            "casename.eam.0001-01-01-0000.nc",
            "casename.eam.unique.name.unique.0001-01-01-0000.nc",
            "casename.eam.unique.name.unique.some.extra.0001-01-01-0000.nc",
            "casename.eam.unique.name.unique.0001-01-01-0000.nc.base",
            "casename.eam.unique.name.unique.some.extra.0001-01-01-0000.nc.base",
        ]

        with self._setup_environment(test_files) as temp_dir:
            hist_files = archiver.get_all_hist_files(
                "casename", "eam", suffix="base", from_dir=temp_dir
            )

        assert len(hist_files) == 2

        assert test_files[3] in hist_files
        assert test_files[4] in hist_files
