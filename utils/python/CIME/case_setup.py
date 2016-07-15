"""
Library for case.setup.
"""

from CIME.XML.standard_module_setup import *

from CIME.check_lockedfiles import check_lockedfiles
from CIME.preview_namelists import preview_namelists
from CIME.XML.env_mach_pes  import EnvMachPes
from CIME.XML.component     import Component
from CIME.XML.compilers     import Compilers
from CIME.utils             import expect, run_cmd, append_status

import shutil, time, glob

logger = logging.getLogger(__name__)

###############################################################################
def _check_pelayouts_require_rebuild(case, models):
###############################################################################
    """
    Create if we require a rebuild, expects cwd is caseroot
    """
    locked_pes = "LockedFiles/env_mach_pes.xml"
    if os.path.exists(locked_pes):
        # Look to see if $comp_PE_CHANGE_REQUIRES_REBUILD is defined
        # for any component
        env_mach_pes_locked = EnvMachPes(infile=locked_pes)
        for comp in models:
            if case.get_value("%s_PE_CHANGE_REQUIRES_REBUILD" % comp):
                # Changing these values in env_mach_pes.xml will force
                # you to clean the corresponding component
                old_tasks   = env_mach_pes_locked.get_value("NTASKS_%s" % comp)
                old_threads = env_mach_pes_locked.get_value("NTHRDS_%s" % comp)
                old_inst    = env_mach_pes_locked.get_value("NINST_%s" % comp)

                new_tasks   = case.get_value("NTASKS_%s" % comp)
                new_threads = case.get_value("NTHRDS_%s" % comp)
                new_inst    = case.get_value("NINST_%s" % comp)

                if old_tasks != new_tasks or old_threads != new_threads or old_inst != new_inst:
                    logger.warn("%s pe change requires clean build" % comp)
                    cleanflag = comp.lower()
                    run_cmd("./case.build --clean %s" % cleanflag)

        os.remove(locked_pes)

###############################################################################
def _build_usernl_files(case, model, comp):
###############################################################################
    """
    Create user_nl_xxx files, expects cwd is caseroot
    """
    model = model.upper()
    model_file = case.get_value("CONFIG_%s_FILE" % model)
    model_dir = os.path.dirname(model_file)

    expect(os.path.isdir(model_dir),
           "cannot find cime_config directory %s for component %s" % (model_dir, comp))

    if comp == "cpl":
        if not os.path.exists("user_nl_cpl"):
            shutil.copy(os.path.join(model_dir, "user_nl_cpl"), ".")
    else:
        ninst = case.get_value("NINST_%s" % model)
        nlfile = "user_nl_%s" % comp
        model_nl = os.path.join(model_dir, nlfile)
        if os.path.exists(model_nl):
            if ninst > 1:
                for inst_counter in xrange(1, ninst+1):
                    case_nlfile = "%s_%04d" % (nlfile, inst_counter)
                    if not os.path.exists(case_nlfile):
                        shutil.copy(model_nl, case_nlfile)
            else:
                if not os.path.exists(nlfile):
                    shutil.copy(model_nl, nlfile)

###############################################################################
def case_setup(case, clean=False, test_mode=False, reset=False):
###############################################################################
    caseroot = case.get_value("CASEROOT")
    os.chdir(caseroot)
    msg = "case.setup starting"
    append_status(msg, caseroot=caseroot, sfile="CaseStatus")

    cimeroot = os.environ["CIMEROOT"]

    # Check that $DIN_LOC_ROOT exists - and abort if not a namelist compare tests
    din_loc_root = case.get_value("DIN_LOC_ROOT")
    testcase     = case.get_value("TESTCASE")
    expect(not (not os.path.isdir(din_loc_root) and testcase != "SBN"),
           "inputdata root is not a directory: \"$din_loc_root\" ")

    # Check that userdefine settings are specified before expanding variable
    for vid, value in case:
        expect(not (type(value) is str and "USERDEFINED_required_build" in value),
               "Parameter '%s' must be defined" % vid)

    # Create batch script
    if reset or clean:
        # Clean batch script

        backup_dir = "PESetupHist/b.%s" % time.strftime("%y%m%d-%H%M%S")
        if not os.path.isdir(backup_dir):
            os.makedirs(backup_dir)

        # back up relevant files
        for fileglob in ["case.run", "env_build.xml", "env_mach_pes.xml", "Macros*"]:
            for filename in glob.glob(fileglob):
                shutil.copy(filename, backup_dir)
        if os.path.exists("case.run"):
            os.remove("case.run")

        # only do the following if are NOT in testmode
        if not test_mode:
            # rebuild the models (even on restart)
            case.set_value("BUILD_COMPLETE", False)

            # backup and then clean test script
            if os.path.exists("case.test"):
                shutil.copy("case.test", backup_dir)
                os.remove("case.test")
                logger.info("Successfully cleaned test script case.test")

            if os.path.exists("case.testdriver"):
                shutil.copy("case.testdriver", backup_dir)
                os.remove("case.testdriver")
                logger.info("Successfully cleaned test script case.testdriver")

        logger.info("Successfully cleaned batch script case.run")

        logger.info("Successfully cleaned batch script case.run")
        logger.info("Some files have been saved to %s" % backup_dir)

        msg = "case.setup clean complete"
        append_status(msg, caseroot=caseroot, sfile="CaseStatus")

    if not clean:
        drv_comp = Component()
        models = drv_comp.get_valid_model_components()
        models.remove("DRV")

        mach = case.get_value("MACH")
        expect(mach is not None, "xml variable MACH is not set")

        # Create Macros file only if it does not exist
        if not os.path.exists("Macros"):
            logger.debug("Creating Macros file for %s" % mach)
            compilers = Compilers(compiler=case.get_value("COMPILER"), machine=mach, os_=case.get_value("OS"), mpilib=case.get_value("MPILIB"))
            compilers.write_macros_file()
        else:
            logger.debug("Macros script already created ...skipping")

        # Set tasks to 1 if mpi-serial library
        if case.get_value("MPILIB") == "mpi-serial":
            for vid, value in case:
                if vid.startswith("NTASKS_") and value != 1:
                    case.set_value(vid, 1)

        # Check ninst.
        # In CIME there can be multiple instances of each component model (an ensemble) NINST is the instance of that component.
        for comp in models:
            ninst  = case.get_value("NINST_%s" % comp)
            ntasks = case.get_value("NTASKS_%s" % comp)
            if ninst > ntasks:
                if ntasks == 1:
                    case.set_value("NTASKS_%s" % comp, ninst)
                else:
                    expect(False, "NINST_%s value %d greater than NTASKS_%s %d" % (comp, ninst, comp, ntasks))

        expect(not (case.get_value("BUILD_THREADED") and case.get_value("COMPILER") == "nag"),
               "it is not possible to run with OpenMP if using the NAG Fortran compiler")

        if os.path.exists("case.run"):
            logger.info("Machine/Decomp/Pes configuration has already been done ...skipping")
        else:
            _check_pelayouts_require_rebuild(case, models)

            if os.path.exists("LockedFiles/env_build.xml"):
                os.remove("LockedFiles/env_build.xml")

            case.flush()
            check_lockedfiles()

            pestot = int(run_cmd("Tools/taskmaker.pl -sumonly"))
            case.set_value("TOTALPES", pestot)

            # Compute cost based on PE count
            pval = 1
            pcnt = 0
            while pval < pestot:
                pval *= 2
                pcnt += 6 # (scaling like sqrt(6/10))
            pcost = 3 - pcnt / 10 # (3 is 64 with 6)

            # Compute cost based on DEBUG
            dcost = 3 if case.get_value("DEBUG") else 0

            # Compute cost based on run length
            # For simplicity, we use a heuristic just based on STOP_OPTION (not considering
            # STOP_N), and only deal with options longer than ndays
            lcost = 0
            if "nmonth" in case.get_value("STOP_OPTION"):
                # N months costs 30x as much as N days; since cost is based on log-base-2, add 5
                lcost = 5
            elif "nyear" in case.get_value("STOP_OPTION"):
                # N years costs 365x as much as N days; since cost is based on log-base-2, add 9
                lcost = 9

            estcost = pcost + dcost + lcost
            for cost in ["CCSM_CCOST", "CCSM_GCOST", "CCSM_TCOST", "CCSM_CCOST"]:
                estcost += case.get_value(cost)

            case.set_value("CCSM_PCOST", pcost)
            case.set_value("CCSM_ESTCOST", estcost)

            # create batch file
            logger.info("Creating batch script case.run")

            # Use BatchFactory to get the appropriate instance of a BatchMaker,
            # use it to create our batch scripts
            env_batch = case._get_env("batch")
            for job in env_batch.get_jobs():
                input_batch_script  = os.path.join(case.get_value("MACHDIR"), env_batch.get_value('template', subgroup=job))
                if job == "case.test" and testcase is not None and not test_mode:
                    logger.info("Writing %s script" % job)
                    testscript = os.path.join(cimeroot, "scripts", "Testing", "Testcases", "%s_script" % testcase)
                    # Short term fix to be removed when csh tests are removed
                    if not os.path.exists(testscript):
                        env_batch.make_batch_script(input_batch_script, job, case)
                elif job != "case.test":
                    logger.info("Writing %s script" % job)
                    env_batch.make_batch_script(input_batch_script, job, case)

            # Make a copy of env_mach_pes.xml in order to be able
            # to check that it does not change once case.setup is invoked
            logger.info("Locking file env_mach_pes.xml")
            case.flush()
            shutil.copy("env_mach_pes.xml", "LockedFiles")

        # Create user_nl files for the required number of instances
        if not os.path.exists("user_nl_cpl"):
            logger.info("Creating user_nl_xxx files for components and cpl")
        # loop over models
        for model in models:
            comp = case.get_value("COMP_%s" % model)
            logger.info("Building %s usernl files"%model)
            _build_usernl_files(case, model, comp)
            if comp == "cism":
                run_cmd("%s/../components/cism/cime_config/cism.template %s" % (cimeroot, caseroot))

        _build_usernl_files(case, "drv", "cpl")

        # Run preview namelists for scripts
        logger.info("preview_namelists")
        preview_namelists(case)

        logger.info("See ./CaseDoc for component namelists")
        logger.info("If an old case build already exists, might want to run \'case.build --clean-all\' before building")

        # Create test script if appropriate
        # Short term fix to be removed when csh tests are removed
        if os.path.exists("env_test.xml"):
            if not os.path.exists("case.test"):
                logger.info("Starting testcase.setup")
                run_cmd("./testcase.setup -caseroot %s" % caseroot)
                logger.info("Finished testcase.setup")

        msg = "case.setup complete"
        append_status(msg, caseroot=caseroot, sfile="CaseStatus")

