"""
Implementation of the CIME REUSEINITFILES test

This test does two runs:

(1) A standard initial run

(2) A run that reuses the init-generated files from run (1).

This verifies that it works to reuse these init-generated files, and that you can get
bit-for-bit results by doing so. This is important because these files are typically
reused whenever a user reruns an initial case.
"""

import os
import shutil
from CIME.XML.standard_module_setup import *
from CIME.SystemTests.system_tests_compare_two import SystemTestsCompareTwo
from CIME.SystemTests.system_tests_common import INIT_GENERATED_FILES_DIRNAME


class REUSEINITFILES(SystemTestsCompareTwo):
    def __init__(self, case):
        SystemTestsCompareTwo.__init__(
            self,
            case,
            separate_builds=False,
            run_two_suffix="reuseinit",
            run_one_description="standard initial run",
            run_two_description="reuse init-generated files from run 1",
            # The following line is a key part of this test: we will copy the
            # init_generated_files from case1 and then need to make sure they are NOT
            # deleted like is normally done for tests:
            case_two_keep_init_generated_files=True,
        )

    def _case_one_setup(self):
        pass

    def _case_two_setup(self):
        pass

    def _case_two_custom_prerun_action(self):
        case1_igf_dir = os.path.join(
            self._case1.get_value("RUNDIR"), INIT_GENERATED_FILES_DIRNAME
        )
        case2_igf_dir = os.path.join(
            self._case2.get_value("RUNDIR"), INIT_GENERATED_FILES_DIRNAME
        )

        expect(
            os.path.isdir(case1_igf_dir),
            "ERROR: Expected a directory named {} in case1's rundir".format(
                INIT_GENERATED_FILES_DIRNAME
            ),
        )
        if os.path.isdir(case2_igf_dir):
            shutil.rmtree(case2_igf_dir)

        shutil.copytree(case1_igf_dir, case2_igf_dir)
