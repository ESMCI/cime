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

logger = logging.getLogger(__name__)

class SystemTest(object):
    def __init__(self,  testname, caseroot=os.getcwd(), case=None):
        """
        initialize a CIME system test object, if the file LockedFiles/env_run.orig.xml
        does not exist copy the current env_run.xml file.  If it does exist restore values
        changed in a previous run of the test.   Test definitions are taken from config_tests.xml
        """
        self._caseroot = caseroot
        # Needed for sh scripts
        os.environ["CASEROOT"] = caseroot
        if case is None:
            self._case = Case()
        else:
            self._case = case
        self._testname = testname

        if os.path.isfile(os.path.join(caseroot, "LockedFiles", "env_run.orig.xml")):
            self.compare_env_run()
        elif os.path.isfile(os.path.join(caseroot, "env_run.xml")):
            lockedfiles = os.path.join(caseroot, "LockedFiles")
            try:
                os.stat(lockedfiles)
            except:
                os.mkdir(lockedfiles)
            shutil.copy("env_run.xml",
                        os.path.join(lockedfiles, "env_run.orig.xml"))
        self._case._test.set_initial_values(self._case)




    def build(self, sharedlib_only=False, model_only=False):
        """
        Build the test case(s) using BUILD settings defined in env_tests.xml
        """
        bldphases = self._case._test.get_step_phase_cnt("BUILD")
        pattern = re.compile("^TEST")
        for bld in range(1,bldphases+1):
            self._update_settings("BUILD", bld)
            build.case_build(self._caseroot, case=self._case,
                             sharedlib_only=sharedlib_only, model_only=model_only,
                             testonly=pattern.match(self._testname))
            expect(self._testname != "TESTBUILDFAIL", "Test build failure")


    def _update_settings(self, name, cnt):
        """
        Update the case based on the settings defined in env_tests.xml for the cnt phase of the
        name (BUILD,RUN) step
        """
        test = self._case._test
        settings = test.get_settings_for_phase(name, str(cnt))
        if settings:
            for name,value in settings:
                if name == "eval":
                    cmd = self._case.get_resolved_value(value)
                    run_cmd(cmd)
                else:
                    type_str = self._case.get_type_info(name)
                    newvalue = convert_to_type(value,
                                               type_str, name, ok_to_fail=True)
                    if type(value) is type(newvalue):
                        newvalue = self._case.get_resolved_value(newvalue)
                    if type(newvalue) is str and type_str != "char":
                        newvalue = eval(newvalue)
                    self._case.set_value(name, newvalue)
            self._case.flush()

    def run(self):
        """
        Run the test(s), check for memory leaks and compare any history files in the run directory
        """
        runphases = self._case._test.get_step_phase_cnt("RUN")
        for run in range(1,runphases+1):
            self._update_settings("RUN", run)
            test_dir = self._case.get_value("CASEROOT")
            rc, output, errput = run_cmd("./case.run", ok_to_fail=True,
                                         from_dir=test_dir)
            logger.info("Run %s of %s completed with rc %s" % (run, runphases, rc))
            with open(os.path.join(test_dir, "TestStatus"), "r") as fe:
                teststatus = fe.read()
            if rc != 0:
                teststatus = teststatus.replace('PEND','FAIL')
                lognote = "case.run failed.\nOutput: %s\n\nErrput: %s" % (output,errput)
                logger.info(lognote)
                with open(os.path.join(test_dir, "TestStatus.log"), "a") as fd:
                    fd.write(lognote)
            else:
                teststatus = teststatus.replace('PEND','PASS')

            with open(os.path.join(test_dir, "TestStatus"), "w") as fd:
                fd.write(teststatus)
            if rc != 0:
                break
            self._checkformemleak(test_dir, run)
            if runphases > 1:
                ccm = os.path.join(self._case.get_value("SCRIPTSROOT"),"Tools","component_compare_move.sh")

                if run == 1:
                    suffix = "base"
                elif run == 2:
                    suffix = "rest"
                run_cmd("%s -rundir %s -testcase %s -suffix %s"%(ccm, self._case.get_value("RUNDIR"),
                                                                   self._case.get_value("CASE"),suffix))
        if runphases > 1:
            self._compare(test_dir)

    def _getlatestcpllog(self):
        """
        find and return the latest cpl log file in the run directory
        """
        newestcpllogfile = min(glob.iglob(os.path.join(
                    self._case.get_value('RUNDIR'),'cpl.log.*')), key=os.path.getctime)
        return newestcpllogfile

    def _checkformemleak(self, test_dir, runnum):
        """
        Examine memory usage as recorded in the cpl log file and look for unexpected
        increases.
        """
        newestcpllogfile = self._getlatestcpllog()
        cmd = os.path.join(self._case.get_value("SCRIPTSROOT"),"Tools","check_memory.pl")
        rc, out, err = run_cmd("%s -file1 %s -m 1.5"%(cmd, newestcpllogfile),ok_to_fail=True)
        if rc == 0:
            with open(os.path.join(test_dir, "TestStatus"), "a") as fd:
                fd.write("PASS %s memleak\n"%(self._case.get_value("CASEBASEID")))
                fd.write("COMMENT run: %s\n"%runnum)
        else:
            with open(os.path.join(test_dir, "TestStatus.log"), "a") as fd:
                fd.write("memleak out: %s\n\nerror: %s"%(out,err))
            with open(os.path.join(test_dir, "TestStatus"), "a") as fd:
                fd.write("FAIL %s memleak\n"%(self._case.get_value("CASEBASEID")))
                fd.write("COMMENT run: %s\n"%runnum)



    def _compare(self, test_dir):
        """
        check to see if there are history files to be compared, compare if they are there
        """
        cmd = os.path.join(self._case.get_value("SCRIPTSROOT"),"Tools",
                                                "component_compare_test.sh")
        rc, out, err = run_cmd("%s -rundir %s -testcase %s -testcase_base %s -suffix1 base -suffix2 rest"
                               %(cmd, self._case.get_value('RUNDIR'), self._case.get_value('CASE'),
                                 self._case.get_value('CASEBASEID')), ok_to_fail=True)
        if rc == 0:
            with open(os.path.join(test_dir, "TestStatus"), "a") as fd:
                fd.write(out)
        else:
            with open(os.path.join(test_dir, "TestStatus.log"), "a") as fd:
                fd.write("Component_compare_test.sh failed out: %s\n\nerr: %s\n"%(out,err))

    def compare_baseline(self):
        """
        compare the current test output to a baseline result
        """
        baselineroot = self._case.get_value("BASELINE_ROOT")
        test_dir = self._case.get_value("CASEROOT")
        basecmp_dir = os.path.join(baselineroot, self._case.get_value("BASECMP_CASE"))
        for bdir in (baselineroot, basecmp_dir):
            if not os.path.isdir(bdir):
                with open(os.path.join(test_dir, "TestStatus"), "a") as fd:
                    fd.write("GFAIL %s baseline\n",self._case.get_value("CASEBASEID"))
                with open(os.path.join(test_dir, "TestStatus.log"), "a") as fd:
                    fd.write("ERROR %s does not exist",bdir)
                return -1
        compgen = os.path.join(self._case.get_value("SCRIPTSROOT"),"Tools",
                               "component_compgen_baseline.sh")
        compgen += " -baseline_dir "+basecmp_dir
        compgen += " -test_dir "+self._case.get_value("RUNDIR")
        compgen += " -compare_tag "+self._case.get_value("BASELINE_NAME_CMP")
        compgen += " -testcase "+self._case.get_value("CASE")
        compgen += " -testcase_base "+self._case.get_value("CASEBASEID")
        rc, out, err = run_cmd(compgen, ok_to_fail=True)
        with open(os.path.join(test_dir, "TestStatus"), "a") as fd:
            fd.write(out)
        if rc != 0:
            with open(os.path.join(test_dir, "TestStatus.log"), "a") as fd:
                fd.write("Error in Baseline compare: %s"%err)


    def generate_baseline(self):
        """
        generate a new baseline case based on the current test
        """
        newestcpllogfile = self._getlatestcpllog()
        baselineroot = self._case.get_value("BASELINE_ROOT")
        basegen_dir = os.path.join(baselineroot, self._case.get_value("BASEGEN_CASE"))
        test_dir = self._case.get_value("CASEROOT")
        for bdir in (baselineroot, basegen_dir):
            if not os.path.isdir(bdir):
                with open(os.path.join(test_dir, "TestStatus"), "a") as fd:
                    fd.write("GFAIL %s baseline\n",self._case.get_value("CASEBASEID"))
                with open(os.path.join(test_dir, "TestStatus.log"), "a") as fd:
                    fd.write("ERROR %s does not exist",bdir)
                return -1
        compgen = os.path.join(self._case.get_value("SCRIPTSROOT"),"Tools",
                               "component_compgen_baseline.sh")
        compgen += " -baseline_dir "+basegen_dir
        compgen += " -test_dir "+self._case.get_value("RUNDIR")
        compgen += " -generate_tag "+self._case.get_value("BASELINE_NAME_GEN")
        compgen += " -testcase "+self._case.get_value("CASE")
        compgen += " -testcase_base "+self._case.get_value("CASEBASEID")
        rc, out, err = run_cmd(compgen, ok_to_fail=True)
        # copy latest cpl log to baseline
        shutil.copyfile(newestcpllogfile, basegen_dir)

        with open(os.path.join(test_dir, "TestStatus"), "a") as fd:
            fd.write(out)
        if rc != 0:
            with open(os.path.join(test_dir, "TestStatus.log"), "a") as fd:
                fd.write("Error in Baseline Generate: %s"%err)

    def compare_env_run(self, expected=None):
        """
        Compare the env_run.xml to the pre test env_run stored in the LockedFiles directory
        """
        f1obj = EnvRun(self._caseroot, "env_run.xml")
        f2obj = EnvRun(self._caseroot, os.path.join("LockedFiles", "env_run.orig.xml"))
        diffs = f1obj.compare_xml(f2obj)
        for key in diffs.keys():
            if expected is not None and key in expected:
                logging.warn("  Resetting %s for test"%key)
                f1obj.set_value(key, f2obj.get_value(key, resolved=False))
            else:
                print "Found difference in %s: case: %s original value %s" %\
                    (key, diffs[key][0], diffs[key][1])
                print " Use option --force to run the test with this"\
                    " value or --reset to reset to original"
                return False
        return True


