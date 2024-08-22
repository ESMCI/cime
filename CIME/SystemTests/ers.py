"""
CIME restart test  This class inherits from SystemTestsCommon
"""
from CIME.XML.standard_module_setup import *
from CIME.SystemTests.system_tests_common import SystemTestsCommon
import glob

logger = logging.getLogger(__name__)


class ERS(SystemTestsCommon):
    def __init__(self, case, **kwargs):
        """
        initialize an object interface to the ERS system test
        """
        SystemTestsCommon.__init__(self, case, **kwargs)

    def _ers_first_phase(self):
        self._rest_n = self._set_restart_interval()
        self.run_indv()

    def _ers_second_phase(self):
        stop_n = self._case.get_value("STOP_N")
        stop_option = self._case.get_value("STOP_OPTION")

        stop_new = stop_n - self._rest_n
        expect(
            stop_new > 0,
            "ERROR: stop_n value {:d} too short {:d} {:d}".format(
                stop_new, stop_n, self._rest_n
            ),
        )
        rundir = self._case.get_value("RUNDIR")
        for pfile in glob.iglob(os.path.join(rundir, "PET*")):
            os.rename(
                pfile,
                os.path.join(os.path.dirname(pfile), "run1." + os.path.basename(pfile)),
            )

        self._case.set_value("HIST_N", stop_n)
        self._case.set_value("STOP_N", stop_new)
        self._case.set_value("CONTINUE_RUN", True)
        self._case.set_value("REST_OPTION", "never")
        self._case.flush()
        logger.info("doing an {} {} restart test".format(str(stop_new), stop_option))
        self._skip_pnl = False
        self.run_indv(suffix="rest")

        # Compare restart file
        self._component_compare_test("base", "rest")

    def run_phase(self):
        self._ers_first_phase()
        self._ers_second_phase()
