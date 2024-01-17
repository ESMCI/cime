#!/usr/bin/env python3

import filecmp
import os
import re
import shutil
import sys

from CIME import utils
from CIME.tests import base
from CIME.case.case import Case
from CIME.build import CmakeTmpBuildDir


class TestCreateNewcase(base.BaseTestCase):
    @classmethod
    def setUpClass(cls):
        cls._testdirs = []
        cls._do_teardown = []
        cls._testroot = os.path.join(cls.TEST_ROOT, "TestCreateNewcase")
        cls._root_dir = os.getcwd()

    def tearDown(self):
        cls = self.__class__
        os.chdir(cls._root_dir)

    def test_a_createnewcase(self):
        cls = self.__class__

        testdir = os.path.join(cls._testroot, "testcreatenewcase")
        if os.path.exists(testdir):
            shutil.rmtree(testdir)
        args = " --case %s --compset X --output-root %s --handle-preexisting-dirs=r" % (
            testdir,
            cls._testroot,
        )
        if self._config.allow_unsupported:
            args += " --run-unsupported"
        if self.TEST_COMPILER is not None:
            args = args + " --compiler %s" % self.TEST_COMPILER
        if self.TEST_MPILIB is not None:
            args = args + " --mpilib %s" % self.TEST_MPILIB
        if utils.get_cime_default_driver() == "nuopc":
            args += " --res f19_g17 "
        else:
            args += " --res f19_g16 "

        args += f" --machine {self.MACHINE.get_machine_name()}"

        cls._testdirs.append(testdir)
        self.run_cmd_assert_result(
            "./create_newcase %s" % (args), from_dir=self.SCRIPT_DIR
        )
        self.assertTrue(os.path.exists(testdir))
        self.assertTrue(os.path.exists(os.path.join(testdir, "case.setup")))

        self.run_cmd_assert_result("./case.setup", from_dir=testdir)
        self.run_cmd_assert_result("./case.build", from_dir=testdir)

        with Case(testdir, read_only=False) as case:
            ntasks = case.get_value("NTASKS_ATM")
            case.set_value("NTASKS_ATM", ntasks + 1)

        # this should fail with a locked file issue
        self.run_cmd_assert_result("./case.build", from_dir=testdir, expected_stat=1)

        self.run_cmd_assert_result("./case.setup --reset", from_dir=testdir)
        self.run_cmd_assert_result("./case.build", from_dir=testdir)
        with Case(testdir, read_only=False) as case:
            case.set_value("CHARGE_ACCOUNT", "fred")
            # to be used in next test
            batch_system = case.get_value("BATCH_SYSTEM")

        # on systems (like github workflow) that do not have batch, set this for the next test
        if batch_system == "none":
            self.run_cmd_assert_result(
                './xmlchange --subgroup case.run BATCH_COMMAND_FLAGS="-q \$JOB_QUEUE"',
                from_dir=testdir,
            )

        # this should not fail with a locked file issue
        self.run_cmd_assert_result("./case.build", from_dir=testdir)

        self.run_cmd_assert_result("./case.st_archive --test-all", from_dir=testdir)

        with Case(testdir, read_only=False) as case:
            batch_command = case.get_value("BATCH_COMMAND_FLAGS", subgroup="case.run")

        self.run_cmd_assert_result(
            './xmlchange --append --subgroup case.run BATCH_COMMAND_FLAGS="-l trythis"',
            from_dir=testdir,
        )
        # Test that changes to BATCH_COMMAND_FLAGS work
        with Case(testdir, read_only=False) as case:
            new_batch_command = case.get_value(
                "BATCH_COMMAND_FLAGS", subgroup="case.run"
            )

        self.assertTrue(
            new_batch_command == batch_command + " -l trythis",
            msg=f"Failed to correctly append BATCH_COMMAND_FLAGS {new_batch_command} {batch_command}#",
        )

        self.run_cmd_assert_result(
            "./xmlchange JOB_QUEUE=fred --subgroup case.run --force", from_dir=testdir
        )

        with Case(testdir, read_only=False) as case:
            new_batch_command = case.get_value(
                "BATCH_COMMAND_FLAGS", subgroup="case.run"
            )
        self.assertTrue(
            "fred" in new_batch_command,
            msg="Failed to update JOB_QUEUE in BATCH_COMMAND_FLAGS {}".format(
                new_batch_command
            ),
        )

        # Trying to set values outside of context manager should fail
        case = Case(testdir, read_only=False)
        with self.assertRaises(utils.CIMEError):
            case.set_value("NTASKS_ATM", 42)

        # Trying to read_xml with pending changes should fail
        with self.assertRaises(utils.CIMEError):
            with Case(testdir, read_only=False) as case:
                case.set_value("CHARGE_ACCOUNT", "fouc")
                case.read_xml()

        cls._do_teardown.append(testdir)

    def test_aa_no_flush_on_instantiate(self):
        testdir = os.path.join(self.__class__._testroot, "testcreatenewcase")
        with Case(testdir, read_only=False) as case:
            for env_file in case._files:
                self.assertFalse(
                    env_file.needsrewrite,
                    msg="Instantiating a case should not trigger a flush call",
                )

        with Case(testdir, read_only=False) as case:
            case.set_value("HIST_OPTION", "nyears")
            runfile = case.get_env("run")
            self.assertTrue(
                runfile.needsrewrite, msg="Expected flush call not triggered"
            )
            for env_file in case._files:
                if env_file != runfile:
                    self.assertFalse(
                        env_file.needsrewrite,
                        msg="Unexpected flush triggered for file {}".format(
                            env_file.filename
                        ),
                    )
            # Flush the file
            runfile.write()
            # set it again to the same value
            case.set_value("HIST_OPTION", "nyears")
            # now the file should not need to be flushed
            for env_file in case._files:
                self.assertFalse(
                    env_file.needsrewrite,
                    msg="Unexpected flush triggered for file {}".format(
                        env_file.filename
                    ),
                )

        # Check once more with a new instance
        with Case(testdir, read_only=False) as case:
            case.set_value("HIST_OPTION", "nyears")
            for env_file in case._files:
                self.assertFalse(
                    env_file.needsrewrite,
                    msg="Unexpected flush triggered for file {}".format(
                        env_file.filename
                    ),
                )

    def test_b_user_mods(self):
        cls = self.__class__

        testdir = os.path.join(cls._testroot, "testusermods")
        if os.path.exists(testdir):
            shutil.rmtree(testdir)

        cls._testdirs.append(testdir)

        user_mods_dir = os.path.join(os.path.dirname(__file__), "user_mods_test1")
        args = (
            " --case %s --compset X --user-mods-dir %s --output-root %s --handle-preexisting-dirs=r"
            % (testdir, user_mods_dir, cls._testroot)
        )
        if self._config.allow_unsupported:
            args += " --run-unsupported"
        if self.TEST_COMPILER is not None:
            args = args + " --compiler %s" % self.TEST_COMPILER
        if self.TEST_MPILIB is not None:
            args = args + " --mpilib %s" % self.TEST_MPILIB
        if utils.get_cime_default_driver() == "nuopc":
            args += " --res f19_g17 "
        else:
            args += " --res f19_g16 "

        args += f" --machine {self.MACHINE.get_machine_name()}"

        self.run_cmd_assert_result(
            "%s/create_newcase %s " % (self.SCRIPT_DIR, args), from_dir=self.SCRIPT_DIR
        )

        self.assertTrue(
            os.path.isfile(
                os.path.join(testdir, "SourceMods", "src.drv", "somefile.F90")
            ),
            msg="User_mods SourceMod missing",
        )

        with open(os.path.join(testdir, "user_nl_cpl"), "r") as fd:
            contents = fd.read()
            self.assertTrue(
                "a different cpl test option" in contents,
                msg="User_mods contents of user_nl_cpl missing",
            )
            self.assertTrue(
                "a cpl namelist option" in contents,
                msg="User_mods contents of user_nl_cpl missing",
            )
        cls._do_teardown.append(testdir)

    def test_c_create_clone_keepexe(self):
        cls = self.__class__

        testdir = os.path.join(cls._testroot, "test_create_clone_keepexe")
        if os.path.exists(testdir):
            shutil.rmtree(testdir)
        prevtestdir = cls._testdirs[0]
        user_mods_dir = os.path.join(os.path.dirname(__file__), "user_mods_test3")

        cmd = "%s/create_clone --clone %s --case %s --keepexe --user-mods-dir %s" % (
            self.SCRIPT_DIR,
            prevtestdir,
            testdir,
            user_mods_dir,
        )
        self.run_cmd_assert_result(cmd, from_dir=self.SCRIPT_DIR, expected_stat=1)
        cls._do_teardown.append(testdir)

    def test_d_create_clone_new_user(self):
        cls = self.__class__

        testdir = os.path.join(cls._testroot, "test_create_clone_new_user")
        if os.path.exists(testdir):
            shutil.rmtree(testdir)
        prevtestdir = cls._testdirs[0]
        cls._testdirs.append(testdir)
        # change the USER and CIME_OUTPUT_ROOT to nonsense values
        # this is intended as a test of whether create_clone is independent of user
        self.run_cmd_assert_result(
            "./xmlchange USER=this_is_not_a_user", from_dir=prevtestdir
        )

        fakeoutputroot = cls._testroot.replace(
            os.environ.get("USER"), "this_is_not_a_user"
        )
        self.run_cmd_assert_result(
            "./xmlchange CIME_OUTPUT_ROOT=%s" % fakeoutputroot, from_dir=prevtestdir
        )

        # this test should pass (user name is replaced)
        self.run_cmd_assert_result(
            "%s/create_clone --clone %s --case %s "
            % (self.SCRIPT_DIR, prevtestdir, testdir),
            from_dir=self.SCRIPT_DIR,
        )

        shutil.rmtree(testdir)
        # this test should pass
        self.run_cmd_assert_result(
            "%s/create_clone --clone %s --case %s --cime-output-root %s"
            % (self.SCRIPT_DIR, prevtestdir, testdir, cls._testroot),
            from_dir=self.SCRIPT_DIR,
        )

        cls._do_teardown.append(testdir)

    def test_dd_create_clone_not_writable(self):
        cls = self.__class__

        testdir = os.path.join(cls._testroot, "test_create_clone_not_writable")
        if os.path.exists(testdir):
            shutil.rmtree(testdir)
        prevtestdir = cls._testdirs[0]
        cls._testdirs.append(testdir)

        with Case(prevtestdir, read_only=False) as case1:
            case2 = case1.create_clone(testdir)
            with self.assertRaises(utils.CIMEError):
                case2.set_value("CHARGE_ACCOUNT", "fouc")
        cls._do_teardown.append(testdir)

    def test_e_xmlquery(self):
        # Set script and script path
        xmlquery = "./xmlquery"
        cls = self.__class__
        casedir = cls._testdirs[0]

        # Check for environment
        self.assertTrue(os.path.isdir(self.SCRIPT_DIR))
        self.assertTrue(os.path.isdir(self.TOOLS_DIR))
        self.assertTrue(os.path.isfile(os.path.join(casedir, xmlquery)))

        # Test command line options
        with Case(casedir, read_only=True, non_local=True) as case:
            STOP_N = case.get_value("STOP_N")
            COMP_CLASSES = case.get_values("COMP_CLASSES")
            BUILD_COMPLETE = case.get_value("BUILD_COMPLETE")
            cmd = xmlquery + " --non-local STOP_N --value"
            output = utils.run_cmd_no_fail(cmd, from_dir=casedir)
            self.assertTrue(output == str(STOP_N), msg="%s != %s" % (output, STOP_N))
            cmd = xmlquery + " --non-local BUILD_COMPLETE --value"
            output = utils.run_cmd_no_fail(cmd, from_dir=casedir)
            self.assertTrue(output == "TRUE", msg="%s != %s" % (output, BUILD_COMPLETE))
            # we expect DOCN_MODE to be undefined in this X compset
            # this test assures that we do not try to resolve this as a compvar
            cmd = xmlquery + " --non-local DOCN_MODE --value"
            _, output, error = utils.run_cmd(cmd, from_dir=casedir)
            self.assertTrue(
                error == "ERROR:  No results found for variable DOCN_MODE",
                msg="unexpected result for DOCN_MODE, output {}, error {}".format(
                    output, error
                ),
            )

            for comp in COMP_CLASSES:
                caseresult = case.get_value("NTASKS_%s" % comp)
                cmd = xmlquery + " --non-local NTASKS_%s --value" % comp
                output = utils.run_cmd_no_fail(cmd, from_dir=casedir)
                self.assertTrue(
                    output == str(caseresult), msg="%s != %s" % (output, caseresult)
                )
                cmd = xmlquery + " --non-local NTASKS --subgroup %s --value" % comp
                output = utils.run_cmd_no_fail(cmd, from_dir=casedir)
                self.assertTrue(
                    output == str(caseresult), msg="%s != %s" % (output, caseresult)
                )
            if self.MACHINE.has_batch_system():
                JOB_QUEUE = case.get_value("JOB_QUEUE", subgroup="case.run")
                cmd = xmlquery + " --non-local JOB_QUEUE --subgroup case.run --value"
                output = utils.run_cmd_no_fail(cmd, from_dir=casedir)
                self.assertTrue(
                    output == JOB_QUEUE, msg="%s != %s" % (output, JOB_QUEUE)
                )

            cmd = xmlquery + " --non-local --listall"
            utils.run_cmd_no_fail(cmd, from_dir=casedir)

        cls._do_teardown.append(cls._testroot)

    def test_f_createnewcase_with_user_compset(self):
        cls = self.__class__

        testdir = os.path.join(cls._testroot, "testcreatenewcase_with_user_compset")
        if os.path.exists(testdir):
            shutil.rmtree(testdir)

        cls._testdirs.append(testdir)

        if self._config.test_mode == "cesm":
            if utils.get_cime_default_driver() == "nuopc":
                pesfile = os.path.join(
                    utils.get_src_root(),
                    "components",
                    "cmeps",
                    "cime_config",
                    "config_pes.xml",
                )
            else:
                pesfile = os.path.join(
                    utils.get_src_root(),
                    "components",
                    "cpl7",
                    "driver",
                    "cime_config",
                    "config_pes.xml",
                )
        else:
            pesfile = os.path.join(
                utils.get_src_root(), "driver-mct", "cime_config", "config_pes.xml"
            )

        args = (
            "--case %s --compset 2000_SATM_XLND_SICE_SOCN_XROF_XGLC_SWAV  --pesfile %s --res f19_g16 --output-root %s --handle-preexisting-dirs=r"
            % (testdir, pesfile, cls._testroot)
        )
        if self._config.allow_unsupported:
            args += " --run-unsupported"
        if self.TEST_COMPILER is not None:
            args += " --compiler %s" % self.TEST_COMPILER
        if self.TEST_MPILIB is not None:
            args = args + " --mpilib %s" % self.TEST_MPILIB

        args += f" --machine {self.MACHINE.get_machine_name()}"

        self.run_cmd_assert_result(
            "%s/create_newcase %s" % (self.SCRIPT_DIR, args), from_dir=self.SCRIPT_DIR
        )
        self.run_cmd_assert_result("./case.setup", from_dir=testdir)
        self.run_cmd_assert_result("./case.build", from_dir=testdir)

        cls._do_teardown.append(testdir)

    def test_g_createnewcase_with_user_compset_and_env_mach_pes(self):
        cls = self.__class__

        testdir = os.path.join(
            cls._testroot, "testcreatenewcase_with_user_compset_and_env_mach_pes"
        )
        if os.path.exists(testdir):
            shutil.rmtree(testdir)
        previous_testdir = cls._testdirs[-1]
        cls._testdirs.append(testdir)

        pesfile = os.path.join(previous_testdir, "env_mach_pes.xml")
        args = (
            "--case %s --compset 2000_SATM_XLND_SICE_SOCN_XROF_XGLC_SWAV --pesfile %s --res f19_g16 --output-root %s --handle-preexisting-dirs=r"
            % (testdir, pesfile, cls._testroot)
        )
        if self._config.allow_unsupported:
            args += " --run-unsupported"
        if self.TEST_COMPILER is not None:
            args += " --compiler %s" % self.TEST_COMPILER
        if self.TEST_MPILIB is not None:
            args += " --mpilib %s" % self.TEST_MPILIB

        args += f" --machine {self.MACHINE.get_machine_name()}"

        self.run_cmd_assert_result(
            "%s/create_newcase %s" % (self.SCRIPT_DIR, args), from_dir=self.SCRIPT_DIR
        )
        self.run_cmd_assert_result(
            "diff env_mach_pes.xml %s" % (previous_testdir), from_dir=testdir
        )
        # this line should cause the diff to fail (I assume no machine is going to default to 17 tasks)
        self.run_cmd_assert_result("./xmlchange NTASKS=17", from_dir=testdir)
        self.run_cmd_assert_result(
            "diff env_mach_pes.xml %s" % (previous_testdir),
            from_dir=testdir,
            expected_stat=1,
        )

        cls._do_teardown.append(testdir)

    def test_h_primary_component(self):
        cls = self.__class__

        testdir = os.path.join(cls._testroot, "testprimarycomponent")
        if os.path.exists(testdir):
            shutil.rmtree(testdir)

        cls._testdirs.append(testdir)
        args = (
            " --case CreateNewcaseTest --script-root %s --compset X --output-root %s --handle-preexisting-dirs u"
            % (testdir, cls._testroot)
        )
        if self._config.allow_unsupported:
            args += " --run-unsupported"
        if self.TEST_COMPILER is not None:
            args += " --compiler %s" % self.TEST_COMPILER
        if self.TEST_MPILIB is not None:
            args += " --mpilib %s" % self.TEST_MPILIB
        if utils.get_cime_default_driver() == "nuopc":
            args += " --res f19_g17 "
        else:
            args += " --res f19_g16 "

        args += f" --machine {self.MACHINE.get_machine_name()}"

        self.run_cmd_assert_result(
            "%s/create_newcase %s" % (self.SCRIPT_DIR, args), from_dir=self.SCRIPT_DIR
        )
        self.assertTrue(os.path.exists(testdir))
        self.assertTrue(os.path.exists(os.path.join(testdir, "case.setup")))

        with Case(testdir, read_only=False) as case:
            case._compsetname = case.get_value("COMPSET")
            case.set_comp_classes(case.get_values("COMP_CLASSES"))
            primary = case._find_primary_component()
            self.assertEqual(
                primary,
                "drv",
                msg="primary component test expected drv but got %s" % primary,
            )
            # now we are going to corrupt the case so that we can do more primary_component testing
            case.set_valid_values("COMP_GLC", "%s,fred" % case.get_value("COMP_GLC"))
            case.set_value("COMP_GLC", "fred")
            primary = case._find_primary_component()
            self.assertEqual(
                primary,
                "fred",
                msg="primary component test expected fred but got %s" % primary,
            )
            case.set_valid_values("COMP_ICE", "%s,wilma" % case.get_value("COMP_ICE"))
            case.set_value("COMP_ICE", "wilma")
            primary = case._find_primary_component()
            self.assertEqual(
                primary,
                "wilma",
                msg="primary component test expected wilma but got %s" % primary,
            )

            case.set_valid_values(
                "COMP_OCN", "%s,bambam,docn" % case.get_value("COMP_OCN")
            )
            case.set_value("COMP_OCN", "bambam")
            primary = case._find_primary_component()
            self.assertEqual(
                primary,
                "bambam",
                msg="primary component test expected bambam but got %s" % primary,
            )

            case.set_valid_values("COMP_LND", "%s,barney" % case.get_value("COMP_LND"))
            case.set_value("COMP_LND", "barney")
            primary = case._find_primary_component()
            # This is a "J" compset
            self.assertEqual(
                primary,
                "allactive",
                msg="primary component test expected allactive but got %s" % primary,
            )
            case.set_value("COMP_OCN", "docn")
            case.set_valid_values("COMP_LND", "%s,barney" % case.get_value("COMP_LND"))
            case.set_value("COMP_LND", "barney")
            primary = case._find_primary_component()
            self.assertEqual(
                primary,
                "barney",
                msg="primary component test expected barney but got %s" % primary,
            )
            case.set_valid_values("COMP_ATM", "%s,wilma" % case.get_value("COMP_ATM"))
            case.set_value("COMP_ATM", "wilma")
            primary = case._find_primary_component()
            self.assertEqual(
                primary,
                "wilma",
                msg="primary component test expected wilma but got %s" % primary,
            )
            # this is a "E" compset
            case._compsetname = case._compsetname.replace("XOCN", "DOCN%SOM")
            primary = case._find_primary_component()
            self.assertEqual(
                primary,
                "allactive",
                msg="primary component test expected allactive but got %s" % primary,
            )
            # finally a "B" compset
            case.set_value("COMP_OCN", "bambam")
            primary = case._find_primary_component()
            self.assertEqual(
                primary,
                "allactive",
                msg="primary component test expected allactive but got %s" % primary,
            )

        cls._do_teardown.append(testdir)

    def test_j_createnewcase_user_compset_vs_alias(self):
        """
        Create a compset using the alias and another compset using the full compset name
        and make sure they are the same by comparing the namelist files in CaseDocs.
        Ignore the modelio files and clean the directory names out first.
        """
        cls = self.__class__

        testdir1 = os.path.join(cls._testroot, "testcreatenewcase_user_compset")
        if os.path.exists(testdir1):
            shutil.rmtree(testdir1)
        cls._testdirs.append(testdir1)

        args = " --case CreateNewcaseTest --script-root {} --compset 2000_DATM%NYF_SLND_SICE_DOCN%SOMAQP_SROF_SGLC_SWAV --output-root {} --handle-preexisting-dirs u".format(
            testdir1, cls._testroot
        )
        if utils.get_cime_default_driver() == "nuopc":
            args += " --res f19_g17 "
        else:
            args += " --res f19_g16 "
        if self._config.allow_unsupported:
            args += " --run-unsupported"
        if self.TEST_COMPILER is not None:
            args += " --compiler %s" % self.TEST_COMPILER
        if self.TEST_MPILIB is not None:
            args += " --mpilib %s" % self.TEST_MPILIB

        args += f" --machine {self.MACHINE.get_machine_name()}"

        self.run_cmd_assert_result(
            "{}/create_newcase {}".format(self.SCRIPT_DIR, args),
            from_dir=self.SCRIPT_DIR,
        )
        self.run_cmd_assert_result("./case.setup ", from_dir=testdir1)
        self.run_cmd_assert_result("./preview_namelists ", from_dir=testdir1)

        dir1 = os.path.join(testdir1, "CaseDocs")
        dir2 = os.path.join(testdir1, "CleanCaseDocs")
        os.mkdir(dir2)
        for _file in os.listdir(dir1):
            if "modelio" in _file:
                continue
            with open(os.path.join(dir1, _file), "r") as fi:
                file_text = fi.read()
                file_text = file_text.replace(os.path.basename(testdir1), "PATH")
                file_text = re.sub(r"logfile =.*", "", file_text)
            with open(os.path.join(dir2, _file), "w") as fo:
                fo.write(file_text)
        cleancasedocs1 = dir2

        testdir2 = os.path.join(cls._testroot, "testcreatenewcase_alias_compset")
        if os.path.exists(testdir2):
            shutil.rmtree(testdir2)
        cls._testdirs.append(testdir2)
        args = " --case CreateNewcaseTest --script-root {} --compset ADSOMAQP --output-root {} --handle-preexisting-dirs u".format(
            testdir2, cls._testroot
        )
        if utils.get_cime_default_driver() == "nuopc":
            args += " --res f19_g17 "
        else:
            args += " --res f19_g16 "
        if self._config.allow_unsupported:
            args += " --run-unsupported"
        if self.TEST_COMPILER is not None:
            args += " --compiler %s" % self.TEST_COMPILER
        if self.TEST_MPILIB is not None:
            args += " --mpilib %s" % self.TEST_MPILIB

        args += f" --machine {self.MACHINE.get_machine_name()}"

        self.run_cmd_assert_result(
            "{}/create_newcase {}".format(self.SCRIPT_DIR, args),
            from_dir=self.SCRIPT_DIR,
        )
        self.run_cmd_assert_result("./case.setup ", from_dir=testdir2)
        self.run_cmd_assert_result("./preview_namelists ", from_dir=testdir2)

        dir1 = os.path.join(testdir2, "CaseDocs")
        dir2 = os.path.join(testdir2, "CleanCaseDocs")
        os.mkdir(dir2)
        for _file in os.listdir(dir1):
            if "modelio" in _file:
                continue
            with open(os.path.join(dir1, _file), "r") as fi:
                file_text = fi.read()
                file_text = file_text.replace(os.path.basename(testdir2), "PATH")
                file_text = re.sub(r"logfile =.*", "", file_text)
            with open(os.path.join(dir2, _file), "w") as fo:
                fo.write(file_text)

        cleancasedocs2 = dir2
        dcmp = filecmp.dircmp(cleancasedocs1, cleancasedocs2)
        self.assertTrue(
            len(dcmp.diff_files) == 0, "CaseDocs differ {}".format(dcmp.diff_files)
        )

        cls._do_teardown.append(testdir1)
        cls._do_teardown.append(testdir2)

    def test_k_append_config(self):
        machlist_before = self.MACHINE.list_available_machines()
        self.assertEqual(
            len(machlist_before) > 1, True, msg="Problem reading machine list"
        )

        newmachfile = os.path.join(
            utils.get_cime_root(),
            "CIME",
            "data",
            "config",
            "xml_schemas",
            "config_machines_template.xml",
        )
        self.MACHINE.read(newmachfile)
        machlist_after = self.MACHINE.list_available_machines()

        self.assertEqual(
            len(machlist_after) - len(machlist_before),
            1,
            msg="Not able to append config_machines.xml {} {}".format(
                len(machlist_after), len(machlist_before)
            ),
        )
        self.assertEqual(
            "mymachine" in machlist_after,
            True,
            msg="Not able to append config_machines.xml",
        )

    def test_ka_createnewcase_extra_machines_dir(self):
        # Test that we pick up changes in both config_machines.xml and
        # cmake macros in a directory specified with the --extra-machines-dir
        # argument to create_newcase.
        cls = self.__class__
        casename = "testcreatenewcase_extra_machines_dir"

        # Setup: stage some xml files in a temporary directory
        extra_machines_dir = os.path.join(
            cls._testroot, "{}_machine_config".format(casename)
        )
        os.makedirs(os.path.join(extra_machines_dir, "cmake_macros"))
        cls._do_teardown.append(extra_machines_dir)
        newmachfile = os.path.join(
            utils.get_cime_root(),
            "CIME",
            "data",
            "config",
            "xml_schemas",
            "config_machines_template.xml",
        )
        utils.safe_copy(
            newmachfile, os.path.join(extra_machines_dir, "config_machines.xml")
        )
        cmake_macro_text = """\
set(NETCDF_PATH /my/netcdf/path)
"""
        cmake_macro_path = os.path.join(
            extra_machines_dir, "cmake_macros", "mymachine.cmake"
        )
        with open(cmake_macro_path, "w") as cmake_macro:
            cmake_macro.write(cmake_macro_text)

        # Create the case
        testdir = os.path.join(cls._testroot, casename)
        if os.path.exists(testdir):
            shutil.rmtree(testdir)
        # In the following, note that 'mymachine' is the machine name defined in
        # config_machines_template.xml
        args = (
            " --case {testdir} --compset X --mach mymachine"
            " --output-root {testroot} --non-local"
            " --extra-machines-dir {extra_machines_dir}".format(
                testdir=testdir,
                testroot=cls._testroot,
                extra_machines_dir=extra_machines_dir,
            )
        )
        if self._config.allow_unsupported:
            args += " --run-unsupported"

        if utils.get_cime_default_driver() == "nuopc":
            args += " --res f19_g17 "
        else:
            args += " --res f19_g16 "
        self.run_cmd_assert_result(
            "./create_newcase {}".format(args), from_dir=self.SCRIPT_DIR
        )

        args += f" --machine {self.MACHINE.get_machine_name()}"

        cls._do_teardown.append(testdir)

        # Run case.setup
        self.run_cmd_assert_result("./case.setup --non-local", from_dir=testdir)

        # Make sure Macros file contains expected text

        with Case(testdir, non_local=True) as case:
            with CmakeTmpBuildDir(macroloc=testdir) as cmaketmp:
                macros_contents = cmaketmp.get_makefile_vars(case=case)

            expected_re = re.compile("NETCDF_PATH.*/my/netcdf/path")
            self.assertTrue(
                expected_re.search(macros_contents),
                msg="{} not found in:\n{}".format(expected_re.pattern, macros_contents),
            )

    def test_m_createnewcase_alternate_drivers(self):
        # Test that case.setup runs for nuopc and moab drivers
        cls = self.__class__

        # TODO refactor
        if self._config.test_mode == "cesm":
            alternative_driver = ("nuopc",)
        else:
            alternative_driver = ("moab",)

        for driver in alternative_driver:
            if driver == "moab" and not os.path.exists(
                os.path.join(utils.get_cime_root(), "src", "drivers", driver)
            ):
                self.skipTest(
                    "Skipping driver test for {}, driver not found".format(driver)
                )
            if driver == "nuopc" and not os.path.exists(
                os.path.join(utils.get_src_root(), "components", "cmeps")
            ):
                self.skipTest(
                    "Skipping driver test for {}, driver not found".format(driver)
                )

            testdir = os.path.join(cls._testroot, "testcreatenewcase.{}".format(driver))
            if os.path.exists(testdir):
                shutil.rmtree(testdir)
            args = " --driver {} --case {} --compset X --res f19_g16 --output-root {} --handle-preexisting-dirs=r".format(
                driver, testdir, cls._testroot
            )
            if self._config.allow_unsupported:
                args += " --run-unsupported"
            if self.TEST_COMPILER is not None:
                args = args + " --compiler %s" % self.TEST_COMPILER
            if self.TEST_MPILIB is not None:
                args = args + " --mpilib %s" % self.TEST_MPILIB

            args += f" --machine {self.MACHINE.get_machine_name()}"

            cls._testdirs.append(testdir)
            self.run_cmd_assert_result(
                "./create_newcase %s" % (args), from_dir=self.SCRIPT_DIR
            )
            self.assertTrue(os.path.exists(testdir))
            self.assertTrue(os.path.exists(os.path.join(testdir, "case.setup")))

            self.run_cmd_assert_result("./case.setup", from_dir=testdir)
            with Case(testdir, read_only=False) as case:
                comp_interface = case.get_value("COMP_INTERFACE")
                self.assertTrue(
                    driver == comp_interface, msg="%s != %s" % (driver, comp_interface)
                )

            cls._do_teardown.append(testdir)

    def test_n_createnewcase_bad_compset(self):
        cls = self.__class__

        testdir = os.path.join(cls._testroot, "testcreatenewcase_bad_compset")
        if os.path.exists(testdir):
            shutil.rmtree(testdir)
        args = (
            " --case %s --compset InvalidCompsetName --output-root %s --handle-preexisting-dirs=r "
            % (testdir, cls._testroot)
        )
        if self._config.allow_unsupported:
            args += " --run-unsupported"
        if self.TEST_COMPILER is not None:
            args = args + " --compiler %s" % self.TEST_COMPILER
        if self.TEST_MPILIB is not None:
            args = args + " --mpilib %s" % self.TEST_MPILIB
        if utils.get_cime_default_driver() == "nuopc":
            args += " --res f19_g17 "
        else:
            args += " --res f19_g16 "

        args += f" --machine {self.MACHINE.get_machine_name()}"

        self.run_cmd_assert_result(
            "./create_newcase %s" % (args), from_dir=self.SCRIPT_DIR, expected_stat=1
        )
        self.assertFalse(os.path.exists(testdir))

    @classmethod
    def tearDownClass(cls):
        do_teardown = (
            len(cls._do_teardown) > 0
            and sys.exc_info() == (None, None, None)
            and not cls.NO_TEARDOWN
        )
        rmtestroot = True
        for tfile in cls._testdirs:
            if tfile not in cls._do_teardown:
                print("Detected failed test or user request no teardown")
                print("Leaving case directory : %s" % tfile)
                rmtestroot = False
            elif do_teardown:
                try:
                    print("Attempt to remove directory {}".format(tfile))
                    shutil.rmtree(tfile)
                except BaseException:
                    print("Could not remove directory {}".format(tfile))
        if rmtestroot and do_teardown:
            shutil.rmtree(cls._testroot)
