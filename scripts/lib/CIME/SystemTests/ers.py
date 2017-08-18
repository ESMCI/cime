"""
CIME restart test  This class inherits from SystemTestsCompareTwo
"""
from CIME.XML.standard_module_setup import *
from CIME.SystemTests.system_tests_compare_two import SystemTestsCompareTwo

logger = logging.getLogger(__name__)

class ERS(SystemTestsCompareTwo):

    def __init__(self, case):
        """
        initialize an object interface to the ERS system test
        """
        SystemTestsCompareTwo.__init__(self, case,
                                       separate_builds = False,
                                       separate_runs = False,
                                       run_two_suffix = 'rest',
                                       run_one_description = 'initial',
                                       run_two_description = 'restart')

    def _case_one_setup(self):
        stop_n      = self._case.get_value("STOP_N")

        expect(stop_n > 0, "Bad STOP_N: {:d}".format(stop_n))
        expect(stop_n > 2, "ERROR: stop_n value {:d} too short".format(stop_n))

    def _case_two_setup(self):
        stop_n      = self._case.get_value("STOP_N")

        rest_n = stop_n/2 + 1
        stop_new = stop_n - rest_n
        expect(stop_new > 0, "ERROR: stop_n value {:d} too short {:d} {:d}".format(stop_new,stop_n,rest_n))

        self._case.set_value("HIST_N", stop_n)
        self._case.set_value("STOP_N", stop_new)
        self._case.set_value("CONTINUE_RUN", True)
        self._case.set_value("REST_OPTION","never")
        self._case.flush()
