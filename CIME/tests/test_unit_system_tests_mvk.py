#!/usr/bin/env python3

import os
import json
import unittest
import tempfile
import contextlib
from pathlib import Path
from unittest import mock

from CIME.SystemTests.mvk import MVK
from CIME.SystemTests.mvk import MVKConfig
from CIME.tests.utils import chdir


def create_complex_case(
    case_name, temp_dir, run_dir, baseline_dir, compare_baseline=False
):
    case = mock.MagicMock()

    side_effect = [
        str(temp_dir),  # CASEROOT
        "MVK.f19_g16.S.docker_gnu",  # CASEBASEID
        "mct",  # COMP_INTERFACE
        "mct",  # COMP_INTERFACE
    ]

    # single extra call for _compare_baseline
    if compare_baseline:
        side_effect.append("e3sm")  # MODEL

    side_effect.extend(
        [
            0,  # RESUBMIT
            False,  # GENERATE_BASELINE
            0,  # RESUBMIT
            str(run_dir),  # RUNDIR
            case_name,  # CASE
            str(baseline_dir),  # BASELINE_ROOT
            "",  # BASECMP_CASE
            "docker",  # MACH
        ]
    )

    case.get_value.side_effect = side_effect

    run_dir.mkdir(parents=True)

    evv_output = run_dir / f"{case_name}.evv" / "index.json"

    evv_output.parent.mkdir(parents=True)

    with open(evv_output, "w") as fd:
        fd.write(json.dumps({"Page": {"elements": []}}))

    return case


def create_simple_case():
    case = mock.MagicMock()

    case.get_value.side_effect = (
        "/tmp/case",  # CASEROOT
        "MVK.f19_g16.S.docker_gnu",  # CASEBASEID
        "mct",  # COMP_INTERFACE
        "MVK.f19_g16.S.docker_gnu",  # CASEBASEID
        "e3sm",  # MODEL
        0,  # RESUBMIT
        False,  # GENERATE_BASELINE
    )

    return case


class TestSystemTestsMVK(unittest.TestCase):
    def tearDown(self):
        # reset singleton
        delattr(MVKConfig, "_instance")

    @mock.patch("CIME.SystemTests.mvk.find_test_mods")
    @mock.patch("CIME.SystemTests.mvk.evv")
    def test_testmod_complex(self, evv, find_test_mods):
        with contextlib.ExitStack() as stack:
            temp_dir = stack.enter_context(tempfile.TemporaryDirectory())
            print(temp_dir)

            stack.enter_context(chdir(temp_dir))

            # convert to Path
            temp_dir = Path(temp_dir)
            run_dir = temp_dir / "run"
            baseline_dir = temp_dir / "baselines"
            testmods_dir = temp_dir / "testmods" / "eam"

            testmods_dir.mkdir(parents=True)

            find_test_mods.return_value = [str(testmods_dir)]

            with open(testmods_dir / "params.py", "w") as fd:
                fd.write(
                    """
import os

component = "new-comp"
components = ["new-comp", "secondary-comp"]
ninst = 8

def write_inst_nml(case, set_nml_variable, component, iinst):
    if component == "new-comp":
        set_nml_variable("var1", "value1")
    elif component == "secondary-comp":
        set_nml_variable("var2", "value2")

def test_config(case, run_dir, base_dir, evv_lib_dir):
    return {
        "module": os.path.join(evv_lib_dir, "extensions", "kso.py"),
        "component": "someother-comp"
    }
                         """
                )

            case_name = "MVK.f19_g16.S.docker_gnu.20240515_212034_41b5u2"  # CASE

            case = create_complex_case(case_name, temp_dir, run_dir, baseline_dir)
            test = MVK(case)

            stack.enter_context(mock.patch.object(test, "build_indv"))

            test.build_phase(False, True)
            test._compare_baseline()

            with open(run_dir / f"{case_name}.json", "r") as fd:
                config = json.load(fd)

            expected_config = {
                "20240515_212034_41b5u2": {
                    "module": "/opt/conda/lib/python3.10/site-packages/evv4esm/extensions/kso.py",
                    "component": "someother-comp",
                }
            }

            assert config == expected_config

            nml_files = [x for x in os.listdir(temp_dir) if x.startswith("user_nl")]

            assert len(nml_files) == 16

            with open(sorted(nml_files)[0], "r") as fd:
                lines = fd.readlines()

            assert lines == ["var1 = value1\n"]

            with open(sorted(nml_files)[-1], "r") as fd:
                lines = fd.readlines()

            assert lines == ["var2 = value2\n"]

    @mock.patch("CIME.SystemTests.mvk.find_test_mods")
    @mock.patch("CIME.SystemTests.mvk.evv")
    def test_testmod_simple(self, evv, find_test_mods):
        with contextlib.ExitStack() as stack:
            temp_dir = stack.enter_context(tempfile.TemporaryDirectory())

            stack.enter_context(chdir(temp_dir))

            # convert to Path
            temp_dir = Path(temp_dir)
            run_dir = temp_dir / "run"
            baseline_dir = temp_dir / "baselines"
            testmods_dir = temp_dir / "testmods" / "eam"

            testmods_dir.mkdir(parents=True)

            find_test_mods.return_value = [str(testmods_dir)]

            with open(testmods_dir / "params.py", "w") as fd:
                fd.write(
                    """
component = "new-comp"
components = ["new-comp", "second-comp"]
ninst = 8
critical = 32
var_set = "special"
ref_case = "Reference"
test_case = "Default"
                         """
                )

            case_name = "MVK.f19_g16.S.docker_gnu.20240515_212034_41b5u2"  # CASE

            case = create_complex_case(case_name, temp_dir, run_dir, baseline_dir)
            test = MVK(case)

            stack.enter_context(mock.patch.object(test, "build_indv"))

            test.build_phase(False, True)
            test._compare_baseline()

            with open(run_dir / f"{case_name}.json", "r") as fd:
                config = json.load(fd)

            expected_config = {
                "20240515_212034_41b5u2": {
                    "module": "/opt/conda/lib/python3.10/site-packages/evv4esm/extensions/ks.py",
                    "test-case": "Default",
                    "test-dir": f"{run_dir}",
                    "ref-case": "Reference",
                    "ref-dir": f"{baseline_dir}/",
                    "var-set": "special",
                    "ninst": 8,
                    "critical": 32,
                    "component": "new-comp",
                }
            }

            assert config == expected_config

            nml_files = [x for x in os.listdir(temp_dir) if x.startswith("user_nl")]

            assert len(nml_files) == 16

            with open(sorted(nml_files)[0], "r") as fd:
                lines = fd.readlines()

            assert lines == [
                "new_random = .true.\n",
                "pertlim = 1.0e-10\n",
                "seed_custom = 1\n",
                "seed_clock = .true.\n",
            ]

            with open(sorted(nml_files)[-1], "r") as fd:
                lines = fd.readlines()

            assert lines == [
                "new_random = .true.\n",
                "pertlim = 1.0e-10\n",
                "seed_custom = 8\n",
                "seed_clock = .true.\n",
            ]

    @mock.patch("CIME.SystemTests.mvk.evv")
    def test__compare_baseline(self, evv):
        with contextlib.ExitStack() as stack:
            temp_dir = stack.enter_context(tempfile.TemporaryDirectory())

            stack.enter_context(chdir(temp_dir))

            # convert to Path
            temp_dir = Path(temp_dir)
            run_dir = temp_dir / "run"
            baseline_dir = temp_dir / "baselines"

            case_name = "MVK.f19_g16.S.docker_gnu.20240515_212034_41b5u2"  # CASE

            case = create_complex_case(case_name, temp_dir, run_dir, baseline_dir, True)

            test = MVK(case)

            test._compare_baseline()

            with open(run_dir / f"{case_name}.json", "r") as fd:
                config = json.load(fd)

            expected_config = {
                "20240515_212034_41b5u2": {
                    "module": "/opt/conda/lib/python3.10/site-packages/evv4esm/extensions/ks.py",
                    "test-case": "Test",
                    "test-dir": f"{run_dir}",
                    "ref-case": "Baseline",
                    "ref-dir": f"{baseline_dir}/",
                    "var-set": "default",
                    "ninst": 30,
                    "critical": 13,
                    "component": "eam",
                }
            }

            assert config == expected_config

    def test_write_inst_nml_multiple_components(self):
        with contextlib.ExitStack() as stack:
            temp_dir = stack.enter_context(tempfile.TemporaryDirectory())

            print(temp_dir)

            stack.enter_context(chdir(temp_dir))

            case = create_simple_case()

            test = MVK(case)

            stack.enter_context(mock.patch.object(test, "build_indv"))

            test._config.components = ["eam", "elm"]

            test.build_phase(False, True)

            nml_files = os.listdir(temp_dir)

            assert len(nml_files) == 60

            with open(sorted(nml_files)[0], "r") as fd:
                lines = fd.readlines()

            assert lines == [
                "new_random = .true.\n",
                "pertlim = 1.0e-10\n",
                "seed_custom = 1\n",
                "seed_clock = .true.\n",
            ]

    def test_write_inst_nml(self):
        with contextlib.ExitStack() as stack:
            temp_dir = stack.enter_context(tempfile.TemporaryDirectory())

            stack.enter_context(chdir(temp_dir))

            case = create_simple_case()

            test = MVK(case)

            stack.enter_context(mock.patch.object(test, "build_indv"))

            test.build_phase(False, True)

            nml_files = os.listdir(temp_dir)

            assert len(nml_files) == 30

            with open(sorted(nml_files)[0], "r") as fd:
                lines = fd.readlines()

            assert lines == [
                "new_random = .true.\n",
                "pertlim = 1.0e-10\n",
                "seed_custom = 1\n",
                "seed_clock = .true.\n",
            ]

    def test_mvk(self):
        case = create_simple_case()

        test = MVK(case)

        assert test._config.component == "eam"
        assert test._config.components == ["eam"]
