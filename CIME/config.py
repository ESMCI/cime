import sys
import glob
import logging
import importlib.machinery
import importlib.util

from CIME import utils

logger = logging.getLogger(__name__)


class Config:
    def __new__(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = super(Config, cls).__new__(cls)

        return cls._instance

    def __init__(self):
        if getattr(self, "_loaded", False):
            return

        self._attribute_config = {}

        self._set_attribute(
            "additional_archive_components",
            ("drv", "dart"),
            desc="Additional components to archive.",
        )
        self._set_attribute(
            "verbose_run_phase",
            False,
            desc="If set to `True` then after a SystemTests successful run phase the elapsed time is recorded to BASELINE_ROOT, on a failure the test is checked against the previous run and potential breaking merges are listed in the testlog.",
        )
        self._set_attribute(
            "baseline_store_teststatus",
            True,
            desc="If set to `True` and GENERATE_BASELINE is set then a teststatus.log is created in the case's baseline.",
        )
        self._set_attribute(
            "common_sharedlibroot",
            True,
            desc="If set to `True` then SHAREDLIBROOT is set for the case and SystemTests will only build the shared libs once.",
        )
        self._set_attribute(
            "create_test_flag_mode",
            "cesm",
            desc="Sets the flag mode for the `create_test` script. When set to `cesm`, the `-c` flag will compare baselines against a give directory.",
        )
        self._set_attribute(
            "use_kokkos",
            False,
            desc="If set to `True` and CAM_TARGET is `preqx_kokkos`, `theta-l` or `theta-l_kokkos` then kokkos is built with the shared libs.",
        )
        self._set_attribute(
            "shared_clm_component",
            True,
            desc="If set to `True` and then the `clm` land component is built as a shared lib.",
        )
        self._set_attribute(
            "ufs_alternative_config",
            False,
            desc="If set to `True` and UFS_DRIVER is set to `nems` then model config dir is set to `$CIMEROOT/../src/model/NEMS/cime/cime_config`.",
        )
        self._set_attribute(
            "enable_smp",
            True,
            desc="If set to `True` then `SMP=` is added to model compile command.",
        )
        self._set_attribute(
            "build_model_use_cmake",
            False,
            desc="If set to `True` the model is built using using CMake otherwise Make is used.",
        )
        self._set_attribute(
            "build_cime_component_lib",
            True,
            desc="If set to `True` then `Filepath`, `CIME_cppdefs` and `CCSM_cppdefs` directories are copied from CASEBUILD directory to BUILDROOT in order to build CIME's internal components.",
        )
        self._set_attribute(
            "default_short_term_archiving",
            True,
            desc="If set to `True` and the case is not a test then DOUT_S is set to True and TIMER_LEVEL is set to 4.",
        )
        # TODO combine copy_e3sm_tools and copy_cesm_tools into a single variable
        self._set_attribute(
            "copy_e3sm_tools",
            False,
            desc="If set to `True` then E3SM specific tools are copied into the case directory.",
        )
        self._set_attribute(
            "copy_cesm_tools",
            True,
            desc="If set to `True` then CESM specific tools are copied into the case directory.",
        )
        self._set_attribute(
            "copy_cism_source_mods",
            True,
            desc="If set to `True` then `$CASEROOT/SourceMods/src.cism/source_cism` is created and a README is written to directory.",
        )
        self._set_attribute(
            "make_case_run_batch_script",
            False,
            desc="If set to `True` and case is not a test then `case.run.sh` is created in case directory from `$MACHDIR/template.case.run.sh`.",
        )
        self._set_attribute(
            "case_setup_generate_namelist",
            False,
            desc="If set to `True` and case is a test then namelists are created during `case.setup`.",
        )
        self._set_attribute(
            "create_bless_log",
            False,
            desc="If set to `True` and comparing test to baselines the most recent bless is added to comments.",
        )
        self._set_attribute(
            "allow_unsupported",
            True,
            desc="If set to `True` then unsupported compsets and resolutions are allowed.",
        )
        # set for ufs
        self._set_attribute(
            "check_machine_name_from_test_name",
            True,
            desc="If set to `True` then the TestScheduler will use testlists to parse for a list of tests.",
        )
        self._set_attribute(
            "sort_tests",
            False,
            desc="If set to `True` then the TestScheduler will sort tests by runtime.",
        )
        self._set_attribute(
            "calculate_mode_build_cost",
            False,
            desc="If set to `True` then the TestScheduler will set the number of processors for building the model to min(16, (($GMAKE_J * 2) / 3) + 1) otherwise it's set to 4.",
        )
        self._set_attribute(
            "share_exes",
            False,
            desc="If set to `True` then the TestScheduler will share exes between tests.",
        )

        self._set_attribute(
            "serialize_sharedlib_builds",
            True,
            desc="If set to `True` then the TestScheduler will use `proc_pool + 1` processors to build shared libraries otherwise a single processor is used.",
        )

        self._set_attribute(
            "use_testreporter_template",
            True,
            desc="If set to `True` then the TestScheduler will create `testreporter` in $CIME_OUTPUT_ROOT.",
        )

        self._set_attribute(
            "check_invalid_args",
            True,
            desc="If set to `True` then script arguments are checked for being valid.",
        )
        self._set_attribute(
            "test_mode",
            "cesm",
            desc="Sets the testing mode, this changes various configuration for CIME's unit and system tests.",
        )
        self._set_attribute(
            "xml_component_key",
            "COMP_ROOT_DIR_{}",
            desc="The string template used as the key to query the XML system to find a components root directory e.g. the template `COMP_ROOT_DIR_{}` and component `LND` becomes `COMP_ROOT_DIR_LND`.",
        )
        self._set_attribute(
            "set_comp_root_dir_cpl",
            True,
            desc="If set to `True` then COMP_ROOT_DIR_CPL is set for the case.",
        )
        self._set_attribute(
            "use_nems_comp_root_dir",
            False,
            desc="If set to `True` then COMP_ROOT_DIR_CPL is set using UFS_DRIVER if defined.",
        )
        self._set_attribute(
            "test_custom_project_machine",
            "melvin",
            desc="Sets the machine name to use when testing a machine with no PROJECT.",
        )
        self._set_attribute(
            "driver_default", "nuopc", desc="Sets the default driver for the model."
        )
        self._set_attribute(
            "driver_choices",
            ("mct", "nuopc"),
            desc="Sets the available driver choices for the model.",
        )
        self._set_attribute(
            "mct_path",
            "{srcroot}/libraries/mct",
            desc="Sets the path to the mct library.",
        )

    @classmethod
    def instance(cls):
        """Access singleton.

        Explicit way to access singleton, same as calling constructor.
        """
        return cls()

    @classmethod
    def load(cls, customize_path):
        obj = cls()

        logger.debug("Searching %r for files to load", customize_path)

        customize_files = glob.glob(f"{customize_path}/**/*.py", recursive=True)

        # filter out any tests
        customize_files = [
            x for x in customize_files if "tests" not in x and "conftest" not in x
        ]

        customize_module_spec = importlib.machinery.ModuleSpec("cime_customize", None)

        customize_module = importlib.util.module_from_spec(customize_module_spec)

        sys.modules["CIME.customize"] = customize_module

        for x in sorted(customize_files):
            obj._load_file(x, customize_module)

        setattr(obj, "_loaded", True)

        return obj

    def _load_file(self, file_path, customize_module):
        logger.debug("Loading file %r", file_path)

        raw_config = utils.import_from_file("raw_config", file_path)

        # filter user define variables and functions
        user_defined = [x for x in dir(raw_config) if not x.endswith("__")]

        # set values on this object, will overwrite existing
        for x in user_defined:
            try:
                value = getattr(raw_config, x)
            except AttributeError:
                # should never hit this
                logger.fatal("Attribute %r missing on obejct", x)

                sys.exit(1)
            else:
                setattr(customize_module, x, value)

                self._set_attribute(x, value)

    def _set_attribute(self, name, value, desc=None):
        if hasattr(self, name):
            logger.debug("Overwriting %r attribute", name)

        logger.debug("Setting attribute %r with value %r", name, value)

        setattr(self, name, value)

        self._attribute_config[name] = {
            "desc": desc,
            "default": value,
        }

    def print_rst_table(self):
        max_variable = max([len(x) for x in self._attribute_config.keys()])
        max_default = max(
            [len(str(x["default"])) for x in self._attribute_config.values()]
        )
        max_type = max(
            [len(type(x["default"]).__name__) for x in self._attribute_config.values()]
        )
        max_desc = max([len(x["desc"]) for x in self._attribute_config.values()])

        divider_row = (
            f"{'='*max_variable}  {'='*max_default}  {'='*max_type}  {'='*max_desc}"
        )

        rows = [
            divider_row,
            f"Variable{' '*(max_variable-8)}  Default{' '*(max_default-7)}  Type{' '*(max_type-4)}  Description{' '*(max_desc-11)}",
            divider_row,
        ]

        for variable, value in sorted(
            self._attribute_config.items(), key=lambda x: x[0]
        ):
            variable_fill = max_variable - len(variable)
            default_fill = max_default - len(str(value["default"]))
            type_fill = max_type - len(type(value["default"]).__name__)

            rows.append(
                f"{variable}{' '*variable_fill}  {value['default']}{' '*default_fill}  {type(value['default']).__name__}{' '*type_fill}  {value['desc']}"
            )

        rows.append(divider_row)

        print("\n".join(rows))
