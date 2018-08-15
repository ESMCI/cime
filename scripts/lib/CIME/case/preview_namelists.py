"""
API for preview namelist
create_dirs and create_namelists are members of Class case from file case.py
"""

from CIME.XML.standard_module_setup import *
from CIME.utils import run_sub_or_cmd, safe_copy
import time, glob
logger = logging.getLogger(__name__)

def create_dirs(self):
    """
    Make necessary directories for case
    """
    # Get data from XML
    exeroot  = self.get_value("EXEROOT")
    libroot  = self.get_value("LIBROOT")
    incroot  = self.get_value("INCROOT")
    rundir   = self.get_value("RUNDIR")
    caseroot = self.get_value("CASEROOT")
    cimeroot = self.get_value("CIMEROOT")
    cime_model = self.get_value("MODEL")

    docdir = os.path.join(caseroot, "CaseDocs")
    dirs_to_make = []
    models = self.get_values("COMP_CLASSES")
    bldxshr = False
    for model in models:
        dirname = model.lower()
        dirs_to_make.append(os.path.join(exeroot, dirname, "obj"))
        comp = self.get_value("COMP_{}".format(model))
        if comp.startswith('x'):
            bldxshr = True

    dirs_to_make.extend([exeroot, libroot, incroot, rundir, docdir])

    for dir_to_make in dirs_to_make:
        if (not os.path.isdir(dir_to_make)):
            try:
                logger.debug("Making dir '{}'".format(dir_to_make))
                os.makedirs(dir_to_make)
            except OSError as e:
                expect(False, "Could not make directory '{}', error: {}".format(dir_to_make, e))

    # Create cmake files for case
    # Copy includedCMakeLists.txt to case directory and set paths
    with open(os.path.join(cimeroot, "scripts", "cmake", "includedCMakeLists.txt")) as fin, open(os.path.join(exeroot,"includedCMakeLists.txt"), "w") as fout:
        for line in fin.readlines():
            if bldxshr and "${CIME_ESP}" in line:
                line = line.replace("${CIME_ESP}","${CIME_ESP} xshr")
            if "${MODEL}" in line:
                line = line.replace("${MODEL}",self.get_value("MODEL"))
            if "ADD_SUBDIRECTORY(${CIME_DIR}/${SEQ_REL_DIR})" in line:
                for model in models:
                    ninst = self.get_value("NINST_{}".format(model))
                    if model != "CPL":
                        fout.writelines("ADD_DEFINITIONS(-DNUM_COMP_INST_{}={})\n".format(model,ninst))

            fout.writelines(line)
            if "cmake_minimum_required" in line:
                fout.writelines("Set(CASEROOT \"{}\")\n".format(caseroot))
                fout.writelines("include({})\n".format(os.path.join(caseroot,"Macros.cmake")))
                fout.writelines("include({})\n".format(os.path.join(cimeroot,"src","CMake","CIME_initial_setup.cmake")))
            if "Configuring Components" in line:
                if bldxshr:
                    xshr_rel_dir = os.path.join("src","components","xcpl_comps","xshare")
                    fout.writelines("SET(XSHR_DIR {})\n".format(os.path.join(cimeroot,xshr_rel_dir)))
                    fout.writelines("SET(XSHR_BINARY_DIR ${CIME_BINARY_DIR}" + os.sep + "{})\n".format(xshr_rel_dir))
                    fout.writelines("ADD_SUBDIRECTORY(${XSHR_DIR})\n")
                    fout.writelines("INCLUDE_DIRECTORIES(${XSHR_BINARY_DIR})\n")
                for model in models:
                    comp = self.get_value("COMP_{}".format(model))
                    # this may not work for e3sm (comp_root_dir_xxx is not defined)
                    if cime_model == 'cesm':
                        comp_dir = self.get_value("COMP_ROOT_DIR_{}".format(model))
                    else:
                        config_file = self.get_value("CONFIG_{}_FILE".format(model))
                        comp_dir = config_file.replace("cime_config/config_component.xml","")
                    rel_dir = comp_dir.replace(cimeroot,"")

                    fout.writelines("SET({}_DIR {})\n".format(model,comp_dir))


                    fout.writelines("SET({}_BINARY_DIR".format(model) + " ${CIME_BINARY_DIR}" + "{})\n".format(rel_dir))

    # As a convenience write the location of the case directory in the bld and run directories
    for dir_ in (exeroot, rundir):
        with open(os.path.join(dir_,"CASEROOT"),"w+") as fd:
            fd.write(caseroot+"\n")

def create_namelists(self, component=None):
    """
    Create component namelists
    """
    self.flush()

    create_dirs(self)

    casebuild = self.get_value("CASEBUILD")
    caseroot = self.get_value("CASEROOT")
    rundir = self.get_value("RUNDIR")

    docdir = os.path.join(caseroot, "CaseDocs")

    # Load modules
    self.load_env()

    self.stage_refcase()


    logger.info("Creating component namelists")

    # Create namelists - must have cpl last in the list below
    # Note - cpl must be last in the loop below so that in generating its namelist,
    # it can use xml vars potentially set by other component's buildnml scripts
    models = self.get_values("COMP_CLASSES")
    models += [models.pop(0)]
    for model in models:
        model_str = model.lower()
        logger.info("  {} {}".format(time.strftime("%Y-%m-%d %H:%M:%S"),model_str))
        config_file = self.get_value("CONFIG_{}_FILE".format(model_str.upper()))
        config_dir = os.path.dirname(config_file)
        if model_str == "cpl":
            compname = "drv"
        else:
            compname = self.get_value("COMP_{}".format(model_str.upper()))
        if component is None or component == model_str:
            # first look in the case SourceMods directory
            cmd = os.path.join(caseroot, "SourceMods", "src."+compname, "buildnml")
            if os.path.isfile(cmd):
                logger.warning("\nWARNING: Using local buildnml file {}\n".format(cmd))
            else:
                # otherwise look in the component config_dir
                cmd = os.path.join(config_dir, "buildnml")
            expect(os.path.isfile(cmd), "Could not find buildnml file for component {}".format(compname))
            run_sub_or_cmd(cmd, (caseroot), "buildnml", (self, caseroot, compname), case=self)

    logger.info("Finished creating component namelists")

    # Save namelists to docdir
    if (not os.path.isdir(docdir)):
        os.makedirs(docdir)
        try:
            with open(os.path.join(docdir, "README"), "w") as fd:
                fd.write(" CESM Resolved Namelist Files\n   For documentation only DO NOT MODIFY\n")
        except (OSError, IOError) as e:
            expect(False, "Failed to write {}/README: {}".format(docdir, e))

    for cpglob in ["*_in_[0-9]*", "*modelio*", "*_in",
                   "*streams*txt*", "*stxt", "*maps.rc", "*cism.config*"]:
        for file_to_copy in glob.glob(os.path.join(rundir, cpglob)):
            logger.debug("Copy file from '{}' to '{}'".format(file_to_copy, docdir))
            safe_copy(file_to_copy, docdir)

    # Copy over chemistry mechanism docs if they exist
    if (os.path.isdir(os.path.join(casebuild, "camconf"))):
        for file_to_copy in glob.glob(os.path.join(casebuild, "camconf", "*chem_mech*")):
            safe_copy(file_to_copy, docdir)
