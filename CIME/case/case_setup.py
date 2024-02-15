"""
Library for case.setup.
case_setup is a member of class Case from file case.py
"""

import os

from CIME.XML.standard_module_setup import *
from CIME.config import Config
from CIME.XML.machines import Machines
from CIME.BuildTools.configure import (
    generate_env_mach_specific,
    copy_depends_files,
)
from CIME.utils import (
    run_and_log_case_status,
    get_batch_script_for_job,
    safe_copy,
    file_contains_python_function,
    import_from_file,
    copy_local_macros_to_dir,
)
from CIME.utils import batch_jobid
from CIME.test_status import *
from CIME.locked_files import unlock_file, lock_file

import errno, shutil

logger = logging.getLogger(__name__)


###############################################################################
def _build_usernl_files(case, model, comp):
    ###############################################################################
    """
    Create user_nl_xxx files, expects cwd is caseroot
    """
    model = model.upper()
    if model == "DRV":
        model_file = case.get_value("CONFIG_CPL_FILE")
    else:
        model_file = case.get_value("CONFIG_{}_FILE".format(model))
    expect(
        model_file is not None,
        "Could not locate CONFIG_{}_FILE in config_files.xml".format(model),
    )
    model_dir = os.path.dirname(model_file)

    expect(
        os.path.isdir(model_dir),
        "cannot find cime_config directory {} for component {}".format(model_dir, comp),
    )
    comp_interface = case.get_value("COMP_INTERFACE")
    multi_driver = case.get_value("MULTI_DRIVER")
    ninst = 1

    if multi_driver:
        ninst_max = case.get_value("NINST_MAX")
        if comp_interface != "nuopc" and model not in ("DRV", "CPL", "ESP"):
            ninst_model = case.get_value("NINST_{}".format(model))
            expect(
                ninst_model == ninst_max,
                "MULTI_DRIVER mode, all components must have same NINST value.  NINST_{} != {}".format(
                    model, ninst_max
                ),
            )
    if comp == "cpl":
        if not os.path.exists("user_nl_cpl"):
            safe_copy(os.path.join(model_dir, "user_nl_cpl"), ".")
    else:
        if comp_interface == "nuopc":
            ninst = case.get_value("NINST")
        elif ninst == 1:
            ninst = case.get_value("NINST_{}".format(model))
        default_nlfile = "user_nl_{}".format(comp)
        model_nl = os.path.join(model_dir, default_nlfile)
        user_nl_list = _get_user_nl_list(case, default_nlfile, model_dir)

        # Note that, even if there are multiple elements of user_nl_list (i.e., we are
        # creating multiple user_nl files for this component with different names), all of
        # them will start out as copies of the single user_nl_comp file in the model's
        # source tree - unless the file has _stream in its name
        for nlfile in user_nl_list:
            if ninst > 1:
                for inst_counter in range(1, ninst + 1):
                    inst_nlfile = "{}_{:04d}".format(nlfile, inst_counter)
                    if not os.path.exists(inst_nlfile):
                        # If there is a user_nl_foo in the case directory, copy it
                        # to user_nl_foo_INST; otherwise, copy the original
                        # user_nl_foo from model_dir
                        if os.path.exists(nlfile):
                            safe_copy(nlfile, inst_nlfile)
                        elif "_stream" in nlfile:
                            safe_copy(os.path.join(model_dir, nlfile), inst_nlfile)
                        elif os.path.exists(model_nl):
                            safe_copy(model_nl, inst_nlfile)
            else:
                # ninst = 1
                if not os.path.exists(nlfile):
                    if "_stream" in nlfile:
                        safe_copy(os.path.join(model_dir, nlfile), nlfile)
                    elif os.path.exists(model_nl):
                        safe_copy(model_nl, nlfile)


###############################################################################
def _get_user_nl_list(case, default_nlfile, model_dir):
    """Get a list of user_nl files needed by this component

    Typically, each component has a single user_nl file: user_nl_comp. However, some
    components use multiple user_nl files. These components can define a function in
    cime_config/buildnml named get_user_nl_list, which returns a list of user_nl files
    that need to be staged in the case directory. For example, in a run where CISM is
    modeling both Antarctica and Greenland, its get_user_nl_list function will return
    ['user_nl_cism', 'user_nl_cism_ais', 'user_nl_cism_gris'].

    If that function is NOT defined in the component's buildnml, then we return the given
    default_nlfile.

    """
    # Check if buildnml is present in the expected location, and if so, whether it
    # contains the function "get_user_nl_list"; if so, we'll import the module and call
    # that function; if not, we'll fall back on the default value.
    buildnml_path = os.path.join(model_dir, "buildnml")
    has_function = False
    if os.path.isfile(buildnml_path) and file_contains_python_function(
        buildnml_path, "get_user_nl_list"
    ):
        has_function = True

    if has_function:
        comp_buildnml = import_from_file("comp_buildnml", buildnml_path)
        return comp_buildnml.get_user_nl_list(case)
    else:
        return [default_nlfile]


###############################################################################
def _create_macros_cmake(
    caseroot, cmake_macros_dir, mach_obj, compiler, case_cmake_path
):
    ###############################################################################
    if not os.path.isfile(os.path.join(caseroot, "Macros.cmake")):
        safe_copy(os.path.join(cmake_macros_dir, "Macros.cmake"), caseroot)

    if not os.path.exists(case_cmake_path):
        os.mkdir(case_cmake_path)

    # This impl is coupled to contents of Macros.cmake
    os_ = mach_obj.get_value("OS")
    mach = mach_obj.get_machine_name()
    macros = [
        "universal.cmake",
        os_ + ".cmake",
        compiler + ".cmake",
        "{}_{}.cmake".format(compiler, os),
        mach + ".cmake",
        "{}_{}.cmake".format(compiler, mach),
        "CMakeLists.txt",
    ]
    for macro in macros:
        repo_macro = os.path.join(cmake_macros_dir, macro)
        case_macro = os.path.join(case_cmake_path, macro)
        if not os.path.exists(case_macro) and os.path.exists(repo_macro):
            safe_copy(repo_macro, case_cmake_path)

    copy_depends_files(mach, mach_obj.machines_dir, caseroot, compiler)


###############################################################################
def _create_macros(
    case, mach_obj, caseroot, compiler, mpilib, debug, comp_interface, sysos
):
    ###############################################################################
    """
    creates the Macros.make, Depends.compiler, Depends.machine, Depends.machine.compiler
    and env_mach_specific.xml if they don't already exist.
    """
    reread = not os.path.isfile("env_mach_specific.xml")
    new_cmake_macros_dir = case.get_value("CMAKE_MACROS_DIR")

    if reread:
        case.flush()
        generate_env_mach_specific(
            caseroot,
            mach_obj,
            compiler,
            mpilib,
            debug,
            comp_interface,
            sysos,
            False,
            threaded=case.get_build_threaded(),
            noenv=True,
        )
        case.read_xml()

    case_cmake_path = os.path.join(caseroot, "cmake_macros")

    _create_macros_cmake(
        caseroot, new_cmake_macros_dir, mach_obj, compiler, case_cmake_path
    )
    copy_local_macros_to_dir(
        case_cmake_path, extra_machdir=case.get_value("EXTRA_MACHDIR")
    )


###############################################################################
def _case_setup_impl(
    case, caseroot, clean=False, test_mode=False, reset=False, keep=None
):
    ###############################################################################
    os.chdir(caseroot)

    non_local = case.get_value("NONLOCAL")

    models = case.get_values("COMP_CLASSES")
    mach = case.get_value("MACH")
    compiler = case.get_value("COMPILER")
    debug = case.get_value("DEBUG")
    mpilib = case.get_value("MPILIB")
    sysos = case.get_value("OS")
    comp_interface = case.get_value("COMP_INTERFACE")
    extra_machines_dir = case.get_value("EXTRA_MACHDIR")

    expect(mach is not None, "xml variable MACH is not set")

    mach_obj = Machines(machine=mach, extra_machines_dir=extra_machines_dir)

    # Check that $DIN_LOC_ROOT exists or can be created:
    if not non_local:
        din_loc_root = case.get_value("DIN_LOC_ROOT")
        testcase = case.get_value("TESTCASE")

        if not os.path.isdir(din_loc_root):
            try:
                os.makedirs(din_loc_root)
            except OSError as e:
                if e.errno == errno.EACCES:
                    logger.info("Invalid permissions to create {}".format(din_loc_root))

        expect(
            not (not os.path.isdir(din_loc_root) and testcase != "SBN"),
            "inputdata root is not a directory or is not readable: {}".format(
                din_loc_root
            ),
        )

    # Remove batch scripts
    if reset or clean:
        # clean setup-generated files
        batch_script = get_batch_script_for_job(case.get_primary_job())
        files_to_clean = [
            batch_script,
            "env_mach_specific.xml",
            "Macros.make",
            "Macros.cmake",
            "cmake_macros",
        ]
        for file_to_clean in files_to_clean:
            if os.path.exists(file_to_clean) and not (keep and file_to_clean in keep):
                if os.path.isdir(file_to_clean):
                    shutil.rmtree(file_to_clean)
                else:
                    os.remove(file_to_clean)
                logger.info("Successfully cleaned {}".format(file_to_clean))

        if not test_mode:
            # rebuild the models (even on restart)
            case.set_value("BUILD_COMPLETE", False)

        # Cannot leave case in bad state (missing env_mach_specific.xml)
        if clean and not os.path.isfile("env_mach_specific.xml"):
            case.flush()
            generate_env_mach_specific(
                caseroot,
                mach_obj,
                compiler,
                mpilib,
                debug,
                comp_interface,
                sysos,
                False,
                threaded=case.get_build_threaded(),
                noenv=True,
            )
            case.read_xml()

    if not clean:
        if not non_local:
            case.load_env()

        _create_macros(
            case, mach_obj, caseroot, compiler, mpilib, debug, comp_interface, sysos
        )

        # Set tasks to 1 if mpi-serial library
        if mpilib == "mpi-serial":
            case.set_value("NTASKS", 1)

        # Check ninst.
        # In CIME there can be multiple instances of each component model (an ensemble) NINST is the instance of that component.
        comp_interface = case.get_value("COMP_INTERFACE")
        if comp_interface == "nuopc":
            ninst = case.get_value("NINST")

        multi_driver = case.get_value("MULTI_DRIVER")

        for comp in models:
            ntasks = case.get_value("NTASKS_{}".format(comp))
            if comp == "CPL":
                continue
            if comp_interface != "nuopc":
                ninst = case.get_value("NINST_{}".format(comp))
            if multi_driver:
                if comp_interface != "nuopc":
                    expect(
                        case.get_value("NINST_LAYOUT_{}".format(comp)) == "concurrent",
                        "If multi_driver is TRUE, NINST_LAYOUT_{} must be concurrent".format(
                            comp
                        ),
                    )
                case.set_value("NTASKS_PER_INST_{}".format(comp), ntasks)
            else:
                if ninst > ntasks:
                    if ntasks == 1:
                        case.set_value("NTASKS_{}".format(comp), ninst)
                        ntasks = ninst
                    else:
                        expect(
                            False,
                            "NINST_{comp} value {ninst} greater than NTASKS_{comp} {ntasks}".format(
                                comp=comp, ninst=ninst, ntasks=ntasks
                            ),
                        )

                case.set_value(
                    "NTASKS_PER_INST_{}".format(comp), max(1, int(ntasks / ninst))
                )

        if os.path.exists(get_batch_script_for_job(case.get_primary_job())):
            logger.info(
                "Machine/Decomp/Pes configuration has already been done ...skipping"
            )

            case.initialize_derived_attributes()

            case.set_value("BUILD_THREADED", case.get_build_threaded())

        else:
            case.check_pelayouts_require_rebuild(models)

            unlock_file("env_build.xml")
            unlock_file("env_batch.xml")

            case.flush()
            case.check_lockedfiles()

            case.initialize_derived_attributes()

            cost_per_node = case.get_value("COSTPES_PER_NODE")
            case.set_value("COST_PES", case.num_nodes * cost_per_node)
            threaded = case.get_build_threaded()
            case.set_value("BUILD_THREADED", threaded)
            if threaded and case.total_tasks * case.thread_count > cost_per_node:
                smt_factor = max(
                    1.0, int(case.get_value("MAX_TASKS_PER_NODE") / cost_per_node)
                )
                case.set_value(
                    "TOTALPES",
                    case.iotasks
                    + int(
                        (case.total_tasks - case.iotasks)
                        * max(1.0, float(case.thread_count) / smt_factor)
                    ),
                )
            else:
                case.set_value(
                    "TOTALPES",
                    (case.total_tasks - case.iotasks) * case.thread_count
                    + case.iotasks,
                )

            # May need to select new batch settings if pelayout changed (e.g. problem is now too big for prev-selected queue)
            env_batch = case.get_env("batch")
            env_batch.set_job_defaults([(case.get_primary_job(), {})], case)

            # create batch files
            env_batch.make_all_batch_files(case)

            if Config.instance().make_case_run_batch_script and not case.get_value(
                "TEST"
            ):
                input_batch_script = os.path.join(
                    case.get_value("MACHDIR"), "template.case.run.sh"
                )
                env_batch.make_batch_script(
                    input_batch_script,
                    "case.run",
                    case,
                    outfile=get_batch_script_for_job("case.run.sh"),
                )

            # Make a copy of env_mach_pes.xml in order to be able
            # to check that it does not change once case.setup is invoked
            case.flush()
            logger.debug("at copy TOTALPES = {}".format(case.get_value("TOTALPES")))
            lock_file("env_mach_pes.xml")
            lock_file("env_batch.xml")

        # Create user_nl files for the required number of instances
        if not os.path.exists("user_nl_cpl"):
            logger.info("Creating user_nl_xxx files for components and cpl")

        # loop over models
        for model in models:
            comp = case.get_value("COMP_{}".format(model))
            logger.debug("Building {} usernl files".format(model))
            _build_usernl_files(case, model, comp)
            if comp == "cism":
                glcroot = case.get_value("COMP_ROOT_DIR_GLC")
                run_cmd_no_fail(
                    "{}/cime_config/cism.template {}".format(glcroot, caseroot)
                )
            if comp == "cam":
                camroot = case.get_value("COMP_ROOT_DIR_ATM")
                if os.path.exists(os.path.join(camroot, "cam.case_setup.py")):
                    logger.debug("Running cam.case_setup.py")
                    run_cmd_no_fail(
                        "python {cam}/cime_config/cam.case_setup.py {cam} {case}".format(
                            cam=camroot, case=caseroot
                        )
                    )

        _build_usernl_files(case, "drv", "cpl")

        # Create needed directories for case
        case.create_dirs()

        logger.info(
            "If an old case build already exists, might want to run 'case.build --clean' before building"
        )

        # Some tests need namelists created here (ERP) - so do this if we are in test mode
        if (
            test_mode or Config.instance().case_setup_generate_namelist
        ) and not non_local:
            logger.info("Generating component namelists as part of setup")
            case.create_namelists()

        # Record env information
        env_module = case.get_env("mach_specific")
        if mach == "zeus":
            overrides = env_module.get_overrides_nodes(case)
            logger.debug("Updating Zeus nodes {}".format(overrides))
        env_module.make_env_mach_specific_file("sh", case)
        env_module.make_env_mach_specific_file("csh", case)
        if not non_local:
            env_module.save_all_env_info("software_environment.txt")

        logger.info(
            "You can now run './preview_run' to get more info on how your case will be run"
        )


###############################################################################
def case_setup(self, clean=False, test_mode=False, reset=False, keep=None):
    ###############################################################################
    caseroot, casebaseid = self.get_value("CASEROOT"), self.get_value("CASEBASEID")
    phase = "setup.clean" if clean else "case.setup"
    functor = lambda: _case_setup_impl(
        self, caseroot, clean=clean, test_mode=test_mode, reset=reset, keep=keep
    )

    is_batch = self.get_value("BATCH_SYSTEM") is not None
    msg_func = None

    if is_batch:
        jobid = batch_jobid()
        msg_func = lambda *args: jobid if jobid is not None else ""

    if self.get_value("TEST") and not test_mode:
        test_name = casebaseid if casebaseid is not None else self.get_value("CASE")
        with TestStatus(test_dir=caseroot, test_name=test_name) as ts:
            try:
                run_and_log_case_status(
                    functor,
                    phase,
                    custom_starting_msg_functor=msg_func,
                    custom_success_msg_functor=msg_func,
                    caseroot=caseroot,
                    is_batch=is_batch,
                )
            except BaseException:  # Want to catch KeyboardInterrupt too
                ts.set_status(SETUP_PHASE, TEST_FAIL_STATUS)
                raise
            else:
                if clean:
                    ts.set_status(SETUP_PHASE, TEST_PEND_STATUS)
                else:
                    ts.set_status(SETUP_PHASE, TEST_PASS_STATUS)
    else:
        run_and_log_case_status(
            functor,
            phase,
            custom_starting_msg_functor=msg_func,
            custom_success_msg_functor=msg_func,
            caseroot=caseroot,
            is_batch=is_batch,
        )
