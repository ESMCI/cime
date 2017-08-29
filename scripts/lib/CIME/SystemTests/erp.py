"""
CIME ERP test.  This class inherits from SystemTestsCompareTwo

This is a pes counts hybrid (open-MP/MPI) restart bfb test from
startup.  This is just like an ERS test but the pe-counts/threading
count are modified on retart.
(1) Do an initial run with pes set up out of the box (suffix base)
(2) Do a restart test with half the number of tasks and threads (suffix rest)
"""

from CIME.XML.standard_module_setup import *
from CIME.case_setup import case_setup
from CIME.SystemTests.system_tests_compare_two import SystemTestsCompareTwo
from CIME.check_lockedfiles import *
from CIME.case_st_archive import _get_datenames

logger = logging.getLogger(__name__)

class ERP(SystemTestsCompareTwo):

    def __init__(self, case):
        """
        initialize a test object
        """
        SystemTestsCompareTwo.__init__(self, case,
                                       separate_builds = True,
                                       run_two_suffix = 'rest',
                                       run_one_description = 'initial',
                                       run_two_description = 'restart')

    def _common_setup(self):
        self._case.set_value("BUILD_THREADED",True)

    def _case_one_setup(self):
        stop_n      = self._case.get_value("STOP_N")

        expect(stop_n > 2, "ERROR: stop_n value {:d} too short".format(stop_n))

    def _case_two_setup(self):
        # halve the number of tasks and threads
        for comp in self._case.get_values("COMP_CLASSES"):
            ntasks    = self._case1.get_value("NTASKS_{}".format(comp))
            nthreads  = self._case1.get_value("NTHRDS_{}".format(comp))
            rootpe    = self._case1.get_value("ROOTPE_{}".format(comp))
            if ( nthreads > 1 ):
                self._case.set_value("NTHRDS_{}".format(comp), nthreads/2)
            if ( ntasks > 1 ):
                self._case.set_value("NTASKS_{}".format(comp), ntasks/2)
                self._case.set_value("ROOTPE_{}".format(comp), rootpe/2)

        stop_n = self._case1.get_value("STOP_N")
        rest_n = self._case1.get_value("REST_N")
        stop_new = stop_n - rest_n
        expect(stop_new > 0, "ERROR: stop_n value {:d} too short {:d} {:d}".format(stop_new,stop_n,rest_n))
        self._case.set_value("STOP_N", stop_new)
        self._case.set_value("HIST_N", stop_n)
        self._case.set_value("CONTINUE_RUN", True)
        self._case.set_value("REST_OPTION","never")

        # Note, some components, like CESM-CICE, have
        # decomposition information in env_build.xml that
        # needs to be regenerated for the above new tasks and thread counts
        case_setup(self._case, test_mode=True, reset=True)

    def _case_one_custom_postrun_action(self):
        rundir1 = self._case1.get_value("RUNDIR")
        rundir2 = self._case2.get_value("RUNDIR")
        case = self._case1.get_value("CASE")
        datenames = _get_datenames(self._case1)
        for file_ in glob.iglob(os.path.join(rundir1,"*")):
            logger.info("File is {}".format(file_))
            if os.path.basename(file_).startswith("rpointer"):
                logger.info("Copy {} to {}".format(file_, rundir2))
                shutil.copy(file_, rundir2)
            elif os.path.basename(file_).startswith(case) and datenames[0] in file_:
                file_case2 = os.path.join(rundir2, os.path.basename(file_))
                if not os.path.isfile(file_case2):
                    logger.info("Link {} to {}".format(file_, rundir2))
                    os.symlink(file_, file_case2)
