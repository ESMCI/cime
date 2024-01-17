#!/usr/bin/env python3

import os
import shutil
import sys

from CIME import utils
from CIME.tests import base


class TestGridGeneration(base.BaseTestCase):
    @classmethod
    def setUpClass(cls):
        cls._do_teardown = []
        cls._testroot = os.path.join(cls.TEST_ROOT, "TestGridGeneration")
        cls._testdirs = []

    def test_gen_domain(self):
        if self._config.test_mode == "cesm":
            self.skipTest("Skipping gen_domain test. Depends on E3SM tools")
        cime_root = utils.get_cime_root()
        inputdata = self.MACHINE.get_value("DIN_LOC_ROOT")

        tool_name = "test_gen_domain"
        tool_location = os.path.join(
            cime_root, "tools", "mapping", "gen_domain_files", "test_gen_domain.sh"
        )
        args = "--cime_root={} --inputdata_root={}".format(cime_root, inputdata)

        cls = self.__class__
        test_dir = os.path.join(cls._testroot, tool_name)
        cls._testdirs.append(test_dir)
        os.makedirs(test_dir)
        self.run_cmd_assert_result(
            "{} {}".format(tool_location, args), from_dir=test_dir
        )
        cls._do_teardown.append(test_dir)

    @classmethod
    def tearDownClass(cls):
        do_teardown = (
            len(cls._do_teardown) > 0
            and sys.exc_info() == (None, None, None)
            and not cls.NO_TEARDOWN
        )
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
