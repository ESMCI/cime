#!/usr/bin/env python3

import os
import time

from CIME import utils
from CIME.case import Case
from CIME.tests import base


def _read_nuopc_clock_attributes(runconfig):
    """Read the CLOCK_attributes section from a NUOPC runconfig."""
    attributes = {}
    in_clock_attributes = False
    with open(runconfig, "r") as fd:
        for line in fd:
            line = line.split("#", 1)[0].strip()
            if line == "CLOCK_attributes::":
                in_clock_attributes = True
            elif in_clock_attributes and line == "::":
                break
            elif in_clock_attributes and "=" in line:
                name, value = line.split("=", 1)
                attributes[name.strip()] = value.strip()
    return attributes


def _expected_nuopc_stop_seconds(case):
    """Calculate the nseconds STOP_N emitted by CMEPS for an nsteps run."""
    ncpl_base_period = case.get_value("NCPL_BASE_PERIOD")
    if ncpl_base_period == "hour":
        base_seconds = 3600
    elif ncpl_base_period == "day":
        base_seconds = 3600 * 24
    elif ncpl_base_period == "year":
        base_seconds = 3600 * 24 * 365
    elif ncpl_base_period == "decade":
        base_seconds = 3600 * 24 * 365 * 10
    else:
        raise AssertionError(
            "Unsupported NCPL_BASE_PERIOD: {}".format(ncpl_base_period)
        )

    min_coupling_seconds = base_seconds
    for comp in case.get_values("COMP_CLASSES"):
        ncpl = case.get_value(comp.upper() + "_NCPL")
        if ncpl is not None:
            min_coupling_seconds = min(min_coupling_seconds, base_seconds // int(ncpl))

    return min_coupling_seconds * case.get_value("STOP_N")


class TestUserConcurrentMods(base.BaseTestCase):
    def test_user_concurrent_mods(self):
        # Put this inside any test that's slow
        if self.FAST_ONLY:
            self.skipTest("Skipping slow test")

        casedir = self._create_test(
            ["--walltime=0:30:00", "TESTRUNUSERXMLCHANGE_Ln3.f19_g16.X"],
            test_id=self._baseline_name,
        )

        with utils.Timeout(3000):
            while True:
                with open(os.path.join(casedir, "CaseStatus"), "r") as fd:
                    self._wait_for_tests(self._baseline_name)
                    contents = fd.read()
                    if contents.count("model execution success") == 2:
                        break

                time.sleep(5)

        rundir = utils.run_cmd_no_fail("./xmlquery RUNDIR --value", from_dir=casedir)
        fake_runs = os.path.join(rundir, "user_xml_change_fake_runs")
        with open(fake_runs, "r") as fd:
            self.assertEqual(len(fd.read().splitlines()), 2)

        if utils.get_cime_default_driver() == "nuopc":
            runconfig = os.path.join(rundir, "nuopc.runconfig")
            clock_attributes = _read_nuopc_clock_attributes(runconfig)
            with Case(casedir, read_only=True) as case:
                self.assertEqual(case.get_value("STOP_OPTION"), "nsteps")
                self.assertEqual(case.get_value("STOP_N"), 6)
                expected_stop_seconds = _expected_nuopc_stop_seconds(case)

            self.assertEqual(clock_attributes["stop_option"], "nseconds")
            self.assertEqual(int(clock_attributes["stop_n"]), expected_stop_seconds)
        else:
            with open(os.path.join(rundir, "drv_in"), "r") as fd:
                contents = fd.read()
                self.assertTrue("stop_n = 6" in contents)
