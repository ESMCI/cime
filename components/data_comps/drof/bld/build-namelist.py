#!/usr/bin/env python

"""Namelist creator for CIME's data river model.

While `build-namelist` historically has been a script in its own right, this
module can be imported, and provides the same functionality via the
`build_namelist` function.
"""

# Typically ignore this.
# pylint: disable=invalid-name

# Disable these because this is our standard setup
# pylint: disable=wildcard-import,unused-wildcard-import,wrong-import-position

import os
import shutil
import sys

CIMEROOT = os.environ.get("CIMEROOT")
if CIMEROOT is None:
    raise SystemExit("ERROR: must set CIMEROOT environment variable")
sys.path.append(os.path.join(CIMEROOT, "scripts", "Tools"))

from standard_script_setup import *
from CIME.case import Case
from CIME.nmlgen import NamelistGenerator
from CIME.utils import expect

logger = logging.getLogger(__name__)

COMPONENT = 'drof'

# Yes this is a long function, but for now just live with it.
# pylint: disable=too-many-arguments,too-many-locals,too-many-branches,too-many-statements
####################################################################################
def build_namelist(case, confdir, inst_string, infiles, definition_files,
                   defaults_files):
####################################################################################
    """Write out the namelist for this component.

    Most arguments are the same as those for `NamelistGenerator`. The
    `inst_string` argument is used as a suffix to distinguish files for
    different instances. The `confdir` argument is used to specify the directory
    in which output files will be placed.
    """

    #----------------------------------------------------
    # Get a bunch of information from the case.
    #----------------------------------------------------
    din_loc_root = case.get_value("DIN_LOC_ROOT")
    rof_domain_file = case.get_value("ROF_DOMAIN_FILE")
    rof_domain_path = case.get_value("ROF_DOMAIN_PATH")
    drof_mode = case.get_value("DROF_MODE")
    rof_grid = case.get_value("ROF_GRID")

    #----------------------------------------------------
    # Check for incompatible options.
    #----------------------------------------------------
    expect(rof_grid != "null",
           "ROF_GRID cannot be null")
    expect(drof_mode != "NULL",
           "DROF_MODE cannot be NULL")

    #----------------------------------------------------
    # Log some settings.
    #----------------------------------------------------
    logger.info("DROF mode is %s", drof_mode)
    logger.info("DROF grid is %s", rof_grid)

    #----------------------------------------------------
    # Clear out old data.
    #----------------------------------------------------
    data_list_path = os.path.join(case.get_case_root(), "Buildconf",
                                  "drof.input_data_list")
    if os.path.exists(data_list_path):
        os.remove(data_list_path)

    #----------------------------------------------------
    # Create configuration information.
    #----------------------------------------------------
    config = {}
    config['rof_grid'] = rof_grid
    config['drof_mode'] = drof_mode

    #----------------------------------------------------
    # Construct the namelist generator.
    #----------------------------------------------------
    nmlgen = NamelistGenerator(case, infiles, definition_files, defaults_files,
                               config)

    #----------------------------------------------------
    # Construct the list of streams.
    #----------------------------------------------------
    streams = nmlgen.get_streams()

    #----------------------------------------------------
    # For each stream, create stream text file and update input data list.
    #----------------------------------------------------
    for stream in streams:

        # Ignore null values.
        if stream is None or stream in ("NULL", ""):
            continue

        inst_stream = stream + inst_string
        logger.info("DROF stream is %s", inst_stream)
        stream_path = os.path.join(confdir,
                                   "drof.streams.txt." + inst_stream)
        user_stream_path = os.path.join(case.get_case_root(),
                                        "user_drof.streams.txt." + inst_stream)

        # Use the user's stream file, or create one if necessary.
        if os.path.exists(user_stream_path):
            shutil.copyfile(user_stream_path, stream_path)
        else:
            nmlgen.create_stream_file(config, stream, stream_path,
                                      data_list_path)

    #----------------------------------------------------
    # Create namelist groups
    #----------------------------------------------------
    # Create namelist `shr_strdata_nml` namelist group.
    rof_full_domain_path = os.path.join(rof_domain_path, rof_domain_file)
    nmlgen.create_shr_strdata_nml(domain_file_path=rof_full_domain_path)

    # Create `drof_nml` namelist group.
    # Should the following be in the namelist definitions file instead of here?
    nmlgen.add_default("decomp", "1d")
    nmlgen.add_default("force_prognostic_true", ".false.")
    nmlgen.add_default("restfilm", "undefined")
    nmlgen.add_default("restfils", "undefined")

    # Create `modelio` namelist group.
    nmlgen.add_default("logfile", "rof.log")

    #----------------------------------------------------
    # Finally, write out all the namelists.
    #----------------------------------------------------
    namelist_file = os.path.join(confdir, COMPONENT+"_in")
    modelio_file = os.path.join(confdir, "rof_modelio.nml")
    nmlgen.write_output_files(namelist_file, modelio_file, data_list_path)

# pylint: enable=too-many-arguments,too-many-locals,too-many-branches,too-many-statements
####################################################################################
def _main_func(caseroot, confdir, inst_string, namelist_infiles, user_xml_dir):
####################################################################################
    # Figure out where definition/defaults files are.
    namelist_xml_dir = os.path.join(CIMEROOT, "components", "data_comps",
                                    COMPONENT, "bld", "namelist_files")
    definition_file_basename = "namelist_definition_%s.xml" % COMPONENT
    definition_files = [os.path.join(namelist_xml_dir, definition_file_basename)]
    user_definition = os.path.join(user_xml_dir, definition_file_basename)

    # User definition *replaces* existing definition.
    if os.path.isfile(user_definition):
        definition_files = [user_definition]
    defaults_file_basename = "namelist_defaults_%s.xml" % COMPONENT
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

    # Now build the component namelist and required stream txt files
    with Case(caseroot) as case:
        build_namelist(case, confdir, inst_string, infiles,
                       definition_files, defaults_files)

####################################################################################
if __name__ == "__main__":
####################################################################################
    # Arguments expected from the buildnml script.
    CASEROOT = sys.argv[1]
    # This is passed in, but ignore it, since we require CIMEROOT to be set in
    # the environment.
    # CIMEROOT = sys.argv[2]
    CONFDIR = sys.argv[3]
    INST_STRING = sys.argv[4]
    NAMELIST_INFILES = sys.argv[5]
    USER_XML_DIR = sys.argv[6]
    _main_func(CASEROOT, CONFDIR, INST_STRING, NAMELIST_INFILES, USER_XML_DIR)
