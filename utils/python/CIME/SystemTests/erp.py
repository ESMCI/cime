"""
CIME ERP test.  This class inherits from SystemTestsCommon

This is a pes counts hybrid (open-MP/MPI) restart bfb test from
startup.  This is just like an ERS test but the pe-counts/threading
count are modified on retart.
(1) Do an initial run with pes set up out of the box (suffix base)
(2) Do a restart test with half the number of tasks and threads (suffix rest)
"""

import shutil
from CIME.XML.standard_module_setup import *
from CIME.case_setup import case_setup
import CIME.utils
from CIME.SystemTests.system_tests_compare_two import SystemTestsCompareTwo

logger = logging.getLogger(__name__)

class ERP(SystemTestsCompareTwo):

    def __init__(self, case):
        """
        initialize a test object
        """
        SystemTestsCompareTwo.__init__(self, case, run_one_st_archive = True)

    def _case_one_setup(self):
        pass

    def _case_two_setup(self):
        """ Case two uses half the number of threads and tasks as the defaults and case one. """
        for comp in self._case.get_values("COMP_CLASSES"):
            if comp == "DRV":
                comp = "CPL"
            ntasks = self._case.get_value("NTASKS_%s"%comp)
            if ntasks > 1:
                rootpe = self._case.get_value("ROOTPE_%s"%comp)
                self._case.set_value("NTASKS_%s"%comp, ntasks // 2)
                self._case.set_value("NTASKS_%s"%comp, rootpe // 2)
            nthreads = self._case.get_value("NTHRDS_%s"%comp)
            if nthreads > 1:
                self._case.set_value("BUILD_THREADED", True)
                self._case.set_value("NTHRDS_%s"%comp, nthreads // 2)
        case_setup(self._case, test_mode=True, reset=True)

    def _pre_run_hook(self):
        pass
