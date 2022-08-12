import sys
import glob
import logging
import importlib

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
            desc="Additional components to archive."
        )
        self._set_attribute(
            "verbose_run_phase",
            False,
            desc="Upon a successful SystemTest, the time taken is recorded to the BASELINE_ROOT. If the RUN phase failed then a possible explanation is appened to the testlog.",
        )
        self._set_attribute(
            "baseline_store_teststatus",
            True,
            desc="Upon the completion of a SystemTest and GENERATE_BASELINE is True, the TestStatus will be copied from the case directory to the baseline directory.",
        )
        self._set_attribute(
            "common_sharedlibroot",
            True,
            desc="During BUILD phase of a SystemTestsCompareN SHAREDLIBROOT is set the same for all cases.",
        )
        self._set_attribute(
            "create_test_flag_mode",
            "cesm",
            desc="Sets model specific flags for 'create_test' script.",
        )
        self._set_attribute(
            "use_kokkos",
            False,
            desc="Enables use of kokkos, CAM_TARGET must be set to either `preqx_kokkos`, `theta-l` or `theta-l_kokkos`.",
        )
        self._set_attribute(
            "shared_clm_component", True, desc="Enables shared clm component."
        )
        self._set_attribute(
            "ufs_alternative_config",
            False,
            desc="Enables ufs config_dir for `nems` driver.",
        )
        # disable for ufs
        self._set_attribute("enable_smp", True, desc="Enables SMP when building model.")
        self._set_attribute(
            "build_model_use_cmake", False, desc="When building model use CMake."
        )
        self._set_attribute(
            "build_cime_component_lib", True, desc="Build CIME component lib."
        )
        self._set_attribute(
            "default_short_term_archiving",
            True,
            desc="Forces short term archiving when not a test.",
        )
        self._set_attribute(
            "copy_e3sm_tools", False, desc="Copies E3SM specific tools to case tools."
        )
        self._set_attribute(
            "copy_cesm_tools", True, desc="Copies archive_metadata to case root."
        )
        self._set_attribute(
            "copy_cism_source_mods", True, desc="Copies cism SourceMods."
        )
        self._set_attribute(
            "make_case_run_batch_script",
            False,
            desc="Makes case.run batch script during case setup.",
        )
        self._set_attribute(
            "case_setup_generate_namelist",
            False,
            desc="Creates namelist during case.setup for some tests.",
        )
        self._set_attribute(
            "create_bless_log",
            False,
            desc="Creates a bless log when comparing baseline.",
        )
        self._set_attribute(
            "allow_unsupported",
            True,
            desc="Allows creation of case that is not test or supported.",
        )
        # set for ufs
        self._set_attribute(
            "check_machine_name_from_test_name",
            True,
            desc="Try to get machine name from testname.",
        )
        self._set_attribute(
            "sort_tests",
            False,
            desc="When creating a test if walltime is defined tests are sorted by execution time",
        )
        self._set_attribute(
            "calculate_mode_build_cost",
            False,
            desc="Calculates model build cost rather than using static value in test_scheduler",
        )
        self._set_attribute(
            "share_exes", False, desc="Test scheduler will shared exes."
        )

        self._set_attribute(
            "serialize_sharedlib_builds",
            True,
            desc="Test scheduler will serialize sharedlib builds.",
        )

        self._set_attribute(
            "use_testreporter_template",
            True,
            desc="Test scheduler will use testreporter.template.",
        )

        self._set_attribute(
            "check_invalid_args",
            True,
            desc="Validates arguments when parsing for CIME commands.",
        )
        self._set_attribute(
            "test_mode",
            "cesm",
            desc="Sets the testing mode.",
        )
        self._set_attribute(
            "xml_component_key",
            "COMP_ROOT_DIR_{}",
            desc="Component key used whenm querying config.",
        )
        self._set_attribute(
            "set_comp_root_dir_cpl",
            True,
            desc="Sets COMP_ROOT_DIR_CPL when setting compset.",
        )
        self._set_attribute(
            "use_nems_comp_root_dir",
            False,
            desc="Use nems specific value for COMP_ROOT_DIR_CPL.",
        )
        self._set_attribute(
            "gpus_use_set_device_rank",
            True,
            desc="Uses set_device_rank.sh from RUNDIR when composing MPI run command.",
        )
        self._set_attribute(
            "test_custom_project_machine",
            "melvin",
            desc="Set a machine which doesn't use PROJECT for testing.",
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
            desc="Path to the mct library.",
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
