"""
common implementation for data model build-namelists

These are used by components/data_comps/<component>/bld/build-namelist
"""

from CIME.XML.standard_module_setup import *
from CIME.utils import expect, handle_standard_logging_options, setup_standard_logging_options
from CIME.case import Case
import sys, os, shutil, glob, argparse, doctest

logger = logging.getLogger(__name__)

###############################################################################
def parse_input(argv):
###############################################################################

    if "--test" in argv:
        test_results = doctest.testmod(verbose=True)
        sys.exit(1 if test_results.failed > 0 else 0)

    parser = argparse.ArgumentParser()

    setup_standard_logging_options(parser)

    parser.add_argument("caseroot", default=os.getcwd(),
                        help="Case directory")

    parser.add_argument("cimeroot", default=os.getcwd(),
                        help="CIMEROOT directory")

    parser.add_argument("confdir", 
                        help="Configuration directory")

    parser.add_argument("inst_string", 
                        help="instance string")

    parser.add_argument("namelist_infiles",
                        help="namelist input files")

    parser.add_argument("user_xml_dir",
                        help="user xml directory")

    args = parser.parse_args()

    handle_standard_logging_options(args)

    return args.caseroot, args.confdir, args.inst_string, args.namelist_infiles, args.user_xml_dir


# pylint: enable=too-many-arguments,too-many-locals,too-many-branches,too-many-statements
####################################################################################
def setup_build_namelist(argv, component, cimeroot):
####################################################################################

    caseroot, confdir, inst_string, namelist_infiles, user_xml_dir = parse_input(argv)

    # Figure out where definition/defaults files are.
    namelist_xml_dir = os.path.join(cimeroot, "components", "data_comps",
                                    component, "bld", "namelist_files")
    definition_file_basename = "namelist_definition_%s.xml" % component
    definition_files = [os.path.join(namelist_xml_dir, definition_file_basename)]
    user_definition = os.path.join(user_xml_dir, definition_file_basename)

    # User definition *replaces* existing definition.
    if os.path.isfile(user_definition):
        definition_files = [user_definition]
    defaults_file_basename = "namelist_defaults_%s.xml" % component
    defaults_files = [os.path.join(namelist_xml_dir, defaults_file_basename)]
    user_defaults = os.path.join(user_xml_dir, defaults_file_basename)

    # User defaults *extends* existing defaults.
    if os.path.isfile(user_defaults):
        defaults_files.append(user_defaults)
    for file_ in definition_files + defaults_files:
        expect(os.path.isfile(file_),
               "Namelist XML file %s not found!" % file_)

    # Split apart input file names.
    if namelist_infiles == '':
        infiles = []
    else:
        infiles = namelist_infiles.split(',')

    return caseroot, confdir, inst_string, infiles, definition_files, defaults_files 

####################################################################################
def create_namelist_groups(nmlgen, case, component, domain_file, domain_path):
####################################################################################
    """ 
    sets up namelist groups and default values common to all data models
    """
    # Create namelist `shr_strdata_nml` namelist group.
    nmlgen.create_shr_strdata_nml()

    # add defaults for  `dxxx_nml` namelist group - where xxx is component
    nmlgen.add_default("decomp", "1d")
    nmlgen.add_default("force_prognostic_true", ".false.")
    nmlgen.add_default("restfilm", "undefined")
    nmlgen.add_default("restfils", "undefined")

    if domain_file != "UNSET":
        full_domain_path = os.path.join(domain_path, domain_file)
        nmlgen.add_default("domainfile", value=full_domain_path)

    # Create `modelio` namelist group.
    logfile = component + ".log"
    nmlgen.add_default("logfile", logfile)
