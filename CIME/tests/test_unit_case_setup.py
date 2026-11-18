#!/usr/bin/env python3

import os
import stat
import unittest
import tempfile
import contextlib
from pathlib import Path
from unittest import mock

import pytest

from CIME.case import case_setup
from CIME.core.exceptions import CIMEError
from CIME.locked_files import LOCKED_DIR
from CIME.tests.utils import chdir
from CIME.user_mod_support import SHELL_COMMANDS_POST_SETUP


class FakeCase:
    """Minimal stand-in for Case recording xml sync calls."""

    def __init__(self):
        self.calls = []

    def flush(self, flushall=False):
        self.calls.append("flush")

    def read_xml(self):
        self.calls.append("read_xml")


def _write_post_setup_commands(caseroot, contents):
    path = Path(caseroot, SHELL_COMMANDS_POST_SETUP)
    path.write_text(contents)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


@contextlib.contextmanager
def create_machines_dir():
    """Creates temp machines directory with fake content"""
    with tempfile.TemporaryDirectory() as temp_path:
        machines_path = os.path.join(temp_path, "machines")
        cmake_path = os.path.join(machines_path, "cmake_macros")
        Path(cmake_path).mkdir(parents=True)
        Path(os.path.join(cmake_path, "Macros.cmake")).touch()
        Path(os.path.join(cmake_path, "test.cmake")).touch()
        Path(os.path.join(cmake_path, "LINUX_gnu-test.cmake")).touch()

        yield temp_path


@contextlib.contextmanager
def create_machines_dir_with_includes():
    """Creates temp machines directory with cmake files containing includes"""
    with tempfile.TemporaryDirectory() as temp_path:
        machines_path = os.path.join(temp_path, "machines")
        cmake_path = os.path.join(machines_path, "cmake_macros")
        Path(cmake_path).mkdir(parents=True)

        # Create base Macros.cmake without includes (not recursively examined)
        Path(os.path.join(cmake_path, "Macros.cmake")).write_text("# Macros file\n")

        # Create common.cmake with an include
        common_content = "include(base_config.cmake)\n# Common definitions\n"
        Path(os.path.join(cmake_path, "common.cmake")).write_text(common_content)

        # Create utilities.cmake
        Path(os.path.join(cmake_path, "utilities.cmake")).write_text(
            "# Utility functions\n"
        )

        # Create base_config.cmake
        Path(os.path.join(cmake_path, "base_config.cmake")).write_text(
            "# Base configuration\n"
        )

        # Create test.cmake with an include
        test_content = "include(helper.cmake)\n# Test file\n"
        Path(os.path.join(cmake_path, "test.cmake")).write_text(test_content)

        # Create helper.cmake
        Path(os.path.join(cmake_path, "helper.cmake")).write_text("# Helper\n")

        yield temp_path


# pylint: disable=protected-access
class TestCaseSetup(unittest.TestCase):
    @mock.patch("CIME.case.case_setup.copy_depends_files")
    def test_create_macros_cmake(self, copy_depends_files):
        """Test that _create_macros_cmake copies machine and os_compiler cmake macros and depends files"""
        machine_mock = mock.MagicMock()
        machine_mock.get_machine_name.return_value = "test"
        # For a call to machine_mock.get_value("OS"), return "LINUX"; for anything else,
        # raise an exception
        machine_mock.get_value.side_effect = {"OS": "LINUX"}.__getitem__

        # create context stack to cleanup after test
        with contextlib.ExitStack() as stack:
            root_path = stack.enter_context(create_machines_dir())
            case_path = stack.enter_context(tempfile.TemporaryDirectory())

            machines_path = os.path.join(root_path, "machines")
            type(machine_mock).machines_dir = mock.PropertyMock(
                return_value=machines_path
            )

            # make sure we're calling everything from within the case root
            stack.enter_context(chdir(case_path))

            case_setup._create_macros_cmake(
                case_path,
                os.path.join(machines_path, "cmake_macros"),
                machine_mock,
                "gnu-test",
                os.path.join(case_path, "cmake_macros"),
            )

            assert os.path.exists(os.path.join(case_path, "Macros.cmake"))
            assert os.path.exists(os.path.join(case_path, "cmake_macros", "test.cmake"))
            assert os.path.exists(
                os.path.join(case_path, "cmake_macros", "LINUX_gnu-test.cmake")
            )

            copy_depends_files.assert_called_with(
                "test",
                machines_path,
                case_path,
                "gnu-test",
                "LINUX",
            )

    @mock.patch("CIME.case.case_setup._create_macros_cmake")
    def test_create_macros(self, _create_macros_cmake):
        case_mock = mock.MagicMock()

        machine_mock = mock.MagicMock()
        machine_mock.get_machine_name.return_value = "test"

        # create context stack to cleanup after test
        with contextlib.ExitStack() as stack:
            root_path = stack.enter_context(create_machines_dir())
            case_path = stack.enter_context(tempfile.TemporaryDirectory())

            cmake_macros_path = os.path.join(root_path, "machines", "cmake_macros")
            case_mock.get_value.return_value = cmake_macros_path

            machines_path = os.path.join(root_path, "machines")
            type(machine_mock).machines_dir = mock.PropertyMock(
                return_value=machines_path
            )

            # do not generate env_mach_specific.xml
            Path(os.path.join(case_path, "env_mach_specific.xml")).touch()

            case_setup._create_macros(
                case_mock,
                machine_mock,
                case_path,
                "gnu-test",
                "openmpi",
                False,
                "mct",
                "LINUX",
            )

            case_mock.get_value.assert_any_call("CMAKE_MACROS_DIR")

            # make sure we're calling everything from within the case root
            stack.enter_context(chdir(case_path))

            _create_macros_cmake.assert_called_with(
                case_path,
                cmake_macros_path,
                machine_mock,
                "gnu-test",
                os.path.join(case_path, "cmake_macros"),
            )

    def test_create_macros_copy_user(self):
        case_mock = mock.MagicMock()

        machine_mock = mock.MagicMock()
        machine_mock.get_machine_name.return_value = "test"

        # create context stack to cleanup after test
        with contextlib.ExitStack() as stack:
            root_path = stack.enter_context(create_machines_dir())
            case_path = stack.enter_context(tempfile.TemporaryDirectory())
            user_path = stack.enter_context(tempfile.TemporaryDirectory())

            user_cime_path = Path(os.path.join(user_path, ".cime"))
            user_cime_path.mkdir()
            user_cmake = user_cime_path / "user.cmake"
            user_cmake.touch()

            cmake_macros_path = os.path.join(root_path, "machines", "cmake_macros")
            case_mock.get_value.return_value = cmake_macros_path

            machines_path = os.path.join(root_path, "machines")
            type(machine_mock).machines_dir = mock.PropertyMock(
                return_value=machines_path
            )

            # do not generate env_mach_specific.xml
            Path(os.path.join(case_path, "env_mach_specific.xml")).touch()

            stack.enter_context(mock.patch.dict(os.environ, {"HOME": user_path}))

            # make sure we're calling everything from within the case root
            stack.enter_context(chdir(case_path))

            case_setup._create_macros(
                case_mock,
                machine_mock,
                case_path,
                "gnu-test",
                "openmpi",
                False,
                "mct",
                "LINUX",
            )

            case_mock.get_value.assert_any_call("CMAKE_MACROS_DIR")

            assert os.path.exists(os.path.join(case_path, "cmake_macros", "user.cmake"))

    def test_create_macros_copy_extra(self):
        case_mock = mock.MagicMock()

        machine_mock = mock.MagicMock()
        machine_mock.get_machine_name.return_value = "test"

        # create context stack to cleanup after test
        with contextlib.ExitStack() as stack:
            root_path = stack.enter_context(create_machines_dir())
            case_path = stack.enter_context(tempfile.TemporaryDirectory())
            extra_path = stack.enter_context(tempfile.TemporaryDirectory())

            extra_cmake_path = Path(extra_path, "cmake_macros")
            extra_cmake_path.mkdir()

            extra_macros_path = extra_cmake_path / "extra.cmake"
            extra_macros_path.touch()

            cmake_macros_path = os.path.join(root_path, "machines", "cmake_macros")
            case_mock.get_value.side_effect = [cmake_macros_path, extra_path]

            machines_path = os.path.join(root_path, "machines")
            type(machine_mock).machines_dir = mock.PropertyMock(
                return_value=machines_path
            )

            # do not generate env_mach_specific.xml
            Path(os.path.join(case_path, "env_mach_specific.xml")).touch()

            # make sure we're calling everything from within the case root
            stack.enter_context(chdir(case_path))

            case_setup._create_macros(
                case_mock,
                machine_mock,
                case_path,
                "gnu-test",
                "openmpi",
                False,
                "mct",
                "LINUX",
            )

            case_mock.get_value.assert_any_call("EXTRA_MACHDIR")

            assert os.path.exists(
                os.path.join(case_path, "cmake_macros", "extra.cmake")
            )

    @mock.patch("CIME.case.case_setup.copy_depends_files")
    def test_create_macros_cmake_recursive_includes(self, copy_depends_files):
        """Test that cmake includes are recursively copied"""
        machine_mock = mock.MagicMock()
        machine_mock.get_machine_name.return_value = "test"
        # For a call to machine_mock.get_value("OS"), return "LINUX"; for anything else,
        # raise an exception
        machine_mock.get_value.side_effect = {"OS": "LINUX"}.__getitem__

        # create context stack to cleanup after test
        with contextlib.ExitStack() as stack:
            root_path = stack.enter_context(create_machines_dir_with_includes())
            case_path = stack.enter_context(tempfile.TemporaryDirectory())

            machines_path = os.path.join(root_path, "machines")
            type(machine_mock).machines_dir = mock.PropertyMock(
                return_value=machines_path
            )

            # make sure we're calling everything from within the case root
            stack.enter_context(chdir(case_path))

            case_setup._create_macros_cmake(
                case_path,
                os.path.join(machines_path, "cmake_macros"),
                machine_mock,
                "gnu-test",
                os.path.join(case_path, "cmake_macros"),
            )

            # Verify main macro files are copied
            assert os.path.exists(os.path.join(case_path, "Macros.cmake"))
            assert os.path.exists(os.path.join(case_path, "cmake_macros", "test.cmake"))

            # Verify included files from test.cmake are recursively copied
            # (but NOT common.cmake or utilities.cmake, since Macros.cmake is not examined)
            assert os.path.exists(
                os.path.join(case_path, "cmake_macros", "helper.cmake")
            )

            # Verify that files included only by Macros.cmake are NOT copied
            assert not os.path.exists(
                os.path.join(case_path, "cmake_macros", "common.cmake")
            )
            assert not os.path.exists(
                os.path.join(case_path, "cmake_macros", "utilities.cmake")
            )

            # base_config.cmake should NOT be copied (only included by common.cmake)
            assert not os.path.exists(
                os.path.join(case_path, "cmake_macros", "base_config.cmake")
            )

            copy_depends_files.assert_called_with(
                "test",
                machines_path,
                case_path,
                "gnu-test",
                "LINUX",
            )


def test_run_post_setup_shell_commands_absent(tmp_path):
    # Context
    case = FakeCase()

    # Act
    case_setup._run_post_setup_shell_commands(case, str(tmp_path))

    # Assert
    assert case.calls == []
    assert not (tmp_path / LOCKED_DIR / SHELL_COMMANDS_POST_SETUP).exists()


def test_run_post_setup_shell_commands_first_setup(tmp_path):
    # Context
    case = FakeCase()
    contents = "#!/bin/sh\necho ran >> post_setup_result\n"
    _write_post_setup_commands(tmp_path, contents)

    # Act
    case_setup._run_post_setup_shell_commands(case, str(tmp_path))

    # Assert
    # Commands run from caseroot; xml state is flushed before and re-read after
    assert (tmp_path / "post_setup_result").read_text() == "ran\n"
    assert case.calls == ["flush", "read_xml"]
    locked = tmp_path / LOCKED_DIR / SHELL_COMMANDS_POST_SETUP
    assert locked.read_text() == contents


def test_run_post_setup_shell_commands_already_run(tmp_path):
    # Context
    case = FakeCase()
    contents = "#!/bin/sh\necho ran >> post_setup_result\n"
    _write_post_setup_commands(tmp_path, contents)
    (tmp_path / LOCKED_DIR).mkdir()
    (tmp_path / LOCKED_DIR / SHELL_COMMANDS_POST_SETUP).write_text(contents)

    # Act
    case_setup._run_post_setup_shell_commands(case, str(tmp_path))

    # Assert
    assert not (tmp_path / "post_setup_result").exists()
    assert case.calls == []


def test_run_post_setup_shell_commands_failure(tmp_path):
    # Context
    case = FakeCase()
    _write_post_setup_commands(
        tmp_path, "#!/bin/sh\necho ran >> post_setup_result\nexit 1\n"
    )

    # Act
    with pytest.raises(CIMEError):
        case_setup._run_post_setup_shell_commands(case, str(tmp_path))

    # Assert
    # A failed run is not recorded, so it is retried on the next case.setup
    assert (tmp_path / "post_setup_result").read_text() == "ran\n"
    assert not (tmp_path / LOCKED_DIR / SHELL_COMMANDS_POST_SETUP).exists()
    assert case.calls == ["flush"]
