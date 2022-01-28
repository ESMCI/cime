"""
Multivariate test for climate reproducibility using the Kolmogrov-Smirnov (K-S)
test and based on The CESM/E3SM model's multi-instance capability is used to
conduct an ensemble of simulations starting from different initial conditions.

This class inherits from SystemTestsCommon.
"""

import os
import json
import logging
import xml.etree.ElementTree as ET

from distutils import dir_util

import numpy as np
import netCDF4 as nc

import CIME.test_status
import CIME.utils
from CIME.SystemTests.system_tests_common import SystemTestsCommon
from CIME.case.case_setup import case_setup
from CIME.XML.machines import Machines


import evv4esm  # pylint: disable=import-error
from evv4esm.__main__ import main as evv  # pylint: disable=import-error

evv_lib_dir = os.path.abspath(os.path.dirname(evv4esm.__file__))
logger = logging.getLogger(__name__)
NINST = 30

# INIT_FILE_ROOT = "/global/cscratch1/sd/salil/initial_conditions"
INIT_FILE_ROOT = "/lcrc/group/e3sm/ac.mkelleher/scratch/initial_conditions"
INIT_FILE_NAME = f"{INIT_FILE_ROOT}/inic_oQU240_from_GMPAS_mpaso.rst.0050-01-01_00000.nc"
PERT_FILE_TEMPLATE = "mpaso_oQ240_perturbed_inic_{ens:04d}.nc"

CLIMO_STREAM = \
"""
<stream name="timeSeriesStatsClimatologyOutput"
    type="output"
    precision="single"
    io_type="pnetcdf"
    filename_template="{case}.mpaso_{inst}.hist.am.timeSeriesStatsClimatology.$Y-$M-$D.nc"
    filename_interval="00-00-00_00:00:00"
    reference_time="00-01-01_00:00:00"
    output_interval="00-00-00_00:00:00"
    clobber_mode="truncate"
    packages="timeSeriesStatsClimatologyAMPKG"
    runtime_format="single_file">

    <var name="daysSinceStartOfSim" />
    <var name="ssh" />
    <var name="velocityZonal" />
    <var name="velocityMeridional" />
    <var name="activeTracers" />
</stream>\n
"""

def perturb_init(infile, field_name, outfile, seed=None):
    """
    Create perturbed initial conditions file from another netCDF using random uniform.

    Parameters
    ----------
    infile : string
        Path to initial conditions input file which will be perturbed
    field_name : string
        Variable name in netCDF file to perturb
    outfile : string
        Path to output file
    seed : int
        Integer seed for the random number generator (optional)

    """

    init_f = nc.Dataset(infile, "r")
    field_temp = init_f.variables[field_name]

    # Initialize numpy random generator with a seed
    rng = np.random.default_rng(seed)

    # Perturbation between -1e-14 -- +1e-14, same size as the input field
    perturbation = rng.uniform(-1e-14, 1e-14, field_temp[:].shape)
    field = field_temp[:] + perturbation

    os.system(f"cp {infile} {outfile}")
    with nc.Dataset(outfile, "a") as out_f:

        field_out = out_f.variables[field_name]
        field_out[:] = field

    init_f.close()


class MVKO(SystemTestsCommon):

    def __init__(self, case):
        """
        initialize an object interface to the MVKO test
        """
        SystemTestsCommon.__init__(self, case)

        if self._case.get_value("MODEL") == "e3sm":
            self.component = "mpaso"
        else:
            self.component = "pop"

        if self._case.get_value("RESUBMIT") == 0 \
                and self._case.get_value("GENERATE_BASELINE") is False:
            self._case.set_value("COMPARE_BASELINE", True)
        else:
            self._case.set_value("COMPARE_BASELINE", False)

    def build_phase(self, sharedlib_only=False, model_only=False):
        # Only want this to happen once. It will impact the sharedlib build
        # so it has to happen there.
        caseroot = self._case.get_value("CASEROOT")
        if not model_only:
            logging.warning('Starting to build multi-instance exe')
            for comp in self._case.get_values("COMP_CLASSES"):
                self._case.set_value('NTHRDS_{}'.format(comp), 1)

                ntasks = self._case.get_value("NTASKS_{}".format(comp))

                self._case.set_value('NTASKS_{}'.format(comp), ntasks * NINST)
                if comp != 'CPL':
                    self._case.set_value('NINST_{}'.format(comp), NINST)

            self._case.flush()

            case_setup(self._case, test_mode=False, reset=True)
        rundir = self._case.get_value("RUNDIR")

        clim_vars = ["daysSinceStartOfSim", "ssh", "velocityZonal", "velocityMeridional", "activeTracers"]
        clim_var_elements = [ET.Element("var", {"name": _var}) for _var in clim_vars]

        for iinst in range(1, NINST + 1):
            pert_file_name = PERT_FILE_TEMPLATE.format(ens=iinst)
            pert_file = os.path.join(rundir, pert_file_name)
            if not os.path.exists(rundir):
                logging.warning(f'CREATE {rundir}')
                os.mkdir(rundir)
            perturb_init(INIT_FILE_NAME, field_name="temperature", outfile=pert_file)

            # Write yearly averages to custom output file
            with open('user_nl_{}_{:04d}'.format(self.component, iinst), 'w') as nl_ocn_file:
                nl_ocn_file.write("config_am_timeseriesstatsclimatology_enable = .true.\n")
                nl_ocn_file.write("config_am_timeseriesstatsclimatology_backward_output_offset = '00-03-00_00:00:00'\n")
                nl_ocn_file.write("config_am_timeseriesstatsclimatology_compute_interval = '00-00-00_01:00:00'\n")
                nl_ocn_file.write("config_am_timeseriesstatsclimatology_compute_on_startup = .false.\n")
                nl_ocn_file.write("config_am_timeseriesstatsclimatology_duration_intervals = '00-03-00_00:00:00;00-03-00_00:00:00;00-03-00_00:00:00;00-03-00_00:00:00;01-00-00_00:00'\n")
                nl_ocn_file.write("config_am_timeseriesstatsclimatology_operation = 'avg'\n")
                nl_ocn_file.write("config_am_timeseriesstatsclimatology_output_stream = 'timeSeriesStatsClimatologyOutput'\n")
                nl_ocn_file.write("config_am_timeseriesstatsclimatology_reference_times = '00-03-01_00:00:00;00-06-01_00:00:00;00-09-01_00:00:00;00-12-01_00:00:00;00-12-01_00:00:00'\n")
                nl_ocn_file.write("config_am_timeseriesstatsclimatology_repeat_intervals = '01-00-00_00:00:00;01-00-00_00:00:00;01-00-00_00:00:00;01-00-00_00:00:00;01-00-00_00:00:00'\n")
                nl_ocn_file.write("config_am_timeseriesstatsclimatology_reset_intervals = '0001-00-00_00:00:00;0001-00-00_00:00:00;0001-00-00_00:00:00;0001-00-00_00:00:00;0001-00-00_00:00:00'\n")
                nl_ocn_file.write("config_am_timeseriesstatsclimatology_restart_stream = 'timeSeriesStatsClimatologyRestart'\n")
                nl_ocn_file.write("config_am_timeseriesstatsclimatology_write_on_startup = .false.\n")

                # nl_ocn_file.write("config_am_timeseriesstatsclimatology_duration_intervals = '00-03-00_00:00:00;00-03-00_00:00:00;00-03-00_00:00:00;00-03-00_00:00:00;01-00-00_00:00'\n")
                # nl_ocn_file.write("config_am_timeseriesstatsclimatology_reference_times = '00-03-01_00:00:00;00-06-01_00:00:00;00-09-01_00:00:00;00-12-01_00:00:00;00-01-00_00:00'\n")
                # nl_ocn_file.write("config_am_timeseriesstatsclimatology_repeat_intervals = '01-00-00_00:00:00;01-00-00_00:00:00;01-00-00_00:00:00;01-00-00_00:00:00;01-00-00_00:00'\n")
                # nl_ocn_file.write("config_am_timeseriesstatsclimatology_reset_intervals = '01-00-00_00:00:00;01-00-00_00:00:00;01-00-00_00:00:00;01-00-00_00:00:00;01-00-00_00:00:00'\n")

                # Disable output we don't use for this test
                nl_ocn_file.write("config_am_highfrequencyoutput_enable = .false.\n")
                nl_ocn_file.write("config_am_timeseriesstatsmonthlymax_enable = .false.\n")
                nl_ocn_file.write("config_am_timeseriesstatsmonthlymin_enable = .false.\n")

            # Set up streams file to get perturbed init file and do yearly climatology
            stream_file = os.path.join(caseroot, "SourceMods", "src.mpaso", "streams.ocean_{:04d}".format(iinst))
            os.system("cp {}/streams.ocean_{:04d} {}".format(rundir, iinst, stream_file))

            streams = ET.parse(stream_file)
            input_stream = list(
                filter(
                    lambda x: x.get("name") == "input", streams.getroot().findall("immutable_stream")
                )
            )
            input_stream[0].set("filename_template", pert_file)

            clim_stream = list(
                filter(
                    lambda x: x.get("name") == "timeSeriesStatsClimatologyOutput", streams.getroot().findall("stream")
                )
            )
            clim_stream = clim_stream[0]

            for clim_element in clim_var_elements:
                clim_stream.append(clim_element)
            # clim_stream.set("filename_interval", "01-00-00_00:00:00")
            # clim_stream.set("output_interval", "01-00-00_00:00:00")
            streams.write(stream_file)

        self.build_indv(sharedlib_only=sharedlib_only, model_only=model_only)


    def run_phase(self):
        # rundir = self._case.get_value("RUNDIR")
        self.run_indv()

    def _generate_baseline(self):
        """
        generate a new baseline case based on the current test
        """
        super(MVKO, self)._generate_baseline()

        with CIME.utils.SharedArea():
            basegen_dir = os.path.join(self._case.get_value("BASELINE_ROOT"),
                                       self._case.get_value("BASEGEN_CASE"))

            rundir = self._case.get_value("RUNDIR")
            ref_case = self._case.get_value("RUN_REFCASE")

            env_archive = self._case.get_env("archive")
            hists = env_archive.get_all_hist_files(self._case.get_value("CASE"), self.component, rundir, ref_case=ref_case)
            logger.debug("MVKO additional baseline files: {}".format(hists))
            hists = [os.path.join(rundir,hist) for hist in hists]
            for hist in hists:
                basename = hist[hist.rfind(self.component):]
                baseline = os.path.join(basegen_dir, basename)
                if os.path.exists(baseline):
                    os.remove(baseline)

                CIME.utils.safe_copy(hist, baseline, preserve_meta=False)

    def _compare_baseline(self):
        with self._test_status:
            if int(self._case.get_value("RESUBMIT")) > 0:
                # This is here because the comparison is run for each submission
                # and we only want to compare once the whole run is finished. We
                # need to return a pass here to continue the submission process.
                self._test_status.set_status(CIME.test_status.BASELINE_PHASE,
                                             CIME.test_status.TEST_PEND_STATUS)
                return

            self._test_status.set_status(CIME.test_status.BASELINE_PHASE,
                                         CIME.test_status.TEST_FAIL_STATUS)

            run_dir = self._case.get_value("RUNDIR")
            case_name = self._case.get_value("CASE")
            base_dir = os.path.join(self._case.get_value("BASELINE_ROOT"),
                                    self._case.get_value("BASECMP_CASE"))

            test_name = "{}".format(case_name.split('.')[-1])
            evv_config = {
                test_name: {
                    "module": os.path.join(evv_lib_dir, "extensions", "ks.py"),
                    "test-case": "Test",
                    "test-dir": run_dir,
                    "ref-case": "Baseline",
                    "ref-dir": base_dir,
                    "var-set": "default",
                    "ninst": NINST,
                    "critical": 13,
                    "component": self.component,
                }
            }

            json_file = os.path.join(run_dir, '.'.join([case_name, 'json']))
            with open(json_file, 'w') as config_file:
                json.dump(evv_config, config_file, indent=4)

            evv_out_dir = os.path.join(run_dir, '.'.join([case_name, 'evv']))
            evv(['-e', json_file, '-o', evv_out_dir])

            with open(os.path.join(evv_out_dir, 'index.json')) as evv_f:
                evv_status = json.load(evv_f)

            comments = ""
            for evv_elem in evv_status['Data']['Elements']:
                if evv_elem['Type'] == 'ValSummary' \
                        and evv_elem['TableTitle'] == 'Kolmogorov-Smirnov test':
                    comments = "; ".join("{}: {}".format(key, val) for key, val
                                         in evv_elem['Data'][test_name][''].items())
                    if evv_elem['Data'][test_name]['']['Test status'].lower() == 'pass':
                        self._test_status.set_status(CIME.test_status.BASELINE_PHASE,
                                                     CIME.test_status.TEST_PASS_STATUS)
                    break

            status = self._test_status.get_status(CIME.test_status.BASELINE_PHASE)
            mach_name = self._case.get_value("MACH")
            mach_obj = Machines(machine=mach_name)
            htmlroot = CIME.utils.get_htmlroot(mach_obj)
            urlroot = CIME.utils.get_urlroot(mach_obj)
            if htmlroot is not None:
                with CIME.utils.SharedArea():
                    dir_util.copy_tree(evv_out_dir, os.path.join(htmlroot, 'evv', case_name), preserve_mode=False)
                if urlroot is None:
                    urlroot = "[{}_URL]".format(mach_name.capitalize())
                viewing = "{}/evv/{}/index.html".format(urlroot, case_name)
            else:
                viewing = "{}\n" \
                            "    EVV viewing instructions can be found at: " \
                            "        https://github.com/E3SM-Project/E3SM/blob/master/cime/scripts/" \
                            "climate_reproducibility/README.md#test-passfail-and-extended-output" \
                            "".format(evv_out_dir)

            comments = "{} {} for test '{}'.\n" \
                        "    {}\n" \
                        "    EVV results can be viewed at:\n" \
                        "        {}".format(CIME.test_status.BASELINE_PHASE, status, test_name, comments, viewing)

            CIME.utils.append_testlog(comments, self._orig_caseroot)
