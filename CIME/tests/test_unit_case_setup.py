#!/usr/bin/env python3

import os
import unittest
import tempfile
import contextlib
from pathlib import Path
from unittest import mock

from CIME.case import case_setup


@contextlib.contextmanager
def create_machines_dir():
    """Creates temp machines directory with fake content"""
    with tempfile.TemporaryDirectory() as temp_path:
        machines_path = os.path.join(temp_path, "machines")
        cmake_path = os.path.join(machines_path, "cmake_macros")
        Path(cmake_path).mkdir(parents=True)
        Path(os.path.join(cmake_path, "Macros.cmake")).touch()
        Path(os.path.join(cmake_path, "test.cmake")).touch()

        yield temp_path


@contextlib.contextmanager
def chdir(path):
    old_path = os.getcwd()
    os.chdir(path)

    try:
        yield
    finally:
        os.chdir(old_path)


# pylint: disable=protected-access
class TestCaseSetup(unittest.TestCase):
    @mock.patch("CIME.case.case_setup.copy_depends_files")
    def test_create_macros_cmake(self, copy_depends_files):
        machine_mock = mock.MagicMock()
        machine_mock.get_machine_name.return_value = "test"

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

            copy_depends_files.assert_called_with(
                "test", machines_path, case_path, "gnu-test"
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
