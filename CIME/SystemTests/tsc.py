"""
Solution reproducibility test based on time-step convergence
The CESM/ACME model's
multi-instance capability is used to conduct an ensemble
of simulations starting from different initial conditions.

This class inherits from SystemTestsCommon.
"""

import os
import json
import logging

from shutil import copytree

import CIME.test_status
import CIME.utils
from CIME.status import append_testlog
from CIME.SystemTests.system_tests_common import SystemTestsCommon
from CIME.case.case_setup import case_setup
from CIME.hist_utils import rename_all_hist_files
from CIME.XML.machines import Machines

import evv4esm  # pylint: disable=import-error
from evv4esm.__main__ import main as evv  # pylint: disable=import-error

evv_lib_dir = os.path.abspath(os.path.dirname(evv4esm.__file__))

logger = logging.getLogger(__name__)


NINST = 12
SIM_LENGTH = 600  # seconds
OUT_FREQ = 10  # seconds
INSPECT_AT = [300, 450, 600]  # seconds
INIT_COND_FILE_TEMPLATE = (
    "20240305.v3p0p0.F2010.ne4pg2_oQU480.chrysalis.{}.{}.0002-{:02d}-01-00000.nc"
)
VAR_LIST = [
    "T",
    "Q",
    "V",
    "CLDLIQ",
    "CLDICE",
    "NUMLIQ",
    "NUMICE",
    "num_a1",
    "num_a2",
    "num_a3",
]
P_THRESHOLD = 0.005


class TSC(SystemTestsCommon):
    def __init__(self, case, **kwargs):
        """
        initialize an object interface to the TSC test
        """
        super(TSC, self).__init__(case, **kwargs)
        if self._case.get_value("MODEL") == "e3sm":
            self.atmmod = "eam"
            self.lndmod = "elm"
            self.atmmodIC = "eam"
            self.lndmodIC = "elm"
        else:
            self.atmmod = "cam"
            self.lndmod = "clm"
            self.atmmodIC = "cam"
            self.lndmodIC = "clm2"

    def build_phase(self, sharedlib_only=False, model_only=False):
        # Only want this to happen once. It will impact the sharedlib build
        # so it has to happen there.
        if not model_only:
            logging.warning("Starting to build multi-instance exe")
            for comp in ["ATM", "OCN", "WAV", "GLC", "ICE", "ROF", "LND"]:
                ntasks = self._case.get_value("NTASKS_{}".format(comp))
                self._case.set_value("ROOTPE_{}".format(comp), 0)
                self._case.set_value("NINST_{}".format(comp), NINST)
                self._case.set_value("NTASKS_{}".format(comp), ntasks * NINST)

            self._case.set_value("ROOTPE_CPL", 0)
            self._case.set_value("NTASKS_CPL", ntasks * NINST)
            self._case.flush()

            case_setup(self._case, test_mode=False, reset=True)

        self.build_indv(sharedlib_only=sharedlib_only, model_only=model_only)

    def _run_with_specified_dtime(self, dtime=2):
        """
        Conduct one multi-instance run with a specified time step size.

        :param dtime (int): Specified time step size in seconds
        """
        coupling_frequency = 86400 // dtime

        self._case.set_value("ATM_NCPL", str(coupling_frequency))
        se_tstep = dtime / 12

        nsteps = SIM_LENGTH // dtime
        self._case.set_value("STOP_N", str(nsteps))
        self._case.set_value("STOP_OPTION", "nsteps")

        csmdata_root = self._case.get_value("DIN_LOC_ROOT")
        csmdata_atm = os.path.join(csmdata_root, "atm/cam/inic/homme/ne4pg2_v3_init")
        csmdata_lnd = os.path.join(csmdata_root, "lnd/clm2/initdata/ne4pg2_v3_init")

        nstep_output = OUT_FREQ // dtime
        for iinst in range(1, NINST + 1):
            fatm_in = os.path.join(
                csmdata_atm,
                INIT_COND_FILE_TEMPLATE.format(self.atmmodIC, "i", iinst),
            )
            flnd_in = os.path.join(
                csmdata_lnd,
                INIT_COND_FILE_TEMPLATE.format(self.lndmodIC, "r", iinst),
            )

            with open(f"user_nl_{self.atmmod}_{iinst:04d}", "w+") as atmnlfile:

                atmnlfile.write("ncdata  = '{}' \n".format(fatm_in))

                atmnlfile.write("dtime = {} \n".format(dtime))
                atmnlfile.write("se_tstep = {} \n".format(se_tstep))
                atmnlfile.write("iradsw = 2 \n")
                atmnlfile.write("iradlw = 2 \n")

                atmnlfile.write("avgflag_pertape = 'I' \n")
                atmnlfile.write("nhtfrq = {} \n".format(nstep_output))
                atmnlfile.write("mfilt = 1 \n")
                atmnlfile.write("ndens = 1 \n")
                atmnlfile.write("empty_htapes = .true. \n")
                atmnlfile.write(
                    "fincl1 = 'PS','U','LANDFRAC',{} \n".format(
                        "".join(["'{}',".format(s) for s in VAR_LIST])[:-1]
                    )
                )

            with open(f"user_nl_{self.lndmod}_{iinst:04d}", "w+") as lndnlfile:
                lndnlfile.write("finidat = '{}' \n".format(flnd_in))
                lndnlfile.write("dtime = {} \n".format(dtime))

        # Force rebuild namelists
        self._skip_pnl = False

        self.run_indv()

        rename_all_hist_files(self._case, suffix="DT{:04d}".format(dtime))

    def run_phase(self):
        self._run_with_specified_dtime(dtime=2)

        if self._case.get_value("GENERATE_BASELINE"):
            self._run_with_specified_dtime(dtime=1)

    def _compare_baseline(self):
        with self._test_status as ts:
            ts.set_status(
                CIME.test_status.BASELINE_PHASE, CIME.test_status.TEST_FAIL_STATUS
            )

            run_dir = self._case.get_value("RUNDIR")
            case_name = self._case.get_value("CASE")
            base_dir = os.path.join(
                self._case.get_value("BASELINE_ROOT"),
                self._case.get_value("BASECMP_CASE"),
            )

            test_name = "{}".format(case_name.split(".")[-1])
            evv_config = {
                test_name: {
                    "module": os.path.join(evv_lib_dir, "extensions", "tsc.py"),
                    "test-case": case_name,
                    "test-dir": run_dir,
                    "ref-case": "Baseline",
                    "ref-dir": base_dir,
                    "time-slice": [OUT_FREQ, SIM_LENGTH],
                    "inspect-times": INSPECT_AT,
                    "variables": VAR_LIST,
                    "p-threshold": P_THRESHOLD,
                    "component": self.atmmod,
                }
            }

            json_file = os.path.join(run_dir, ".".join([case_name, "json"]))
            with open(json_file, "w") as config_file:
                json.dump(evv_config, config_file, indent=4)

            evv_out_dir = os.path.join(run_dir, ".".join([case_name, "evv"]))
            evv(["-e", json_file, "-o", evv_out_dir])

            with open(os.path.join(evv_out_dir, "index.json"), "r") as evv_f:
                evv_status = json.load(evv_f)

            comments = ""
            for evv_ele in evv_status["Page"]["elements"]:
                if "Table" in evv_ele:
                    comments = "; ".join(
                        "{}: {}".format(key, val[0])
                        for key, val in evv_ele["Table"]["data"].items()
                    )
                    if evv_ele["Table"]["data"]["Test status"][0].lower() == "pass":
                        self._test_status.set_status(
                            CIME.test_status.BASELINE_PHASE,
                            CIME.test_status.TEST_PASS_STATUS,
                        )
                    break

            status = self._test_status.get_status(CIME.test_status.BASELINE_PHASE)
            mach_name = self._case.get_value("MACH")
            mach_obj = Machines(machine=mach_name)
            htmlroot = CIME.utils.get_htmlroot(mach_obj)
            urlroot = CIME.utils.get_urlroot(mach_obj)
            if htmlroot is not None:
                with CIME.utils.SharedArea():
                    copytree(
                        evv_out_dir,
                        os.path.join(htmlroot, "evv", case_name),
                    )
                if urlroot is None:
                    urlroot = "[{}_URL]".format(mach_name.capitalize())
                viewing = "{}/evv/{}/index.html".format(urlroot, case_name)
            else:
                viewing = (
                    "{}\n"
                    "    EVV viewing instructions can be found at: "
                    "        https://github.com/ESMCI/CIME/blob/master/scripts/"
                    "climate_reproducibility/README.md#test-passfail-and-extended-output"
                    "".format(evv_out_dir)
                )

            comments = (
                "{} {} for test '{}'.\n"
                "    {}\n"
                "    EVV results can be viewed at:\n"
                "        {}".format(
                    CIME.test_status.BASELINE_PHASE,
                    status,
                    test_name,
                    comments,
                    viewing,
                )
            )

            append_testlog(comments, self._orig_caseroot)

    def _generate_baseline(self):
        super(TSC, self)._generate_baseline()

        with CIME.utils.SharedArea():
            basegen_dir = os.path.join(
                self._case.get_value("BASELINE_ROOT"),
                self._case.get_value("BASEGEN_CASE"),
            )

            rundir = self._case.get_value("RUNDIR")
            ref_case = self._case.get_value("RUN_REFCASE")

            env_archive = self._case.get_env("archive")
            hists = env_archive.get_all_hist_files(
                self._case.get_value("CASE"),
                self.atmmod,
                rundir,
                r"DT\d*",
                ref_case=ref_case,
            )
            hists = [os.path.join(rundir, hist) for hist in hists]
            logger.debug("TSC additional baseline files: {}".format(hists))
            for hist in hists:
                basename = hist[hist.rfind(self.atmmod) :]
                baseline = os.path.join(basegen_dir, basename)
                if os.path.exists(baseline):
                    os.remove(baseline)

                CIME.utils.safe_copy(hist, baseline, preserve_meta=False)
