#!/usr/bin/env python3

import glob
import re
import os
import stat

from CIME import utils
from CIME.tests import base


class TestBlessTestResults(base.BaseTestCase):
    def setUp(self):
        super().setUp()

        # Set a restrictive umask so we can test that SharedAreas used for
        # recording baselines are working
        restrictive_mask = 0o027
        self._orig_umask = os.umask(restrictive_mask)

    def tearDown(self):
        super().tearDown()

        if "TESTRUNDIFF_ALTERNATE" in os.environ:
            del os.environ["TESTRUNDIFF_ALTERNATE"]

        os.umask(self._orig_umask)

    def test_bless_test_results(self):
        if self.NO_FORTRAN_RUN:
            self.skipTest("Skipping fortran test")
        # Test resubmit scenario if Machine has a batch system
        if self.MACHINE.has_batch_system():
            test_names = [
                "TESTRUNDIFFRESUBMIT_Mmpi-serial.f19_g16_rx1.A",
                "TESTRUNDIFF_Mmpi-serial.f19_g16_rx1.A",
            ]
        else:
            test_names = ["TESTRUNDIFF_P1.f19_g16_rx1.A"]

        # Generate some baselines
        for test_name in test_names:
            if self._config.create_test_flag_mode == "e3sm":
                genargs = ["-g", "-o", "-b", self._baseline_name, test_name]
                compargs = ["-c", "-b", self._baseline_name, test_name]
            else:
                genargs = [
                    "-g",
                    self._baseline_name,
                    "-o",
                    test_name,
                    "--baseline-root ",
                    self._baseline_area,
                ]
                compargs = [
                    "-c",
                    self._baseline_name,
                    test_name,
                    "--baseline-root ",
                    self._baseline_area,
                ]

            self._create_test(genargs)
            # Hist compare should pass
            self._create_test(compargs)
            # Change behavior
            os.environ["TESTRUNDIFF_ALTERNATE"] = "True"

            # Hist compare should now fail
            test_id = "%s-%s" % (self._baseline_name, utils.get_timestamp())
            self._create_test(compargs, test_id=test_id, run_errors=True)

            # compare_test_results should detect the fail
            cpr_cmd = "{}/compare_test_results --test-root {} -t {} ".format(
                self.TOOLS_DIR, self._testroot, test_id
            )
            output = self.run_cmd_assert_result(
                cpr_cmd, expected_stat=utils.TESTS_FAILED_ERR_CODE
            )

            # use regex
            expected_pattern = re.compile(r"FAIL %s[^\s]* BASELINE" % test_name)
            the_match = expected_pattern.search(output)
            self.assertNotEqual(
                the_match,
                None,
                msg="Cmd '%s' failed to display failed test %s in output:\n%s"
                % (cpr_cmd, test_name, output),
            )
            # Bless
            utils.run_cmd_no_fail(
                "{}/bless_test_results --test-root {} --hist-only --force -t {}".format(
                    self.TOOLS_DIR, self._testroot, test_id
                )
            )
            # Hist compare should now pass again
            self._create_test(compargs)
            self.verify_perms(self._baseline_area)
            if "TESTRUNDIFF_ALTERNATE" in os.environ:
                del os.environ["TESTRUNDIFF_ALTERNATE"]

    def test_rebless_namelist(self):
        # Generate some namelist baselines
        if self.NO_FORTRAN_RUN:
            self.skipTest("Skipping fortran test")
        test_to_change = "TESTRUNPASS_P1.f19_g16_rx1.A"
        if self._config.create_test_flag_mode == "e3sm":
            genargs = ["-g", "-o", "-b", self._baseline_name, "cime_test_only_pass"]
            compargs = ["-c", "-b", self._baseline_name, "cime_test_only_pass"]
        else:
            genargs = ["-g", self._baseline_name, "-o", "cime_test_only_pass"]
            compargs = ["-c", self._baseline_name, "cime_test_only_pass"]

        self._create_test(genargs)

        # Basic namelist compare
        test_id = "%s-%s" % (self._baseline_name, utils.get_timestamp())
        cases = self._create_test(compargs, test_id=test_id)
        casedir = self.get_casedir(test_to_change, cases)

        # Check standalone case.cmpgen_namelists
        self.run_cmd_assert_result("./case.cmpgen_namelists", from_dir=casedir)

        # compare_test_results should pass
        cpr_cmd = "{}/compare_test_results --test-root {} -n -t {} ".format(
            self.TOOLS_DIR, self._testroot, test_id
        )
        output = self.run_cmd_assert_result(cpr_cmd)

        # use regex
        expected_pattern = re.compile(r"PASS %s[^\s]* NLCOMP" % test_to_change)
        the_match = expected_pattern.search(output)
        msg = f"Cmd {cpr_cmd} failed to display passed test in output:\n{output}"
        self.assertNotEqual(
            the_match,
            None,
            msg=msg,
        )

        # Modify namelist
        fake_nl = """
 &fake_nml
   fake_item = 'fake'
   fake = .true.
/"""
        baseline_area = self._baseline_area
        baseline_glob = glob.glob(
            os.path.join(baseline_area, self._baseline_name, "TEST*")
        )
        self.assertEqual(
            len(baseline_glob),
            3,
            msg="Expected three matches, got:\n%s" % "\n".join(baseline_glob),
        )

        for baseline_dir in baseline_glob:
            nl_path = os.path.join(baseline_dir, "CaseDocs", "datm_in")
            self.assertTrue(os.path.isfile(nl_path), msg="Missing file %s" % nl_path)

            os.chmod(nl_path, stat.S_IRUSR | stat.S_IWUSR)
            with open(nl_path, "a") as nl_file:
                nl_file.write(fake_nl)

        # Basic namelist compare should now fail
        test_id = "%s-%s" % (self._baseline_name, utils.get_timestamp())
        self._create_test(compargs, test_id=test_id, run_errors=True)
        casedir = self.get_casedir(test_to_change, cases)

        # Unless namelists are explicitly ignored
        test_id2 = "%s-%s" % (self._baseline_name, utils.get_timestamp())
        self._create_test(compargs + ["--ignore-namelists"], test_id=test_id2)

        self.run_cmd_assert_result(
            "./case.cmpgen_namelists", from_dir=casedir, expected_stat=100
        )

        # preview namelists should work
        self.run_cmd_assert_result("./preview_namelists", from_dir=casedir)

        # This should still fail
        self.run_cmd_assert_result(
            "./case.cmpgen_namelists", from_dir=casedir, expected_stat=100
        )

        # compare_test_results should fail
        cpr_cmd = "{}/compare_test_results --test-root {} -n -t {} ".format(
            self.TOOLS_DIR, self._testroot, test_id
        )
        output = self.run_cmd_assert_result(
            cpr_cmd, expected_stat=utils.TESTS_FAILED_ERR_CODE
        )

        # use regex
        expected_pattern = re.compile(r"FAIL %s[^\s]* NLCOMP" % test_to_change)
        the_match = expected_pattern.search(output)
        self.assertNotEqual(
            the_match,
            None,
            msg="Cmd '%s' failed to display passed test in output:\n%s"
            % (cpr_cmd, output),
        )

        # Bless
        new_test_id = "%s-%s" % (self._baseline_name, utils.get_timestamp())
        utils.run_cmd_no_fail(
            "{}/bless_test_results --test-root {} -n --force -t {} --new-test-root={} --new-test-id={}".format(
                self.TOOLS_DIR, self._testroot, test_id, self._testroot, new_test_id
            )
        )

        # Basic namelist compare should now pass again
        self._create_test(compargs)

        self.verify_perms(self._baseline_area)
