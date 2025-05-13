#!/usr/bin/env python3

from CIME.Tools.standard_script_setup import *
from CIME.utils import expect
from CIME.case import Case
from argparse import RawTextHelpFormatter
import re

logger = logging.getLogger(__name__)

###############################################################################
def parse_command_line(args):
    ###############################################################################
    parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter)

    CIME.utils.setup_standard_logging_options(parser)

    parser.add_argument(
        "--case",
        "-case",
        required=True,
        help="(required) Specify a new case name. If not a full pathname, "
        "\nthe new case will be created under then current working directory.",
    )

    parser.add_argument(
        "--clone",
        "-clone",
        required=True,
        help="(required) Specify a case to be cloned. If not a full pathname, "
        "\nthe case to be cloned is assumed to be under then current working directory.",
    )

    parser.add_argument(
        "--ensemble",
        default=1,
        help="clone an ensemble of cases, the case name argument must end in an integer.\n"
        "for example: ./create_clone --clone case.template --case case.001 --ensemble 4 \n"
        "will create case.001, case.002, case.003, case.004 from existing case.template",
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
        "\nin this case, the included directory will be applied multiple times.)"
        "\nIf this argument is used in conjunction "
        "\nwith the --keepexe flag, then no changes will be permitted to the env_build.xml "
        "\nin the newly created case directory. ",
    )

    parser.add_argument(
        "--keepexe",
        "-keepexe",
        action="store_true",
        help="Sets EXEROOT to point to original build. It is HIGHLY recommended "
        "\nthat the original case be built BEFORE cloning it if the --keepexe flag is specfied. "
        "\nThis flag will make the SourceMods/ directory in the newly created case directory a "
        "\nsymbolic link to the SourceMods/ directory in the original case directory. ",
    )

    parser.add_argument(
        "--mach-dir",
        "-mach_dir",
        help="Specify the locations of the Machines directory, other than the default. "
        "\nThe default is CIMEROOT/machines.",
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
        "--cime-output-root",
        help="Specify the root output directory. The default is the setting in the original"
        "\ncase directory. NOTE: create_clone will fail if this directory is not writable.",
    )

    args = CIME.utils.parse_args_and_handle_standard_logging_options(args, parser)

    if args.case is None:
        expect(False, "Must specify -case as an input argument")

    if args.clone is None:
        expect(False, "Must specify -clone as an input argument")

    startval = "1"
    if int(args.ensemble) > 1:
        m = re.search(r"(\d+)$", args.case)
        expect(m, " case name must end in an integer to use this feature")
        startval = m.group(1)

    return (
        args.case,
        args.clone,
        args.keepexe,
        args.mach_dir,
        args.project,
        args.cime_output_root,
        args.user_mods_dirs,
        int(args.ensemble),
        startval,
    )


##############################################################################
def _main_func():
    ###############################################################################

    (
        case,
        clone,
        keepexe,
        mach_dir,
        project,
        cime_output_root,
        user_mods_dirs,
        ensemble,
        startval,
    ) = parse_command_line(sys.argv)

    cloneroot = os.path.abspath(clone)
    expect(os.path.isdir(cloneroot), "Missing cloneroot directory %s " % cloneroot)

    if user_mods_dirs is not None:
        user_mods_dirs = [
            os.path.abspath(one_user_mods_dir)
            if os.path.isdir(one_user_mods_dir)
            else one_user_mods_dir
            for one_user_mods_dir in user_mods_dirs
        ]
    nint = len(startval)

    for i in range(int(startval), int(startval) + ensemble):
        if ensemble > 1:
            case = case[:-nint] + "{{0:0{0:d}d}}".format(nint).format(i)
        with Case(cloneroot, read_only=False) as clone:
            clone.create_clone(
                case,
                keepexe=keepexe,
                mach_dir=mach_dir,
                project=project,
                cime_output_root=cime_output_root,
                user_mods_dirs=user_mods_dirs,
            )


###############################################################################

if __name__ == "__main__":
    _main_func()
