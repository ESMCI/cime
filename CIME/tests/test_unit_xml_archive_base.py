#!/usr/bin/env python3

import os
import io
import unittest
import tempfile
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

from CIME.XML.archive_base import ArchiveBase

TEST_CONFIG = """<components version="2.0">
  <comp_archive_spec compname="eam" compclass="atm">
    <hist_file_extension>unique\.name\.unique.*</hist_file_extension>
  </comp_archive_spec>
</components>"""

EXACT_TEST_CONFIG = """<components version="2.0">
  <comp_archive_spec compname="eam" compclass="atm">
    <hist_file_extension>unique\.name\.unique.nc</hist_file_extension>
  </comp_archive_spec>
</components>"""

EXCLUDE_TEST_CONFIG = """<components version="2.0">
  <comp_archive_spec compname="eam" compclass="atm">
    <hist_file_extension>unique\.name\.unique.nc</hist_file_extension>
  </comp_archive_spec>
  <comp_archive_spec compname="cpl" compclass="drv" exclude_testing="True">
    <hist_file_extension>unique\.name\.unique.nc</hist_file_extension>
  </comp_archive_spec>
  <comp_archive_spec compname="mpasso" compclass="drv" exclude_testing="False">
    <hist_file_extension>unique\.name\.unique.nc</hist_file_extension>
  </comp_archive_spec>
</components>"""


class TestXMLArchiveBase(unittest.TestCase):
    @contextmanager
    def _setup_environment(self, test_files):
        with tempfile.TemporaryDirectory() as temp_dir:
            for x in test_files:
                Path(temp_dir, x).touch()

            yield temp_dir

    def test_exclude_testing(self):
        archiver = ArchiveBase()

        archiver.read_fd(io.StringIO(EXCLUDE_TEST_CONFIG))

        # no attribute
        assert not archiver.exclude_testing("eam")

        # not in config
        assert not archiver.exclude_testing("mpassi")

        # set false
        assert not archiver.exclude_testing("mpasso")

        # set true
        assert archiver.exclude_testing("cpl")

    def test_match_files(self):
        archiver = ArchiveBase()

        archiver.read_fd(io.StringIO(TEST_CONFIG))

        fail_files = [
            "othername.eam.unique.name.unique.0001-01-01-0000.nc",  # casename mismatch
            "casename.satm.unique.name.unique.0001-01-01-0000.nc",  # model (component?) mismatch
            "casename.eam.0001-01-01-0000.nc",  # missing hist_file_extension
            "casename.eam.unique.name.unique.0001-01-01-0000.nc",
            "casename.eam.unique.name.unique.some.extra.0001-01-01-0000.nc",
        ]

        test_files = [
            "casename.eam1.unique.name.unique.0001-01-01-0000.nc",
            "casename.eam1_.unique.name.unique.0001-01-01-0000.nc",
            "casename.eam_.unique.name.unique.0001-01-01-0000.nc",
            "casename.eam1990.unique.name.unique.0001-01-01-0000.nc",
            "casename.eam_1990.unique.name.unique.0001-01-01-0000.nc",
            "casename.eam1_1990.unique.name.unique.0001-01-01-0000.nc",
            "casename.eam11990.unique.name.unique.0001-01-01-0000.nc",
            "casename.eam.unique.name.unique.0001-01-01-0000.nc",
            "casename.eam.unique.name.unique.some.extra.0001-01-01-0000.nc",
            "casename.eam.unique.name.unique.0001-01-01-0000.nc.base",
            "casename.eam.unique.name.unique.some.extra.0001-01-01-0000.nc.base",
        ]

        with self._setup_environment(fail_files + test_files) as temp_dir:
            hist_files = archiver.get_all_hist_files(
                "casename", "eam", from_dir=temp_dir
            )

        test_files.sort()
        hist_files.sort()

        assert len(hist_files) == len(test_files)

        # assert all match except first
        for x, y in zip(test_files, hist_files):
            assert x == y, f"{x} != {y}"

    def test_extension_included(self):
        archiver = ArchiveBase()

        archiver.read_fd(io.StringIO(EXACT_TEST_CONFIG))

        fail_files = [
            "othername.eam.unique.name.unique.0001-01-01-0000.nc",  # casename mismatch
            "casename.satm.unique.name.unique.0001-01-01-0000.nc",  # model (component?) mismatch
            "casename.eam.0001-01-01-0000.nc",  # missing hist_file_extension
            "casename.eam.unique.name.unique.0001-01-01-0000.nc",
            "casename.eam.unique.name.unique.some.extra.0001-01-01-0000.nc",
            "casename.eam.unique.name.unique.0001-01-01-0000.nc.base",
            "casename.eam.unique.name.unique.some.extra.0001-01-01-0000.nc.base",
        ]

        test_files = [
            "casename.eam1.unique.name.unique.nc",
            "casename.eam1_.unique.name.unique.nc",
            "casename.eam_.unique.name.unique.nc",
            "casename.eam1990.unique.name.unique.nc",
            "casename.eam_1990.unique.name.unique.nc",
            "casename.eam1_1990.unique.name.unique.nc",
            "casename.eam11990.unique.name.unique.nc",
            "casename.eam.unique.name.unique.nc",
        ]

        with self._setup_environment(fail_files + test_files) as temp_dir:
            hist_files = archiver.get_all_hist_files(
                "casename", "eam", suffix="nc", from_dir=temp_dir
            )

        test_files.sort()
        hist_files.sort()

        assert len(hist_files) == len(test_files)

        # assert all match except first
        for x, y in zip(test_files, hist_files):
            assert x == y, f"{x} != {y}"

    def test_suffix(self):
        archiver = ArchiveBase()

        archiver.read_fd(io.StringIO(TEST_CONFIG))

        fail_files = [
            "othername.eam.unique.name.unique.0001-01-01-0000.nc",  # casename mismatch
            "casename.satm.unique.name.unique.0001-01-01-0000.nc",  # model (component?) mismatch
            "casename.eam.0001-01-01-0000.nc",  # missing hist_file_extension
            "casename.eam.unique.name.unique.0001-01-01-0000.nc",
            "casename.eam.unique.name.unique.some.extra.0001-01-01-0000.nc",
            # ensure these do not match when suffix is provided
            "casename.eam1.unique.name.unique.0001-01-01-0000.nc",
            "casename.eam1_.unique.name.unique.0001-01-01-0000.nc",
            "casename.eam_.unique.name.unique.0001-01-01-0000.nc",
            "casename.eam1990.unique.name.unique.0001-01-01-0000.nc",
            "casename.eam_1990.unique.name.unique.0001-01-01-0000.nc",
            "casename.eam1_1990.unique.name.unique.0001-01-01-0000.nc",
            "casename.eam11990.unique.name.unique.0001-01-01-0000.nc",
            "casename.eam.unique.name.unique.0001-01-01-0000.nc",
            "casename.eam.unique.name.unique.some.extra.0001-01-01-0000.nc",
        ]

        test_files = [
            "casename.eam.unique.name.unique.0001-01-01-0000.nc.base",
            "casename.eam.unique.name.unique.some.extra.0001-01-01-0000.nc.base",
        ]

        with self._setup_environment(fail_files + test_files) as temp_dir:
            hist_files = archiver.get_all_hist_files(
                "casename", "eam", suffix="base", from_dir=temp_dir
            )

        assert len(hist_files) == len(test_files)

        hist_files.sort()
        test_files.sort()

        for x, y in zip(hist_files, test_files):
            assert x == y, f"{x} != {y}"
