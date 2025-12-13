#!/usr/bin/env python3

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from CIME import date
from CIME.case import case_st_archive
from CIME.XML import env_archive as _env_archive
from CIME.tests import utils

UNSET = r"""<components version="2.0">
  <comp_archive_spec compname="drv" compclass="cpl">
    <rpointer>
      <rpointer_file>unset</rpointer_file>
      <rpointer_content >$CASE.cpl$NINST_STRING.r.$DATENAME.nc</rpointer_content>
    </rpointer>
  </comp_archive_spec>
</components>
"""

UNSET_CONTENT = r"""<components version="2.0">
  <comp_archive_spec compname="drv" compclass="cpl">
    <rpointer>
      <rpointer_file>rpointer.cpl$NINST_STRING.$DATENAME</rpointer_file>
      <rpointer_content>unset</rpointer_content>
    </rpointer>
  </comp_archive_spec>
</components>
"""

SINGLE_NINST_DATE = r"""<components version="2.0">
  <comp_archive_spec compname="drv" compclass="cpl">
    <rpointer>
      <rpointer_file>rpointer.cpl$NINST_STRING.$DATENAME</rpointer_file>
      <rpointer_content >$CASE.cpl$NINST_STRING.r.$DATENAME.nc</rpointer_content>
    </rpointer>
  </comp_archive_spec>
</components>
"""


def write_files(*files):
    for file, content in files:
        p = Path(file)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.open("w").write(content or "")


class TestArchiveRpointerFiles(unittest.TestCase):
    @mock.patch("shutil.move")
    @mock.patch("CIME.case.case_st_archive.safe_copy")
    @utils.mock_env(_env_archive.EnvArchive, SINGLE_NINST_DATE)
    def test_generate_rpointer(self, env_archive, safe_copy, move):
        archive_entry = env_archive.get_archive_specs()[0]

        with tempfile.TemporaryDirectory() as tempdir:
            run_dir = Path(tempdir, "run")
            rest_dir = Path(tempdir, "archive", "rest", "0001-01-01")
            rest_dir.mkdir(parents=True)

            case_st_archive._archive_rpointer_files(
                "case",
                [],
                str(run_dir),
                True,
                env_archive,
                archive_entry,
                str(rest_dir),
                date.date(1, 1, 1),
                False,
            )

            safe_copy.assert_not_called()

            move.assert_not_called()

            # should have created the file
            generated_files = list(rest_dir.glob("*"))
            assert generated_files == [rest_dir / "rpointer.cpl.0001-01-01-00000"]

            with (rest_dir / "rpointer.cpl.0001-01-01-00000").open("r") as f:
                content = f.read()

            # check content
            assert content == "case.cpl.r.0001-01-01-00000.nc \n"

    @mock.patch("shutil.move")
    @mock.patch("CIME.case.case_st_archive.safe_copy")
    @utils.mock_env(_env_archive.EnvArchive, UNSET_CONTENT)
    def test_generate_rpointer_unset_content(self, env_archive, safe_copy, move):
        archive_entry = env_archive.get_archive_specs()[0]

        with tempfile.TemporaryDirectory() as tempdir:
            run_dir = Path(tempdir, "run")
            rest_dir = Path(tempdir, "archive", "rest", "0001-01-01")
            rest_dir.mkdir(parents=True)

            case_st_archive._archive_rpointer_files(
                "case",
                [],
                str(run_dir),
                True,
                env_archive,
                archive_entry,
                str(rest_dir),
                date.date(1, 1, 1),
                False,
            )

            safe_copy.assert_not_called()

            move.assert_not_called()

            # should have created the file
            generated_files = list(rest_dir.glob("*"))
            assert generated_files == []

    @mock.patch("shutil.move")
    @mock.patch("CIME.case.case_st_archive.safe_copy")
    @utils.mock_env(_env_archive.EnvArchive, SINGLE_NINST_DATE)
    def test_ninst_generate_rpointer(self, env_archive, safe_copy, move):
        archive_entry = env_archive.get_archive_specs()[0]

        with tempfile.TemporaryDirectory() as tempdir:
            run_dir = Path(tempdir, "run")
            rest_dir = Path(tempdir, "archive", "rest", "0001-01-01")
            rest_dir.mkdir(parents=True)

            case_st_archive._archive_rpointer_files(
                "case",
                ["01", "02"],
                str(run_dir),
                True,
                env_archive,
                archive_entry,
                str(rest_dir),
                date.date(1, 1, 1),
                False,
            )

            safe_copy.assert_not_called()

            move.assert_not_called()

            # should have created the file
            generated_files = list(rest_dir.glob("*"))
            assert sorted(generated_files) == sorted(
                [
                    rest_dir / "rpointer.cpl01.0001-01-01-00000",
                    rest_dir / "rpointer.cpl02.0001-01-01-00000",
                ]
            )

            with (rest_dir / "rpointer.cpl01.0001-01-01-00000").open("r") as f:
                content = f.read()

            # check content
            assert content == "case.cpl01.r.0001-01-01-00000.nc \n"

    @mock.patch("shutil.move")
    @mock.patch("CIME.case.case_st_archive.safe_copy")
    @utils.mock_env(_env_archive.EnvArchive, SINGLE_NINST_DATE)
    def test_datename_is_last(self, env_archive, safe_copy, move):
        archive_entry = env_archive.get_archive_specs()[0]

        with tempfile.TemporaryDirectory() as tempdir:
            run_dir = Path(tempdir, "run")
            rest_dir = Path(tempdir, "archive", "rest", "0001-01-01")
            rest_dir.mkdir(parents=True)

            write_files(
                (run_dir / "rpointer.cpl.0001-01-01-00000", ""),
            )

            case_st_archive._archive_rpointer_files(
                "case",
                [],
                str(run_dir),
                True,
                env_archive,
                archive_entry,
                str(rest_dir),
                date.date(1, 1, 1),
                True,
            )

            safe_copy.assert_any_call(
                str(run_dir / "rpointer.cpl.0001-01-01-00000"),
                str(rest_dir / "rpointer.cpl.0001-01-01-00000"),
            )

            move.assert_not_called()

    @mock.patch("shutil.move")
    @mock.patch("CIME.case.case_st_archive.safe_copy")
    @utils.mock_env(_env_archive.EnvArchive, SINGLE_NINST_DATE)
    def test_ninst(self, env_archive, safe_copy, move):
        archive_entry = env_archive.get_archive_specs()[0]

        with tempfile.TemporaryDirectory() as tempdir:
            run_dir = Path(tempdir, "run")
            rest_dir = Path(tempdir, "archive", "rest", "0001-01-01")
            rest_dir.mkdir(parents=True)

            write_files(
                (run_dir / "rpointer.cpl.01.0001-01-01-00000", ""),
                (run_dir / "rpointer.cpl.02.0001-01-01-00000", ""),
            )

            case_st_archive._archive_rpointer_files(
                "case",
                ["01", "02"],
                str(run_dir),
                True,
                env_archive,
                archive_entry,
                str(rest_dir),
                date.date(1, 1, 1),
                False,
            )

            safe_copy.assert_not_called()

            move.assert_any_call(
                str(run_dir / "rpointer.cpl.01.0001-01-01-00000"),
                str(rest_dir / "rpointer.cpl.01.0001-01-01-00000"),
            )
            move.assert_any_call(
                str(run_dir / "rpointer.cpl.02.0001-01-01-00000"),
                str(rest_dir / "rpointer.cpl.02.0001-01-01-00000"),
            )

    @mock.patch("shutil.move")
    @mock.patch("CIME.case.case_st_archive.safe_copy")
    @utils.mock_env(_env_archive.EnvArchive, SINGLE_NINST_DATE)
    def test_single_rpointer(self, env_archive, safe_copy, move):
        archive_entry = env_archive.get_archive_specs()[0]

        with tempfile.TemporaryDirectory() as tempdir:
            run_dir = Path(tempdir, "run")
            rest_dir = Path(tempdir, "archive", "rest", "0001-01-01")
            rest_dir.mkdir(parents=True)

            write_files(
                (run_dir / "rpointer.cpl.0001-01-01-00000", ""),
            )

            case_st_archive._archive_rpointer_files(
                "case",
                [],
                str(run_dir),
                True,
                env_archive,
                archive_entry,
                str(rest_dir),
                date.date(1, 1, 1),
                False,
            )

            safe_copy.assert_not_called()

            move.assert_called_once()
            move.assert_any_call(
                str(run_dir / "rpointer.cpl.0001-01-01-00000"),
                str(rest_dir / "rpointer.cpl.0001-01-01-00000"),
            )

    @mock.patch("shutil.move")
    @mock.patch("CIME.case.case_st_archive.safe_copy")
    @utils.mock_env(_env_archive.EnvArchive, UNSET)
    def test_unset(self, env_archive, safe_copy, move):
        archive_entry = env_archive.get_archive_specs()[0]

        with tempfile.TemporaryDirectory() as tempdir:
            run_dir = Path(tempdir, "run")
            rest_dir = Path(tempdir, "archive", "rest", "0001-01-01")
            rest_dir.mkdir(parents=True)

            case_st_archive._archive_rpointer_files(
                "case",
                [],
                str(run_dir),
                True,
                env_archive,
                archive_entry,
                str(rest_dir),
                date.date(1, 1, 1),
                False,
            )

        safe_copy.assert_not_called()

        move.assert_not_called()
