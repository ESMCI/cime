import tempfile
import unittest
from unittest import mock
from pathlib import Path

from CIME import locked_files
from CIME.core.exceptions import CIMEError
from CIME.XML.entry_id import EntryID
from CIME.XML.env_batch import EnvBatch
from CIME.XML.files import Files


def create_batch_system(env_batch, batch_submit_value=None):
    batch_system = env_batch.make_child(
        name="batch_system", attributes={"type": "slurm"}
    )
    env_batch.make_child(name="batch_query", attributes={"args": ""}, root=batch_system)
    batch_submit = env_batch.make_child(
        name="batch_submit", root=batch_system, text=batch_submit_value
    )
    env_batch.make_child(name="batch_cancel", root=batch_system)
    env_batch.make_child(name="batch_redirect", root=batch_system)
    env_batch.make_child(name="batch_directive", root=batch_system)
    directives = env_batch.make_child(name="directives", root=batch_system)
    env_batch.make_child(name="directive", root=directives)

    return batch_system


def create_fake_env(tempdir):
    locked_files_dir = Path(tempdir, locked_files.LOCKED_DIR)

    locked_files_dir.mkdir(parents=True)

    locked_file_path = locked_files_dir / "env_batch.xml"

    env_batch = EnvBatch(tempdir)

    env_batch.write(force_write=True)

    batch_system = create_batch_system(env_batch, "sbatch")

    env_batch.write(str(locked_file_path), force_write=True)

    env_batch.remove_child(batch_system)

    batch_system = create_batch_system(env_batch)

    env_batch.write(force_write=True)

    return env_batch


class TestLockedFiles(unittest.TestCase):
    def test_check_diff_reset_and_rebuild(self):
        case = mock.MagicMock()

        # reset triggered by env_mach_pes
        # rebuild triggered by REBUILD_TRIGGER_ATM and REBUILD_TRIGGER_LND
        # COMP_CLASSES, REBUILD_TRIGGER_CPL, REBUILD_TRIGGER_ATM, REBUILD_TRIGGER_LND
        case.get_values.side_effect = (
            ("CPL", "ATM", "LND"),
            (),
            ("NTASKS",),
            ("NTASKS",),
        )

        diff = {
            "NTASKS": ("32", "16"),
        }

        expected_msg = """ERROR: For your changes to take effect, run:
./case.setup --reset
./case.build --clean atm lnd
./case.build"""

        with self.assertRaisesRegex(CIMEError, expected_msg):
            locked_files.check_diff(case, "env_mach_pes.xml", "env_mach_pes", diff)

    def test_check_diff_reset_and_rebuild_single(self):
        case = mock.MagicMock()

        # reset triggered by env_mach_pes
        # rebuild triggered only by REBUILD_TRIGGER_ATM
        # COMP_CLASSES, REBUILD_TRIGGER_CPL, REBUILD_TRIGGER_ATM, REBUILD_TRIGGER_LND
        case.get_values.side_effect = (("CPL", "ATM", "LND"), (), ("NTASKS",), ())

        diff = {
            "NTASKS": ("32", "16"),
        }

        expected_msg = """ERROR: For your changes to take effect, run:
./case.setup --reset
./case.build --clean atm
./case.build"""

        with self.assertRaisesRegex(CIMEError, expected_msg):
            locked_files.check_diff(case, "env_mach_pes.xml", "env_mach_pes", diff)

    def test_check_diff_env_mach_pes(self):
        case = mock.MagicMock()

        diff = {
            "NTASKS": ("32", "16"),
        }

        expected_msg = """ERROR: For your changes to take effect, run:
./case.setup --reset"""

        with self.assertRaisesRegex(CIMEError, expected_msg):
            locked_files.check_diff(case, "env_mach_pes.xml", "env_mach_pes", diff)

    def test_check_diff_env_build_no_diff(self):
        case = mock.MagicMock()

        diff = {}

        locked_files.check_diff(case, "env_build.xml", "env_build", diff)

        case.set_value.assert_not_called()

    def test_check_diff_env_build_pio_version(self):
        case = mock.MagicMock()

        diff = {
            "some_key": ("value1", "value2"),
            "PIO_VERSION": ("1", "2"),
        }

        expected_msg = """ERROR: For your changes to take effect, run:
./case.build --clean-all
./case.build"""

        with self.assertRaisesRegex(CIMEError, expected_msg):
            locked_files.check_diff(case, "env_build.xml", "env_build", diff)

        case.set_value.assert_any_call("BUILD_COMPLETE", False)
        case.set_value.assert_any_call("BUILD_STATUS", 2)

    def test_check_diff_env_build(self):
        case = mock.MagicMock()

        diff = {
            "some_key": ("value1", "value2"),
        }

        expected_msg = """ERROR: For your changes to take effect, run:
./case.build --clean-all
./case.build"""

        with self.assertRaisesRegex(CIMEError, expected_msg):
            locked_files.check_diff(case, "env_build.xml", "env_build", diff)

        case.set_value.assert_any_call("BUILD_COMPLETE", False)
        case.set_value.assert_any_call("BUILD_STATUS", 1)

    def test_check_diff_env_batch(self):
        case = mock.MagicMock()

        diff = {
            "some_key": ("value1", "value2"),
        }

        expected_msg = """ERROR: For your changes to take effect, run:
./case.setup --reset"""

        with self.assertRaisesRegex(CIMEError, expected_msg):
            locked_files.check_diff(case, "env_batch.xml", "env_batch", diff)

    def test_check_diff_env_case(self):
        case = mock.MagicMock()

        diff = {
            "some_key": ("value1", "value2"),
        }

        expected_msg = (
            "ERROR: Cannot change `env_case.xml`, please restore origin 'env_case.xml'"
        )

        with self.assertRaisesRegex(CIMEError, expected_msg):
            locked_files.check_diff(case, "env_case.xml", "env_case", diff)

    def test_diff_lockedfile_detect_difference(self):
        case = mock.MagicMock()

        with tempfile.TemporaryDirectory() as tempdir:
            case.get_value.side_effect = (tempdir,)

            env_batch = create_fake_env(tempdir)

            case.get_env.return_value = env_batch

            _, diff = locked_files.diff_lockedfile(case, tempdir, "env_batch.xml")

            assert diff
            assert diff["batch_submit"] == [None, "sbatch"]

    def test_diff_lockedfile_not_supported(self):
        case = mock.MagicMock()

        with tempfile.TemporaryDirectory() as tempdir:
            case.get_value.side_effect = (tempdir,)

            locked_file_path = Path(tempdir, locked_files.LOCKED_DIR, "env_new.xml")

            locked_file_path.parent.mkdir(parents=True)

            locked_file_path.touch()

            _, diff = locked_files.diff_lockedfile(case, tempdir, "env_new.xml")

            assert not diff

    def test_diff_lockedfile_does_not_exist(self):
        case = mock.MagicMock()

        with tempfile.TemporaryDirectory() as tempdir:
            case.get_value.side_effect = (tempdir,)

            locked_files.diff_lockedfile(case, tempdir, "env_batch.xml")

    def test_diff_lockedfile(self):
        case = mock.MagicMock()

        with tempfile.TemporaryDirectory() as tempdir:
            case.get_value.side_effect = (tempdir,)

            create_fake_env(tempdir)

            locked_files.diff_lockedfile(case, tempdir, "env_batch.xml")

    def test_check_lockedfile(self):
        case = mock.MagicMock()

        with tempfile.TemporaryDirectory() as tempdir:
            case.get_value.side_effect = (tempdir,)

            create_fake_env(tempdir)

            with self.assertRaises(CIMEError):
                locked_files.check_lockedfile(case, "env_batch.xml")

    def test_check_lockedfiles_skip(self):
        case = mock.MagicMock()

        with tempfile.TemporaryDirectory() as tempdir:
            case.get_value.side_effect = (tempdir,)

            create_fake_env(tempdir)

            locked_files.check_lockedfiles(case, skip="env_batch.xml")

    def test_check_lockedfiles(self):
        case = mock.MagicMock()

        with tempfile.TemporaryDirectory() as tempdir:
            case.get_value.side_effect = (tempdir,)

            create_fake_env(tempdir)

            with self.assertRaises(CIMEError):
                locked_files.check_lockedfiles(case)

    def test_check_lockedfiles_quiet(self):
        case = mock.MagicMock()

        with tempfile.TemporaryDirectory() as tempdir:
            case.get_value.side_effect = (tempdir,)

            create_fake_env(tempdir)

            # Should not raise exception
            locked_files.check_lockedfiles(case, quiet=True)

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

    def test_check_diff_env_run_lock_on_restart(self):
        """Verify that modifying a lock_on_restart variable when CONTINUE_RUN=TRUE raises a CIMEError."""
        case = mock.MagicMock()
        l_env = mock.MagicMock()
        l_env.is_lock_on_restart.side_effect = lambda k: k == "CALENDAR"
        case.get_env.return_value = l_env
        case.get_value.side_effect = lambda k: True if k == "CONTINUE_RUN" else ()

        diff = {"CALENDAR": ("GREGORIAN", "NO_LEAP")}

        expected_msg = "Cannot change variable\\(s\\) 'CALENDAR' on a continued run \\(CONTINUE_RUN=TRUE\\)"
        with self.assertRaisesRegex(CIMEError, expected_msg):
            locked_files.check_diff(case, "env_run.xml", "env_run", diff)

    def test_check_diff_env_run_not_continue_run(self):
        """Verify that modifying a lock_on_restart variable when CONTINUE_RUN=FALSE does not raise an error."""
        case = mock.MagicMock()
        l_env = mock.MagicMock()
        l_env.is_lock_on_restart.side_effect = lambda k: k == "CALENDAR"
        case.get_env.return_value = l_env
        case.get_value.side_effect = lambda k: False if k == "CONTINUE_RUN" else ()

        diff = {"CALENDAR": ("GREGORIAN", "NO_LEAP")}
        # Should not raise CIMEError
        locked_files.check_diff(case, "env_run.xml", "env_run", diff)

    def test_check_diff_env_run_unlocked_var_continue_run(self):
        """Verify that modifying a non-lock_on_restart variable when CONTINUE_RUN=TRUE does not raise an error."""
        case = mock.MagicMock()
        l_env = mock.MagicMock()
        l_env.is_lock_on_restart.side_effect = lambda k: False
        case.get_env.return_value = l_env
        case.get_value.side_effect = lambda k: True if k == "CONTINUE_RUN" else ()

        diff = {"STOP_N": ("10", "5")}
        # Should not raise CIMEError
        locked_files.check_diff(case, "env_run.xml", "env_run", diff)

    def test_continue_run_true_with_locked_var_changed(self):
        """Verify that enabling CONTINUE_RUN=TRUE when a lock_on_restart variable has changed raises CIMEError."""
        case = mock.MagicMock()
        l_env = mock.MagicMock()
        l_env.is_lock_on_restart.side_effect = lambda k: k == "CALENDAR"
        case.get_env.return_value = l_env
        case.get_value.side_effect = lambda k: True if k == "CONTINUE_RUN" else ()

        diff = {"CONTINUE_RUN": ("TRUE", "FALSE"), "CALENDAR": ("GREGORIAN", "NO_LEAP")}

        expected_msg = "Cannot change variable\\(s\\) 'CALENDAR' on a continued run \\(CONTINUE_RUN=TRUE\\)"
        with self.assertRaisesRegex(CIMEError, expected_msg):
            locked_files.check_diff(case, "env_run.xml", "env_run", diff)

    def test_continue_run_true_with_no_locked_var_changed(self):
        """Verify that enabling CONTINUE_RUN=TRUE when no lock_on_restart variable has changed passes cleanly."""
        case = mock.MagicMock()
        l_env = mock.MagicMock()
        l_env.is_lock_on_restart.side_effect = lambda k: False
        case.get_env.return_value = l_env
        case.get_value.side_effect = lambda k: True if k == "CONTINUE_RUN" else ()

        diff = {"CONTINUE_RUN": ("TRUE", "FALSE"), "STOP_N": ("10", "5")}
        # Should not raise CIMEError
        locked_files.check_diff(case, "env_run.xml", "env_run", diff)

    def test_is_lock_on_restart(self):
        """Verify that EntryID.is_lock_on_restart detects lock_on_restart attributes or tags."""
        with tempfile.NamedTemporaryFile("w+", suffix=".xml") as tf:
            tf.write("""<entry_id>
<entry id="VAR_LOCKED" lock_on_restart="true">
  <type>char</type>
</entry>
<entry id="VAR_UNLOCKED">
  <type>char</type>
</entry>
</entry_id>""")
            tf.flush()
            entry_id = EntryID(tf.name)
            self.assertTrue(entry_id.is_lock_on_restart("VAR_LOCKED"))
            self.assertFalse(entry_id.is_lock_on_restart("VAR_UNLOCKED"))
            self.assertFalse(entry_id.is_lock_on_restart("NON_EXISTENT_VAR"))



