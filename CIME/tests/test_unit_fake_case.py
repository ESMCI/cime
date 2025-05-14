#!/usr/bin/env python3

"""
This module contains unit tests of FakeCase from configure
This is seperate from FakeCase that's under CIME/tests
"""

import unittest

from CIME.BuildTools.configure import FakeCase


class TestFakeCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def create_fake_case(self, compiler, mpilib, debug, comp_interface, threading=False, gpu_type="none"):

        casedir = "."
        pio_version = 2
        fake_case = FakeCase(compiler, mpilib, debug, comp_interface, threading=threading, gpu_type=gpu_type)

        # Verify
        self.assertEqual(compiler, fake_case.get_value("COMPILER"))
        self.assertEqual(mpilib, fake_case.get_value("MPILIB"))
        self.assertEqual(debug, fake_case.get_value("DEBUG"))
        self.assertEqual(comp_interface, fake_case.get_value("COMP_INTERFACE"))
        self.assertEqual(gpu_type, fake_case.get_value("GPU_TYPE"))
        self.assertEqual(pio_version, fake_case.get_value("PIO_VERSION"))
        self.assertEqual(threading, fake_case.get_build_threaded() )
        #self.assertEqual(casedir, fake_case.get_case_root() )

    def test_create_simple(self):
        # Setup
        compiler = "intel"
        mpilib = "mpich"
        debug = "FALSE"
        comp_interface = "nuopc"

        self.create_fake_case(compiler, mpilib, debug, comp_interface)


if __name__ == "__main__":
    unittest.main()
