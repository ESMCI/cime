#!/usr/bin/env python3

# pylint: disable=W0621, W0613

"""
Script to create a new CIME Case Control System (CSS) experimental case.
"""

from CIME.Tools.standard_script_setup import *
from CIME.utils import (
    expect,
    get_cime_config,
    get_cime_default_driver,
    get_src_root,
)
from CIME.config import Config
from CIME.case import Case
from argparse import RawTextHelpFormatter

logger = logging.getLogger(__name__)

###############################################################################
def parse_command_line(args, cimeroot, description):
    ###############################################################################
    parser = argparse.ArgumentParser(
        description=description, formatter_class=RawTextHelpFormatter
    )

    CIME.utils.setup_standard_logging_options(parser)

    customize_path = os.path.join(CIME.utils.get_src_root(), "cime_config", "customize")

    config = Config.load(customize_path)

    try:
        cime_config = get_cime_config()
    except Exception:
        cime_config = None

    parser.add_argument(
        "--case",
        "-case",
        required=True,
        metavar="CASENAME",
        help="(required) Specify the case name. "
        "\nIf this is simply a name (not a path), the case directory is created in the current working directory."
        "\nThis can also be a relative or absolute path specifying where the case should be created;"
        "\nwith this usage, the name of the case will be the last component of the path.",
    )

    parser.add_argument(
        "--compset",
        "-compset",
        required=True,
        help="(required) Specify a compset. "
        "\nTo see list of current compsets, use the utility ./query_config --compsets in this directory.\n",
    )

    parser.add_argument(
        "--res",
        "-res",
        required=True,
        metavar="GRID",
        help="(required) Specify a model grid resolution. "
        "\nTo see list of current model resolutions, use the utility "
        "\n./query_config --grids in this directory.",
    )

    parser.add_argument(
        "--machine",
        "-mach",
        help="Specify a machine. "
        "The default value is the match to NODENAME_REGEX in config_machines.xml. To see "
        "\nthe list of current machines, invoke ./query_config --machines.",
    )

    parser.add_argument(
        "--compiler",
        "-compiler",
        help="Specify a compiler. "
        "\nTo see list of supported compilers for each machine, use the utility "
        "\n./query_config --machines in this directory. "
        "\nThe default value will be the first one listed.",
    )

    parser.add_argument(
        "--multi-driver",
        action="store_true",
        help="Specify that --ninst should modify the number of driver/coupler instances. "
        "\nThe default is to have one driver/coupler supporting multiple component instances.",
    )

    parser.add_argument(
        "--ninst",
        default=1,
        type=int,
        help="Specify number of model ensemble instances. "
        "\nThe default is multiple components and one driver/coupler. "
        "\nUse --multi-driver to run multiple driver/couplers in the ensemble.",
    )

    parser.add_argument(
        "--mpilib",
        "-mpilib",
        help="Specify the MPI library. "
        "To see list of supported mpilibs for each machine, invoke ./query_config --machines."
        "\nThe default is the first listing in MPILIBS in config_machines.xml.\n",
    )

    parser.add_argument(
        "--project",
        "-project",
        help="Specify a project id for the case (optional)."
        "\nUsed for accounting and directory permissions when on a batch system."
        "\nThe default is user or machine specified by PROJECT."
        "\nAccounting (only) may be overridden by user or machine specified CHARGE_ACCOUNT.",
    )

    parser.add_argument(
        "--pecount",
        "-pecount",
        default="M",
        help="Specify a target size description for the number of cores. "
        "\nThis is used to query the appropriate config_pes.xml file and find the "
        "\noptimal PE-layout for your case - if it exists there. "
        "\nAllowed options are  ('S','M','L','X1','X2','[0-9]x[0-9]','[0-9]').\n",
    )

    # This option supports multiple values, hence the plural ("user-mods-dirs"). However,
    # we support the singular ("user-mods-dir") for backwards compatibility (and because
    # the singular may be more intuitive for someone who only wants to use a single
    # directory).
    parser.add_argument(
        "--user-mods-dirs",
        "--user-mods-dir",
        nargs="*",
        help="Full pathname to a directory containing any combination of user_nl_* files "
        "\nand a shell_commands script (typically containing xmlchange commands). "
        "\nThe directory can also contain an SourceMods/ directory with the same structure "
        "\nas would be found in a case directory."
        "\nIt can also contain a file named 'include_user_mods' which gives the path to"
        "\none or more other directories that should be included."
        "\nMultiple directories can be given to the --user-mods-dirs argument,"
        "\nin which case changes from all of them are applied."
        "\n(If there are conflicts, later directories take precedence.)"
        "\n(Care is needed if multiple directories include the same directory via 'include_user_mods':"
        "\nin this case, the included directory will be applied multiple times.)",
    )

    parser.add_argument(
        "--pesfile",
        help="Full pathname of an optional pes specification file. "
        "\nThe file can follow either the config_pes.xml or the env_mach_pes.xml format.",
    )

    parser.add_argument(
        "--gridfile",
        help="Full pathname of config grid file to use. "
        "\nThis should be a copy of config/config_grids.xml with the new user grid changes added to it. \n",
    )

    if cime_config and cime_config.has_option("main", "workflow"):
        workflow_default = cime_config.get("main", "workflow")
    else:
        workflow_default = "default"

    parser.add_argument(
        "--workflow",
        default=workflow_default,
        help="A workflow from config_workflow.xml to apply to this case. ",
    )

    srcroot_default = get_src_root()

    parser.add_argument(
        "--srcroot",
        default=srcroot_default,
        help="Alternative pathname for source root directory. "
        f"The default is {srcroot_default}",
    )

    parser.add_argument(
        "--output-root",
        help="Alternative pathname for the directory where case output is written.",
    )

    # The following is a deprecated option
    parser.add_argument(
        "--script-root", dest="script_root", default=None, help=argparse.SUPPRESS
    )

    if config.allow_unsupported:
        parser.add_argument(
            "--run-unsupported",
            action="store_true",
            help="Force the creation of a case that is not tested or supported by CESM developers.",
        )
    # hidden argument indicating called from create_test
    # Indicates that create_newcase was called from create_test - do not use otherwise.
    parser.add_argument("--test", "-test", action="store_true", help=argparse.SUPPRESS)

    parser.add_argument(
        "--walltime",
        default=os.getenv("CIME_GLOBAL_WALLTIME"),
        help="Set the wallclock limit for this case in the format (the usual format is HH:MM:SS). "
        "\nYou may use env var CIME_GLOBAL_WALLTIME to set this. "
        "\nIf CIME_GLOBAL_WALLTIME is not defined in the environment, then the walltime"
        "\nwill be the maximum allowed time defined for the queue in config_batch.xml.",
    )

    parser.add_argument(
        "-q",
        "--queue",
        default=None,
        help="Force batch system to use the specified queue. ",
    )

    parser.add_argument(
        "--handle-preexisting-dirs",
        dest="answer",
        choices=("a", "r", "u"),
        default=None,
        help="Do not query how to handle pre-existing bld/exe dirs. "
        "\nValid options are (a)bort (r)eplace or (u)se existing. "
        "\nThis can be useful if you need to run create_newcase non-iteractively.",
    )

    parser.add_argument(
        "-i",
        "--input-dir",
        help="Use a non-default location for input files. This will change the xml value of DIN_LOC_ROOT.",
    )

    drv_choices = config.driver_choices
    drv_help = (
        "Override the top level driver type and use this one "
        + "(changes xml variable COMP_INTERFACE) [this is an advanced option]"
    )

    parser.add_argument(
        "--driver",
        default=get_cime_default_driver(),
        choices=drv_choices,
        help=drv_help,
    )

    parser.add_argument(
        "-n",
        "--non-local",
        action="store_true",
        help="Use when you've requested a machine that you aren't on. "
        "Will reduce errors for missing directories etc.",
    )

    parser.add_argument(
        "--extra-machines-dir",
        help="Optional path to a directory containing one or more of:"
        "\nconfig_machines.xml, config_batch.xml."
        "\nIf provided, the contents of these files will be appended to"
        "\nthe standard machine files (and any files in ~/.cime).",
    )

    parser.add_argument("--case-group", help="Add this case to a case group")

    parser.add_argument(
        "--ngpus-per-node",
        default=0,
        type=int,
        help="Specify number of GPUs used for simulation. ",
    )

    args = CIME.utils.parse_args_and_handle_standard_logging_options(args, parser)

    if args.srcroot is not None:
        expect(
            os.path.isdir(args.srcroot),
            "Input non-default directory srcroot {} does not exist ".format(
                args.srcroot
            ),
        )
        args.srcroot = os.path.abspath(args.srcroot)

    if args.gridfile is not None:
        expect(
            os.path.isfile(args.gridfile),
            "Grid specification file {} does not exist ".format(args.gridfile),
        )

    if args.pesfile is not None:
        expect(
            os.path.isfile(args.pesfile),
            "Pes specification file {} cannot be found ".format(args.pesfile),
        )

    run_unsupported = False
    if config.allow_unsupported:
        run_unsupported = args.run_unsupported

    expect(
        CIME.utils.check_name(args.case, fullpath=True),
        "Illegal case name argument provided",
    )

    if args.input_dir is not None:
        args.input_dir = os.path.abspath(args.input_dir)
    elif cime_config and cime_config.has_option("main", "input_dir"):
        args.input_dir = os.path.abspath(cime_config.get("main", "input_dir"))

    if config.create_test_flag_mode == "cesm" and args.driver == "mct":
        logger.warning(
            """========================================================================
WARNING: The MCT-based driver and data models will be removed from CESM
WARNING: on September 30, 2022.
WARNING: Please contact members of the CESM Software Engineering Group
WARNING: if you need support migrating to the ESMF/NUOPC infrastructure.
========================================================================"""
        )

    return (
        args.case,
        args.compset,
        args.res,
        args.machine,
        args.compiler,
        args.mpilib,
        args.project,
        args.pecount,
        args.user_mods_dirs,
        args.pesfile,
        args.gridfile,
        args.srcroot,
        args.test,
        args.multi_driver,
        args.ninst,
        args.walltime,
        args.queue,
        args.output_root,
        args.script_root,
        run_unsupported,
        args.answer,
        args.input_dir,
        args.driver,
        args.workflow,
        args.non_local,
        args.extra_machines_dir,
        args.case_group,
        args.ngpus_per_node,
    )


###############################################################################
def _main_func(description=None):
    ###############################################################################
    cimeroot = os.path.abspath(CIME.utils.get_cime_root())

    (
        casename,
        compset,
        grid,
        machine,
        compiler,
        mpilib,
        project,
        pecount,
        user_mods_dirs,
        pesfile,
        gridfile,
        srcroot,
        test,
        multi_driver,
        ninst,
        walltime,
        queue,
        output_root,
        script_root,
        run_unsupported,
        answer,
        input_dir,
        driver,
        workflow,
        non_local,
        extra_machines_dir,
        case_group,
        ngpus_per_node,
    ) = parse_command_line(sys.argv, cimeroot, description)

    if script_root is None:
        caseroot = os.path.abspath(casename)
    else:
        caseroot = os.path.abspath(script_root)

    if user_mods_dirs is not None:
        user_mods_dirs = [
            os.path.abspath(one_user_mods_dir)
            if os.path.isdir(one_user_mods_dir)
            else one_user_mods_dir
            for one_user_mods_dir in user_mods_dirs
        ]

    # create_test creates the caseroot before calling create_newcase
    # otherwise throw an error if this directory exists
    expect(
        not (os.path.exists(caseroot) and not test),
        "Case directory {} already exists".format(caseroot),
    )

    # create_newcase ... --test ... throws a CIMEError along with
    # a very stern warning message to the user
    # if it detects that it was invoked outside of create_test
    if test:
        expect(
            (
                "FROM_CREATE_TEST" in os.environ
                and os.environ["FROM_CREATE_TEST"] == "True"
            ),
            "The --test argument is intended to only be called from inside create_test. Invoking this option from the command line is not appropriate usage.",
        )
        del os.environ["FROM_CREATE_TEST"]

    with Case(caseroot, read_only=False, non_local=non_local) as case:
        # Configure the Case
        case.create(
            casename,
            srcroot,
            compset,
            grid,
            user_mods_dirs=user_mods_dirs,
            machine_name=machine,
            project=project,
            pecount=pecount,
            compiler=compiler,
            mpilib=mpilib,
            pesfile=pesfile,
            gridfile=gridfile,
            multi_driver=multi_driver,
            ninst=ninst,
            test=test,
            walltime=walltime,
            queue=queue,
            output_root=output_root,
            run_unsupported=run_unsupported,
            answer=answer,
            input_dir=input_dir,
            driver=driver,
            workflowid=workflow,
            non_local=non_local,
            extra_machines_dir=extra_machines_dir,
            case_group=case_group,
            ngpus_per_node=ngpus_per_node,
        )

        # Called after create since casedir does not exist yet
        case.record_cmd(init=True)


###############################################################################

if __name__ == "__main__":
    _main_func(__doc__)
