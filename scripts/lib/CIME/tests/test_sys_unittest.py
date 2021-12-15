#!/usr/bin/env python3

import os
import shutil
import sys

from CIME import utils
from CIME.tests import base
from CIME.XML.compilers import Compilers


class TestUnitTest(base.BaseTestCase):
    @classmethod
    def setUpClass(cls):
        cls._do_teardown = []
        cls._testroot = os.path.join(cls.TEST_ROOT, "TestUnitTests")
        cls._testdirs = []
        os.environ["CIME_NO_CMAKE_MACRO"] = "ON"

    def _has_unit_test_support(self):
        if self.TEST_COMPILER is None:
            default_compiler = self.MACHINE.get_default_compiler()
            compiler = Compilers(self.MACHINE, compiler=default_compiler)
        else:
            compiler = Compilers(self.MACHINE, compiler=self.TEST_COMPILER)
        attrs = {"MPILIB": "mpi-serial", "compile_threaded": "FALSE"}
        pfunit_path = compiler.get_optional_compiler_node(
            "PFUNIT_PATH", attributes=attrs
        )
        if pfunit_path is None:
            return False
        else:
            return True

    def test_a_unit_test(self):
        cls = self.__class__
        if not self._has_unit_test_support():
            self.skipTest(
                "Skipping TestUnitTest - PFUNIT_PATH not found for the default compiler on this machine"
            )
        test_dir = os.path.join(cls._testroot, "unit_tester_test")
        cls._testdirs.append(test_dir)
        os.makedirs(test_dir)
        unit_test_tool = os.path.abspath(
            os.path.join(
                utils.get_cime_root(), "scripts", "fortran_unit_testing", "run_tests.py"
            )
        )
        test_spec_dir = os.path.join(
            os.path.dirname(unit_test_tool), "Examples", "interpolate_1d", "tests"
        )
        args = "--build-dir {} --test-spec-dir {}".format(test_dir, test_spec_dir)
        args += " --machine {}".format(self.MACHINE.get_machine_name())
        utils.run_cmd_no_fail("{} {}".format(unit_test_tool, args))
        cls._do_teardown.append(test_dir)

    def test_b_cime_f90_unit_tests(self):
        cls = self.__class__
        if self.FAST_ONLY:
            self.skipTest("Skipping slow test")

        if not self._has_unit_test_support():
            self.skipTest(
                "Skipping TestUnitTest - PFUNIT_PATH not found for the default compiler on this machine"
            )

        test_dir = os.path.join(cls._testroot, "driver_f90_tests")
        cls._testdirs.append(test_dir)
        os.makedirs(test_dir)
        test_spec_dir = utils.get_cime_root()
        unit_test_tool = os.path.abspath(
            os.path.join(
                test_spec_dir, "scripts", "fortran_unit_testing", "run_tests.py"
            )
        )
        args = "--build-dir {} --test-spec-dir {}".format(test_dir, test_spec_dir)
        args += " --machine {}".format(self.MACHINE.get_machine_name())
        utils.run_cmd_no_fail("{} {}".format(unit_test_tool, args))
        cls._do_teardown.append(test_dir)

    @classmethod
    def tearDownClass(cls):
        do_teardown = len(cls._do_teardown) > 0 and sys.exc_info() == (None, None, None) and not cls.NO_TEARDOWN
        del os.environ["CIME_NO_CMAKE_MACRO"]

        teardown_root = True
        for tfile in cls._testdirs:
            if tfile not in cls._do_teardown:
                print("Detected failed test or user request no teardown")
                print("Leaving case directory : %s" % tfile)
                teardown_root = False
            elif do_teardown:
                shutil.rmtree(tfile)

        if teardown_root and do_teardown:
            shutil.rmtree(cls._testroot)
