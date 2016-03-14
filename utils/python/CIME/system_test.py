"""
Base class for CIME system tests
"""
import shutil, glob
from CIME.XML.standard_module_setup import *
from CIME.case import Case
from CIME.XML.env_run import EnvRun
from CIME.XML.env_test import EnvTest
from CIME.utils import run_cmd, convert_to_type
import CIME.build as build

class SystemTest(object):
    def __init__(self,  testname, caseroot=os.getcwd(), case=None):
        """
        initialize a CIME system test object, if the file LockedFiles/env_run.orig.xml
        does not exist copy the current env_run.xml file.  If it does exist restore values
        changed in a previous run of the test.
        """
        self._caseroot = caseroot
        if case is None:
            self._case = Case()
        else:
            self._case = case
        self._testname = testname

        if os.path.isfile(os.path.join(caseroot, "LockedFiles", "env_run.orig.xml")):
            self.compare_env_run(expectedrunvars)
        elif os.path.isfile(os.path.join(caseroot, "env_run.xml")):
            lockedfiles = os.path.join(caseroot, "Lockedfiles")
            try:
                os.stat(lockedfiles)
            except:
                os.mkdir(lockedfiles)
            shutil.copy("env_run.xml",
                        os.path.join(lockedfiles, "env_run.orig.xml"))

    def build(self, sharedlib_only=False, model_only=False):
        bldphases = self._case._test.get_step_phase_cnt("BUILD")
        pattern = re.compile("^TEST")
        for bld in str(bldphases):
            self._update_settings("BUILD", bld)
            if not pattern.match(self._testname):
                build.case_build(self._caseroot, case=self._case,
                                 sharedlib_only=sharedlib_only, model_only=model_only)

    def _update_settings(self, name, cnt):
        test = self._case._test
        settings = test.get_settings_for_phase(name, cnt)
        if settings:
            for name,value in settings:
                if name == "eval":
                    cmd = self._case.get_resolved_value(value)
                    run_cmd(cmd)
                else:
                    type_str = self._case.get_type_info(name)
                    self._case.set_value(name, convert_to_type(value, type_str, name))
            self._case.flush()

    def run(self):
        runphases = self._case._test.get_step_phase_cnt("RUN")
        for run in str(runphases):
            self._update_settings("RUN", run)
            run_cmd("./case.run")
            if run == 1:
                ccm = os.path.join(self._case.get_value("SCRIPTSROOT"),"Tools","component_compare_move.sh")
                run_cmd("ccm -rundir %s -testcase %s -suffix \"base\""%(self._case.get_value("RUNDIR"),
                                                                        self._case.get_value("CASE")))

    def report(self):
        return

    def check_mem_leak(self):
        """ TODO: incomplete """
        rundir = self._case.get_value("RUNDIR")
        cpllogfile = min(glob.iglob(os.path.join(rundir, "cpl.log*")), key=os.path.getctime)

    def compare_env_run(self, expected=None):
        f1obj = EnvRun(self._caseroot, "env_run.xml")
        f2obj = EnvRun(self._caseroot, os.path.join("LockedFiles", "env_run.orig.xml"))
        diffs = f1obj.compare_xml(f2obj)
        for key in diffs.keys():
            if key in expected:
                logging.warn("  Resetting %s for test"%key)
                f1obj.set_value(key, f2obj.get_value(key, resolved=False))
            else:
                print "Found difference in %s: case: %s original value %s" %\
                    (key, diffs[key][0], diffs[key][1])
                print " Use option --force to run the test with this"\
                    " value or --reset to reset to original"
                return False
        return True


