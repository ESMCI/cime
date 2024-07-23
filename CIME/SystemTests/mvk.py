"""
Multivariate test for climate reproducibility using the Kolmogrov-Smirnov (K-S)
test and based on The CESM/E3SM model's multi-instance capability is used to
conduct an ensemble of simulations starting from different initial conditions.

This class inherits from SystemTestsCommon.
"""

import os
import json
import logging
from distutils import dir_util

from CIME import test_status
from CIME import utils
from CIME.SystemTests.system_tests_common import SystemTestsCommon
from CIME.case.case_setup import case_setup
from CIME.XML.machines import Machines
from CIME.config import ConfigBase
from CIME.SystemTests import test_mods

import evv4esm  # pylint: disable=import-error
from evv4esm.__main__ import main as evv  # pylint: disable=import-error

version = evv4esm.__version_info__

assert version[0] <= 0 and version[1] <= 5, "Please install evv4esm less than 0.5.x"

EVV_LIB_DIR = os.path.abspath(os.path.dirname(evv4esm.__file__))

logger = logging.getLogger(__name__)


class MVKConfig(ConfigBase):
    def __init__(self):
        super().__init__()

        if self.loaded:
            return

        self._set_attribute("component", "", "The main component.")
        self._set_attribute(
            "components", [], "Components that require namelist customization."
        )
        self._set_attribute("ninst", 30, "The number of instances.")
        self._set_attribute(
            "var_set", "default", "Name of the variable set to analyze."
        )
        self._set_attribute("ref_case", "Baseline", "Name of the reference case.")
        self._set_attribute("test_case", "Test", "Name of the test case.")

    def write_inst_nml(
        self, case, set_nml_variable, component, iinst
    ):  # pylint: disable=unused-argument
        """Write per instance namelist.

        This method is called once per instance to generate the namelist.

        Args:
            case (CIME.case.case.Case): The case instance.
            write_nml_variable (function): Function takes two `str` arguments.
            component (str): Component the namelist belongs to.
            iinst (int): Instance unique number.
        """
        set_nml_variable("new_random", ".true.")
        set_nml_variable("pertlim", "1.0e-10")
        set_nml_variable("seed_custom", f"{iinst}")
        set_nml_variable("seed_clock", ".true.")

    def test_config(
        self, case, run_dir, base_dir, evv_lib_dir
    ):  # pylint: disable=unused-argument
        """Configure the evv test.

        This method is used to pass the evv4esm configuration to be written for the test.

        Args:
            case (CIME.case.case.Case): The case instance.
            run_dir (str): Path the case's run directory.
            base_dir (str): Path to the case's baseline directory.
            evv_lib_dir (str): Path to the evv4esm package root.

        Returns:
            dict: Dictionary with test configuration.
        """
        config = {
            "module": os.path.join(evv_lib_dir, "extensions", "ks.py"),
            "test-case": self.test_case,
            "test-dir": run_dir,
            "ref-case": self.ref_case,
            "ref-dir": base_dir,
            "var-set": self.var_set,
            "ninst": self.ninst,
            "component": self.component,
        }

        return config


class MVK(SystemTestsCommon):
    def __init__(self, case, **kwargs):
        """
        initialize an object interface to the MVK test
        """
        self._config = None

        SystemTestsCommon.__init__(self, case, **kwargs)

        *_, case_test_mods = utils.parse_test_name(self._casebaseid)

        test_mods_paths = test_mods.find_test_mods(
            case.get_value("COMP_INTERFACE"), case_test_mods
        )

        for test_mods_path in test_mods_paths:
            self._config = MVKConfig.load(os.path.join(test_mods_path, "params.py"))

        if self._config is None:
            self._config = MVKConfig()

        # Use old behavior for component
        if self._config.component == "":
            # TODO remove model specific
            if self._case.get_value("MODEL") == "e3sm":
                self._config.component = "eam"
            else:
                self._config.component = "cam"

        if len(self._config.components) == 0:
            self._config.components = [self._config.component]

        if (
            self._case.get_value("RESUBMIT") == 0
            and self._case.get_value("GENERATE_BASELINE") is False
        ):
            self._case.set_value("COMPARE_BASELINE", True)
        else:
            self._case.set_value("COMPARE_BASELINE", False)

    def build_phase(self, sharedlib_only=False, model_only=False):
        # Only want this to happen once. It will impact the sharedlib build
        # so it has to happen there.
        if not model_only:
            logging.warning("Starting to build multi-instance exe")

            for comp in self._case.get_values("COMP_CLASSES"):
                self._case.set_value("NTHRDS_{}".format(comp), 1)

                ntasks = self._case.get_value("NTASKS_{}".format(comp))

                self._case.set_value(
                    "NTASKS_{}".format(comp), ntasks * self._config.ninst
                )

                if comp != "CPL":
                    self._case.set_value("NINST_{}".format(comp), self._config.ninst)

            self._case.flush()

            case_setup(self._case, test_mode=False, reset=True)

        for iinst in range(1, self._config.ninst + 1):
            for component in self._config.components:
                with open(
                    "user_nl_{}_{:04d}".format(component, iinst), "w"
                ) as nml_file:
                    set_nml_variable = lambda key, value: nml_file.write(  # pylint: disable=cell-var-from-loop
                        f"{key} = {value}\n"
                    )

                    self._config.write_inst_nml(
                        self._case, set_nml_variable, component, iinst
                    )

        self.build_indv(sharedlib_only=sharedlib_only, model_only=model_only)

    def _generate_baseline(self):
        """
        generate a new baseline case based on the current test
        """
        super(MVK, self)._generate_baseline()

        with utils.SharedArea():
            basegen_dir = os.path.join(
                self._case.get_value("BASELINE_ROOT"),
                self._case.get_value("BASEGEN_CASE"),
            )

            rundir = self._case.get_value("RUNDIR")
            ref_case = self._case.get_value("RUN_REFCASE")

            env_archive = self._case.get_env("archive")
            hists = env_archive.get_all_hist_files(
                self._case.get_value("CASE"),
                self._config.component,
                rundir,
                ref_case=ref_case,
            )
            logger.debug("MVK additional baseline files: {}".format(hists))
            hists = [os.path.join(rundir, hist) for hist in hists]
            for hist in hists:
                basename = hist[hist.rfind(self._config.component) :]
                baseline = os.path.join(basegen_dir, basename)
                if os.path.exists(baseline):
                    os.remove(baseline)

                utils.safe_copy(hist, baseline, preserve_meta=False)

    def _compare_baseline(self):
        with self._test_status:
            if int(self._case.get_value("RESUBMIT")) > 0:
                # This is here because the comparison is run for each submission
                # and we only want to compare once the whole run is finished. We
                # need to return a pass here to continue the submission process.
                self._test_status.set_status(
                    test_status.BASELINE_PHASE, test_status.TEST_PASS_STATUS
                )
                return

            self._test_status.set_status(
                test_status.BASELINE_PHASE, test_status.TEST_FAIL_STATUS
            )

            run_dir = self._case.get_value("RUNDIR")
            case_name = self._case.get_value("CASE")
            base_dir = os.path.join(
                self._case.get_value("BASELINE_ROOT"),
                self._case.get_value("BASECMP_CASE"),
            )

            test_name = "{}".format(case_name.split(".")[-1])

            test_config = self._config.test_config(
                self._case, run_dir, base_dir, EVV_LIB_DIR
            )

            evv_config = {test_name: test_config}

            json_file = os.path.join(run_dir, f"{case_name}.json")
            with open(json_file, "w") as config_file:
                json.dump(evv_config, config_file, indent=4)

            evv_out_dir = os.path.join(run_dir, f"{case_name}.evv")
            evv(["-e", json_file, "-o", evv_out_dir])

            self.update_testlog(test_name, case_name, evv_out_dir)

    def update_testlog(self, test_name, case_name, evv_out_dir):
        comments = self.process_evv_output(evv_out_dir)

        status = self._test_status.get_status(test_status.BASELINE_PHASE)

        mach_name = self._case.get_value("MACH")

        mach_obj = Machines(machine=mach_name)

        htmlroot = utils.get_htmlroot(mach_obj)

        if htmlroot is not None:
            urlroot = utils.get_urlroot(mach_obj)

            with utils.SharedArea():
                dir_util.copy_tree(
                    evv_out_dir,
                    os.path.join(htmlroot, "evv", case_name),
                    preserve_mode=False,
                )

            if urlroot is None:
                urlroot = "[{}_URL]".format(mach_name.capitalize())

            viewing = "{}/evv/{}/index.html".format(urlroot, case_name)
        else:
            viewing = (
                "{}\n"
                "    EVV viewing instructions can be found at: "
                "        https://github.com/E3SM-Project/E3SM/blob/master/cime/scripts/"
                "climate_reproducibility/README.md#test-passfail-and-extended-output"
                "".format(evv_out_dir)
            )

        comments = (
            "{} {} for test '{}'.\n"
            "    {}\n"
            "    EVV results can be viewed at:\n"
            "        {}".format(
                test_status.BASELINE_PHASE,
                status,
                test_name,
                comments,
                viewing,
            )
        )

        utils.append_testlog(comments, self._orig_caseroot)

    def process_evv_output(self, evv_out_dir):
        with open(os.path.join(evv_out_dir, "index.json")) as evv_f:
            evv_status = json.load(evv_f)

        comments = ""

        for evv_ele in evv_status["Page"]["elements"]:
            if "Table" in evv_ele:
                comments = "; ".join(
                    "{}: {}".format(key, val[0])
                    for key, val in evv_ele["Table"]["data"].items()
                )

                if evv_ele["Table"]["data"]["Test status"][0].lower() == "pass":
                    with self._test_status:
                        self._test_status.set_status(
                            test_status.BASELINE_PHASE,
                            test_status.TEST_PASS_STATUS,
                        )

                break

        return comments
