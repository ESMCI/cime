"""
common implementation for building namelist commands

These are used by components/<model_type>/<component>/cime_config/buildnml
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

    args = parser.parse_args()

    handle_standard_logging_options(args)

    return args.caseroot

###############################################################################
def build_xcpl_nml(argv, compclass):
###############################################################################

    caseroot = parse_input(argv)

    compname = "x" + compclass

    caseroot = parse_input(argv)

    with Case(caseroot) as case:
        rundir = case.get_value("RUNDIR")
        ninst  = case.get_value("NINST_%s" % compclass.upper())
        nx     = case.get_value("%s_NX" % compclass.upper())
        ny     = case.get_value("%s_NY" % compclass.upper())
        if compname == "xrof":
            flood_mode = case.get_value('XROF_FLOOD_MODE')

    extras = []
    dtype = 1
    npes = 0
    length = 0

    if compname == "xatm":
        if ny == 1:
            dtype = 2
        extras = [["24",
                   "ncpl  number of communications w/coupler per dat"],
                  ["0.0",
                   "simul time proxy (secs): time between cpl comms"]]
    elif compname == "xglc" or compname == "xice":
        dtype = 2
    elif compname == "xlnd":
        dtype = 11
    elif compname == "xocn":
        dtype = 4
    elif compname == "xrof":
        dtype = 11
        if flood_mode == "ACTIVE":
            extras = [[".true.", "flood flag"]]
        else:
            extras = [[".false.", "flood flag"]]

    for i in range(1, ninst + 1):
        # If only 1 file, name is 'compclass_in'
        # otherwise files are 'compclass_in0001', 'compclass_in0002', etc
        if ninst == 1:
            filename = os.path.join(rundir, "%s_in" % compname)
        else:
            filename = os.path.join(rundir, "%s_in_%4.4d" % (compname, i))

        with open(filename, 'w') as infile:
            infile.write("%-20d ! i-direction global dimension\n" % nx)
            infile.write("%-20d ! j-direction global dimension\n" % ny)
            infile.write("%-20d ! decomp_type  1=1d-by-lat, 2=1d-by-lon,"
                         " 3=2d, 4=2d evensquare, 11=segmented\n" % dtype)
            infile.write("%-20d ! num of pes for i (type 3 only)\n" % npes)
            infile.write("%-20d ! length of segments (type 4 only)\n"
                         % length)
            for extra in extras:
                infile.write("%-20s ! %s\n" % (extra[0], extra[1]))


###############################################################################
def build_data_nml(argv, compclass):
###############################################################################
    # This function is just a wrapper for the one below, to avoid having to
    # indent everything for the "with" block.
    caseroot = parse_input(argv)
    with Case(caseroot) as case:
        _build_data_nml(case, caseroot, compclass)

###############################################################################
def _build_data_nml(case, caseroot, compclass):
###############################################################################

    cimeroot = case.get_value("CIMEROOT")
    rundir   = case.get_value("RUNDIR")
    ninst    = case.get_value("NINST_%s" % compclass.upper())
    compname = "d" + compclass
    din_loc_root = case.get_value("DIN_LOC_ROOT")

    if not os.path.isdir(din_loc_root):
        os.makedirs(din_loc_root)
        logger.info("Created input root directory %s" %din_loc_root)

    confdir = os.path.join(caseroot,"Buildconf",compname + "conf")
    if not os.path.isdir(confdir):
        os.makedirs(confdir)

    inst_string = ""
    inst_counter = 1
    while (inst_counter <= ninst):

        # determine instance string
        inst_string = ""
        if ninst > 1:
            inst_string = '_' + '%04d' % inst_counter

            # If multi-instance case does not have restart file, use
            # single-case restart for each instance
            rpointer = "rpointer." + compname
            if (os.path.isfile(os.path.join(rundir,rpointer)) and
                (not os.path.isfile(os.path.join(rundir,rpointer + inst_string)))):
                shutil.copy(os.path.join(rundir, rpointer),
                            os.path.join(rundir, rpointer + inst_string))

        inst_string_label = inst_string
        if not inst_string_label:
            inst_string_label = "\"\""

        # create namelist output infile using user_nl_file as input
        user_nl_file = os.path.join(caseroot, "user_nl_" + compname + inst_string)
        expect(os.path.isfile(user_nl_file),
               "Missing required user_nl_file %s " %(user_nl_file))
        infile = os.path.join(confdir, "namelist_infile")
        create_namelist_infile(case, user_nl_file, infile)

        # determine directory for user modified namelist_definitions.xml and namelist_defaults.xml
        user_xml_dir = os.path.join(caseroot, "SourceMods", "src." + compname)
        expect (os.path.isdir(user_xml_dir),
                "user_xml_dir %s does not exist " %user_xml_dir)

        # call build-namelist for data component
        command = os.path.join(cimeroot, "components", "data_comps", compname, "cime_config", "build-namelist")
        cmd = "%s --confdir %s --caseroot %s --cimeroot %s  --infile %s --user_xml_dir %s --inst_string %s" \
              % (command, confdir, caseroot, cimeroot, infile, user_xml_dir, inst_string_label)
        logger.info( "cmd is: %s " %cmd)
        rc, out, err = run_cmd(cmd, from_dir=confdir)
        expect(rc==0,"Command %s failed rc=%d\nout=%s\nerr=%s"%(cmd,rc,out,err))
        if out is not None and len(out) > 0:
            logger.debug("cmd=%s"%cmd)
            logger.info("out = %s"%out)
        if err is not None and len(err) > 0:
            logger.info("err= %s"%err)

        # copy namelist files and stream text files, to rundir
        if os.path.isdir(rundir):
            filename = compname + "_in"
            file_src  = os.path.join(confdir, filename)
            file_dest = os.path.join(rundir, filename)
            if inst_string:
                file_dest += inst_string
            shutil.copy(file_src,file_dest)

            for txtfile in glob.glob(os.path.join(confdir, "*txt*")):
                shutil.copy(txtfile, rundir)

        # increment instance counter
        inst_counter = inst_counter + 1

###############################################################################
def create_namelist_infile(case, user_nl_file, namelist_infile, infile_text=""):
###############################################################################
    lines_input = []
    if os.path.isfile(user_nl_file):
        with open(user_nl_file, "r") as file_usernl:
            lines_input = file_usernl.readlines()
    else:
        logger.warn("WARNING: No file %s found in case directory"%user_nl_file)

    lines_output = []
    lines_output.append("&comp_inparm \n")
    if infile_text:
        lines_output.append(infile_text)
        logger.info("file_infile %s " %infile_text)

    for line in lines_input:
        match1 = re.search(r"^[\&\/\!]", line)
        match2 = re.search(r"\$([\w\_])+", line)
        if match1 is None and match2 is not None:
            line = case.get_resolved_value(line)
        if match1 is None:
            lines_output.append(line)

    lines_output.append("/ \n")

    with open(namelist_infile, "w") as file_infile:
        file_infile.write("\n".join(lines_output))
