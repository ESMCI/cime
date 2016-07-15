"""
Implementation of the CIME PET test.  This class inherits from SystemTestsCommon

This is an openmp test to determine that changing thread counts does not change answers.
(1) do an initial run where all components are threaded by default (suffix: base)
(2) do another initial run with nthrds=1 for all components (suffix: single_thread)
"""

import shutil
from CIME.XML.standard_module_setup import *
from CIME.case import Case
import CIME.utils
from CIME.case_setup import case_setup
from system_tests_common import SystemTestsCommon

logger = logging.getLogger(__name__)

class PET(SystemTestsCommon):

    def __init__(self, case):
        """
        initialize a test object
        """
        SystemTestsCommon.__init__(self, case)

    def build(self, sharedlib_only=False, model_only=False):
        exeroot = self._case.get_value("EXEROOT")
        cime_model = CIME.utils.get_model()

        # first make sure that all components have threaded settings
        for comp in ['ATM','CPL','OCN','WAV','GLC','ICE','ROF','LND']:
            if self._case.get_value("NTHRDS_%s"%comp) <= 1:
                self._case.set_value("NTHRDS_%s"%comp, 2)
        self._case.flush()

        case_setup(self._case, reset=True)

        self.clean_build()
        SystemTestsCommon.build(self, sharedlib_only=sharedlib_only, model_only=model_only)

    def _pet_first_phase(self):
        #Do a run with default threading
        self._case.set_value("CONTINUE_RUN",False)
        self._case.set_value("REST_OPTION","none")
        self._case.set_value("HIST_OPTION","$STOP_OPTION")
        self._case.set_value("HIST_N","$STOP_N")
        self._case.flush()

        stop_n = self._case.get_value("STOP_N")
        stop_option = self._case.get_value("STOP_OPTION")
        logger.info("doing a %d %s initial test with default threading, no restarts written" 
                    % (stop_n, stop_option))

        return SystemTestsCommon._run(self)

    def _pet_second_phase(self):
        #Do a run with all threads set to 1
        for comp in ['ATM','CPL','OCN','WAV','GLC','ICE','ROF','LND']:
                self._case.set_value("NTHRDS_%s"%comp, 1)
        self._case.flush()
        shutil.copy("env_mach_pes.xml", os.path.join("LockedFiles","env_mach_pes.xml"))

        stop_n = self._case.get_value("STOP_N")
        stop_option = self._case.get_value("STOP_OPTION")
        logger.info("doing a %d %s initial test with threads set to 1, no restarts written" 
                    % (stop_n, stop_option))

        return SystemTestsCommon._run(self, "single_thread")

        if success:
            return self._component_compare_test("base", "single_thread")
        else:
            return False

    def run(self):
        success = self._pet_first_phase()

        if success:
            return self._pet_second_phase()
        else:
            return False

    def report(self):
        SystemTestsCommon.report(self)
