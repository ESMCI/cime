#!/usr/bin/env python3

"""
This module contains unit tests of FakeCase from configure
This is seperate from FakeCase that's under CIME/tests
"""

import unittest
import os
from CIME.utils import get_model, CIMEError

from CIME.BuildTools.configure import FakeCase


class TestFakeCase(unittest.TestCase):
    def setUp(self):
        self.compiler = "intel"
        self.mpilib = "mpich"
        self.debug = "FALSE"
        self.comp_interface = "nuopc"
        self.model = get_model()
        self.srcroot = "."
        os.environ["SRCROOT"] = self.srcroot

    def create_fake_case(self, compiler, mpilib, debug, comp_interface, threading=False, gpu_type="none"):

        pio_version = 2
        fake_case = FakeCase(compiler, mpilib, debug, comp_interface, threading=threading, gpu_type=gpu_type)

        # Verify
        self.assertEqual(compiler, fake_case.get_value("COMPILER"))
        self.assertEqual(mpilib, fake_case.get_value("MPILIB"))
        self.assertEqual(debug, fake_case.get_value("DEBUG"))
        self.assertEqual(comp_interface, fake_case.get_value("COMP_INTERFACE"))
        self.assertEqual(gpu_type, fake_case.get_value("GPU_TYPE"))
        self.assertEqual(pio_version, fake_case.get_value("PIO_VERSION"))
        self.assertEqual(self.model, fake_case.get_value("MODEL"))
        self.assertEqual(self.srcroot, fake_case.get_value("SRCROOT"))
        self.assertEqual(threading, fake_case.get_build_threaded() )

        return fake_case

    def test_create_simple(self):
        fake_case = self.create_fake_case(self.compiler, self.mpilib, self.debug, self.comp_interface)

    def test_get_bad_setting(self):
        fake_case = self.create_fake_case(self.compiler, self.mpilib, self.debug, self.comp_interface)

        with self.assertRaisesRegex(CIMEError, "ERROR: FakeCase does not support getting value of 'ZZTOP'" ):
            fake_case.get_value("ZZTOP")
        

if __name__ == "__main__":
    unittest.main()
