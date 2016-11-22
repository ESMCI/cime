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
from CIME.SystemTests.system_tests_compare_two import SystemTestsCompareTwo

logger = logging.getLogger(__name__)

def _compute_rest_n(stop_n):
    return stop_n // 2 + 1

class ERP(SystemTestsCompareTwo):

    def __init__(self, case):
        """
        initialize a test object
        """
        SystemTestsCompareTwo.__init__(self, case,
                                       separate_builds = True,
                                       run_two_suffix = "BFBRestTest",
                                       run_one_st_archive = True,
                                       run_one_description = "Baseline run from day 0 to STOP_N",
                                       run_two_description = ("Test run starting from run one's " +
                                                              "state at STOP_N // 2 + 1 to STOP_N.\n" +
                                                              "Run 2 is done with half of the " +
                                                              "number of tasks and threads as run 1"))

    def _case_one_setup(self):
        stop_n = self._case.get_value("STOP_N")
        rest_n = _compute_rest_n(stop_n)
        expect(stop_n > rest_n , "STOP_N value too small for test")
        self._case.set_value("REST_N", rest_n)
        self._case.set_value("REST_OPTION", self._case.get_value("STOP_OPTION"))

    def _case_two_setup(self):
        """ Case two uses half the number of threads and tasks as the defaults and case one. """
        self._case.set_value("REST_OPTION", "never")

        stop_n_tot = self._case.get_value("STOP_N")
        stop_n = stop_n_tot - _compute_rest_n(stop_n_tot)
        expect(stop_n > 0, "STOP_N value too small for test")
        self._case.set_value("STOP_N", stop_n)

        for comp in self._case.get_values("COMP_CLASSES"):
            if comp == "DRV":
                comp = "CPL"
            ntasks = self._case.get_value("NTASKS_%s"%comp)
            if ntasks > 1:
                rootpe = self._case.get_value("ROOTPE_%s"%comp)
                self._case.set_value("NTASKS_%s"%comp, ntasks // 2)
                self._case.set_value("ROOTPE_%s"%comp, rootpe // 2)
            nthreads = self._case.get_value("NTHRDS_%s"%comp)
            if nthreads > 1:
                self._case.set_value("BUILD_THREADED", True)
                self._case.set_value("NTHRDS_%s"%comp, nthreads // 2)

        ref_case = self._case1.get_value("CASE")
        self._case.set_value("RUN_REFCASE", ref_case)
        self._case.set_value("RUN_TYPE", "branch")

        case_setup(self._case, test_mode=True, reset=True)

    def _inter_run_hook(self):
        st_archive_dir_one = self._case1.get_value("DOUT_S_ROOT")
        restdir_name = "rest"
        restdir = os.path.join(st_archive_dir_one, restdir_name)
        rundir = self._case2.get_value("RUNDIR")
        rest_points = os.listdir(restdir)
        expect(len(rest_points) == 1, "Cannot determine the rest point to use")

        rest_time = rest_points[0]
        date = rest_time[:rest_time.rfind('-')]
        self._case2.set_value("RUN_REFDATE", date)
        time_of_day = rest_time[rest_time.rfind('-') + len('-'):]
        self._case2.set_value("RUN_REFTOD", time_of_day)

        rtime_dir = os.path.join(restdir, rest_time)
        files = os.listdir(rtime_dir)
        expect(len(files) > 0, "No rest files found")
        for f in files:
            fpath_in = os.path.join(rtime_dir, f)
            fpath_out = os.path.join(rundir, f)
            shutil.copy(fpath_in, fpath_out)
