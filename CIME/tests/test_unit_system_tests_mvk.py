#!/usr/bin/env python3

import os
import json
import unittest
import tempfile
import contextlib
import sysconfig
from pathlib import Path
from unittest import mock
from CIME.tests.utils import chdir

evv4esm = False
try:
    from CIME.SystemTests.mvk import MVK
except:
    unittest.SkipTest("Skipping mvk tests. E3SM feature")
else:
    from CIME.SystemTests.mvk import MVKConfig

    evv4esm = True


def create_complex_case(
    case_name,
    temp_dir,
    run_dir,
    baseline_dir,
    compare_baseline=False,
    mock_evv_output=False,
):
    case = mock.MagicMock()

    side_effect = [
        str(temp_dir),  # CASEROOT
        "MVK.f19_g16.S.docker_gnu",  # CASEBASEID
        "mct",  # COMP_INTERFACE
        "mct",  # COMP_INTERFACE
        False,  # DRV_RESTART_POINTER
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

    run_dir.mkdir(parents=True, exist_ok=True)

    evv_output = run_dir / f"{case_name}.evv" / "index.json"

    evv_output.parent.mkdir(parents=True, exist_ok=True)

    write_evv_output(evv_output, mock_evv_output=mock_evv_output)

    return case


def write_evv_output(evv_output_path, mock_evv_output):
    if mock_evv_output:
        evv_output_data = {
            "Page": {
                "elements": [
                    {
                        "Table": {
                            "data": {
                                "Test status": ["pass"],
                                "Variables analyzed": ["v1", "v2"],
                                "Rejecting": [2],
                                "Critical value": [12],
                            }
                        }
                    }
                ]
            }
        }
    else:
        evv_output_data = {"Page": {"elements": []}}

    with open(evv_output_path, "w") as fd:
        fd.write(json.dumps(evv_output_data))


def create_simple_case(model="e3sm", resubmit=0, generate_baseline=False):
    case = mock.MagicMock()

    case.get_value.side_effect = (
        "/tmp/case",  # CASEROOT
        "MVK.f19_g16.S.docker_gnu",  # CASEBASEID
        "mct",  # COMP_INTERFACE
        False,  # DRV_RESTART_POINTER
        "MVK.f19_g16.S.docker_gnu",  # CASEBASEID
        model,
        resubmit,
        generate_baseline,
    )

    return case


class TestSystemTestsMVK(unittest.TestCase):
    def tearDown(self):
        # reset singleton
        try:
            delattr(MVKConfig, "_instance")
        except:
            pass

    @mock.patch("CIME.SystemTests.mvk.test_mods.find_test_mods")
    @mock.patch("CIME.SystemTests.mvk.evv")
    @unittest.skipUnless(evv4esm, "evv4esm module not found")
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
from CIME.namelist import Namelist
from CIME.SystemTests.mvk import EVV_LIB_DIR

component = "new-comp"
components = ["new-comp", "secondary-comp"]
ninst = 8

def generate_namelist(case, component, i, filename):
    nml = Namelist()

    if component == "new-comp":
        nml.set_variable_value("", "var1", "value1")
    elif component == "secondary-comp":
        nml.set_variable_value("", "var2", "value2")

    nml.write(filename)

def evv_test_config(case, config):
    config["module"] = os.path.join(EVV_LIB_DIR, "extensions", "kso.py")
    config["component"] = "someother-comp"

    return config
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
                    "component": "someother-comp",
                    "ninst": 8,
                    "ref-case": "Baseline",
                    "ref-dir": f"{temp_dir}/baselines/",
                    "test-case": "Test",
                    "test-dir": f"{temp_dir}/run",
                    "var-set": "default",
                }
            }

            module = config["20240515_212034_41b5u2"].pop("module")

            assert (
                f'{sysconfig.get_paths()["purelib"]}/evv4esm/extensions/kso.py'
                == module
            )

            assert config == expected_config

            nml_files = [x for x in os.listdir(temp_dir) if x.startswith("user_nl")]

            assert len(nml_files) == 16

            with open(sorted(nml_files)[0], "r") as fd:
                lines = fd.readlines()

            assert lines == ["var1 = value1\n"]

            with open(sorted(nml_files)[-1], "r") as fd:
                lines = fd.readlines()

            assert lines == ["var2 = value2\n"]

    @mock.patch("CIME.SystemTests.mvk.append_testlog")
    @mock.patch("CIME.SystemTests.mvk.Machines")
    @unittest.skipUnless(evv4esm, "evv4esm module not found")
    def test_update_testlog(self, machines, append_testlog):
        with contextlib.ExitStack() as stack:
            temp_dir = stack.enter_context(tempfile.TemporaryDirectory())

            stack.enter_context(chdir(temp_dir))

            # convert to Path
            temp_dir = Path(temp_dir)
            run_dir = temp_dir / "run"
            baseline_dir = temp_dir / "baselines"

            run_dir.mkdir(parents=True)

            evv_output_path = run_dir / "index.json"

            write_evv_output(evv_output_path, True)

            case_name = "MVK.f19_g16.S.docker_gnu.20240515_212034_41b5u2"  # CASE

            machines.return_value.get_value.return_value = "docker"

            case = create_complex_case(case_name, temp_dir, run_dir, baseline_dir)

            test = MVK(case)

            test.update_testlog("test1", case_name, str(run_dir))

            append_testlog.assert_any_call(
                """BASELINE PASS for test 'test1'.
    Test status: pass; Variables analyzed: v1; Rejecting: 2; Critical value: 12
    EVV results can be viewed at:
        docker/evv/MVK.f19_g16.S.docker_gnu.20240515_212034_41b5u2/index.html""",
                str(temp_dir),
            )

    @mock.patch("CIME.SystemTests.mvk.utils.get_urlroot")
    @mock.patch("CIME.SystemTests.mvk.append_testlog")
    @mock.patch("CIME.SystemTests.mvk.Machines")
    @unittest.skipUnless(evv4esm, "evv4esm module not found")
    def test_update_testlog_urlroot_None(self, machines, append_testlog, get_urlroot):
        with contextlib.ExitStack() as stack:
            temp_dir = stack.enter_context(tempfile.TemporaryDirectory())

            stack.enter_context(chdir(temp_dir))

            # convert to Path
            temp_dir = Path(temp_dir)
            run_dir = temp_dir / "run"
            baseline_dir = temp_dir / "baselines"

            run_dir.mkdir(parents=True)

            evv_output_path = run_dir / "index.json"

            write_evv_output(evv_output_path, True)

            case_name = "MVK.f19_g16.S.docker_gnu.20240515_212034_41b5u2"  # CASE

            machines.return_value.get_value.return_value = "docker"

            get_urlroot.return_value = None

            case = create_complex_case(case_name, temp_dir, run_dir, baseline_dir)

            test = MVK(case)

            test.update_testlog("test1", case_name, str(run_dir))

            print(append_testlog.call_args_list)
            append_testlog.assert_any_call(
                f"""BASELINE PASS for test 'test1'.
    Test status: pass; Variables analyzed: v1; Rejecting: 2; Critical value: 12
    EVV results can be viewed at:
        [{run_dir!s}_URL]/evv/MVK.f19_g16.S.docker_gnu.20240515_212034_41b5u2/index.html""",
                str(temp_dir),
            )

    @mock.patch("CIME.SystemTests.mvk.utils.get_htmlroot")
    @mock.patch("CIME.SystemTests.mvk.append_testlog")
    @mock.patch("CIME.SystemTests.mvk.Machines")
    @unittest.skipUnless(evv4esm, "evv4esm module not found")
    def test_update_testlog_htmlroot(self, machines, append_testlog, get_htmlroot):
        with contextlib.ExitStack() as stack:
            temp_dir = stack.enter_context(tempfile.TemporaryDirectory())

            stack.enter_context(chdir(temp_dir))

            # convert to Path
            temp_dir = Path(temp_dir)
            run_dir = temp_dir / "run"
            baseline_dir = temp_dir / "baselines"

            run_dir.mkdir(parents=True)

            evv_output_path = run_dir / "index.json"

            write_evv_output(evv_output_path, True)

            case_name = "MVK.f19_g16.S.docker_gnu.20240515_212034_41b5u2"  # CASE

            machines.return_value.get_value.return_value = "docker"

            get_htmlroot.return_value = None

            case = create_complex_case(case_name, temp_dir, run_dir, baseline_dir)

            test = MVK(case)

            test.update_testlog("test1", case_name, str(run_dir))

            append_testlog.assert_any_call(
                f"""BASELINE PASS for test 'test1'.
    Test status: pass; Variables analyzed: v1; Rejecting: 2; Critical value: 12
    EVV results can be viewed at:
        {run_dir!s}
    EVV viewing instructions can be found at:         https://github.com/E3SM-Project/E3SM/blob/master/cime/scripts/climate_reproducibility/README.md#test-passfail-and-extended-output""",
                str(temp_dir),
            )

    @mock.patch("CIME.SystemTests.mvk.test_mods.find_test_mods")
    @mock.patch("CIME.SystemTests.mvk.evv")
    @unittest.skipUnless(evv4esm, "evv4esm module not found")
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
                    "test-case": "Default",
                    "test-dir": f"{run_dir}",
                    "ref-case": "Reference",
                    "ref-dir": f"{baseline_dir}/",
                    "var-set": "special",
                    "ninst": 8,
                    "component": "new-comp",
                }
            }

            module = config["20240515_212034_41b5u2"].pop("module")

            assert (
                f'{sysconfig.get_paths()["purelib"]}/evv4esm/extensions/ks.py' == module
            )

            assert config == expected_config

            nml_files = [x for x in os.listdir(temp_dir) if x.startswith("user_nl")]

            assert len(nml_files) == 16

            with open(sorted(nml_files)[0], "r") as fd:
                lines = fd.readlines()

            assert lines == [
                "new_random = .true.\n",
                "pertlim = 1.0e-10\n",
                "seed_clock = .true.\n",
                "seed_custom = 1\n",
            ]

            with open(sorted(nml_files)[-1], "r") as fd:
                lines = fd.readlines()

            assert lines == [
                "new_random = .true.\n",
                "pertlim = 1.0e-10\n",
                "seed_clock = .true.\n",
                "seed_custom = 8\n",
            ]

    @mock.patch("CIME.SystemTests.mvk.case_setup")
    @mock.patch("CIME.SystemTests.mvk.MVK.build_indv")
    @unittest.skipUnless(evv4esm, "evv4esm module not found")
    def test_build_phase(self, build_indv, case_setup):
        with contextlib.ExitStack() as stack:
            temp_dir = stack.enter_context(tempfile.TemporaryDirectory())

            stack.enter_context(chdir(temp_dir))

            # convert to Path
            temp_dir = Path(temp_dir)
            run_dir = temp_dir / "run"
            baseline_dir = temp_dir / "baselines"

            case_name = "MVK.f19_g16.S.docker_gnu.20240515_212034_41b5u2"  # CASE

            case = create_complex_case(
                case_name, temp_dir, run_dir, baseline_dir, True, mock_evv_output=True
            )

            case.get_values.side_effect = (("CPL", "LND"),)

            side_effect = [x for x in case.get_value.side_effect]

            n = 7
            side_effect.insert(n, 8)
            side_effect.insert(n, 16)
            side_effect.insert(n, None)

            case.get_value.side_effect = side_effect

            test = MVK(case)

            test.build_phase(sharedlib_only=True)

            case.set_value.assert_any_call("NTHRDS_CPL", 1)
            case.set_value.assert_any_call("NTASKS_CPL", 480)
            case.set_value.assert_any_call("NTHRDS_LND", 1)
            case.set_value.assert_any_call("NTASKS_LND", 240)
            case.set_value.assert_any_call("NINST_LND", 30)

            case.flush.assert_called()

            case_setup.assert_any_call(case, test_mode=False, reset=True)

    @mock.patch("CIME.SystemTests.mvk.SystemTestsCommon._generate_baseline")
    @mock.patch("CIME.SystemTests.mvk.append_testlog")
    @mock.patch("CIME.SystemTests.mvk.evv")
    @unittest.skipUnless(evv4esm, "evv4esm module not found")
    def test__generate_baseline(self, evv, append_testlog, _generate_baseline):
        with contextlib.ExitStack() as stack:
            temp_dir = stack.enter_context(tempfile.TemporaryDirectory())

            stack.enter_context(chdir(temp_dir))

            # convert to Path
            temp_dir = Path(temp_dir)
            run_dir = temp_dir / "run"
            baseline_dir = temp_dir / "baselines"

            case_name = "MVK.f19_g16.S.docker_gnu.20240515_212034_41b5u2"  # CASE

            case = create_complex_case(
                case_name, temp_dir, run_dir, baseline_dir, True, mock_evv_output=True
            )

            # use original 5 args
            side_effect = [x for x in case.get_value.side_effect][:7]

            side_effect.extend(
                [
                    None,
                    str(baseline_dir),
                    "MVK.f19_g16.S",
                    str(run_dir),
                    "MVK.f19_g16.S",
                    case_name,
                ]
            )

            case.get_value.side_effect = side_effect

            case_baseline_dir = baseline_dir / "MVK.f19_g16.S" / "eam"

            case_baseline_dir.mkdir(parents=True, exist_ok=True)

            (run_dir / "eam").mkdir(parents=True, exist_ok=True)

            (run_dir / "eam" / "test1.nc").touch()
            (run_dir / "eam" / "test2.nc").touch()

            case.get_env.return_value.get_all_hist_files.return_value = (
                "eam/test1.nc",
                "eam/test2.nc",
            )

            test = MVK(case)

            test._generate_baseline()

            files = os.listdir(case_baseline_dir)

            assert sorted(files) == sorted(["test1.nc", "test2.nc"])

            # reset side_effect
            case.get_value.side_effect = side_effect

            test = MVK(case)

            # test baseline_dir already exists
            test._generate_baseline()

            files = os.listdir(case_baseline_dir)

            assert sorted(files) == sorted(["test1.nc", "test2.nc"])

    @mock.patch("CIME.SystemTests.mvk.append_testlog")
    @mock.patch("CIME.SystemTests.mvk.evv")
    @unittest.skipUnless(evv4esm, "evv4esm module not found")
    def test__compare_baseline_resubmit(self, evv, append_testlog):
        with contextlib.ExitStack() as stack:
            temp_dir = stack.enter_context(tempfile.TemporaryDirectory())

            stack.enter_context(chdir(temp_dir))

            # convert to Path
            temp_dir = Path(temp_dir)
            run_dir = temp_dir / "run"
            baseline_dir = temp_dir / "baselines"

            case_name = "MVK.f19_g16.S.docker_gnu.20240515_212034_41b5u2"  # CASE

            case = create_complex_case(
                case_name, temp_dir, run_dir, baseline_dir, True, mock_evv_output=True
            )

            side_effect = [x for x in case.get_value.side_effect][:-8]

            side_effect.extend([1, 1])

            case.get_value.side_effect = side_effect

            test = MVK(case)

            with mock.patch.object(test, "_test_status") as _test_status:
                test._compare_baseline()

            _test_status.set_status.assert_any_call("BASELINE", "PASS")

    @mock.patch("CIME.SystemTests.mvk.append_testlog")
    @mock.patch("CIME.SystemTests.mvk.evv")
    @unittest.skipUnless(evv4esm, "evv4esm module not found")
    def test__compare_baseline(self, evv, append_testlog):
        with contextlib.ExitStack() as stack:
            temp_dir = stack.enter_context(tempfile.TemporaryDirectory())

            stack.enter_context(chdir(temp_dir))

            # convert to Path
            temp_dir = Path(temp_dir)
            run_dir = temp_dir / "run"
            baseline_dir = temp_dir / "baselines"

            case_name = "MVK.f19_g16.S.docker_gnu.20240515_212034_41b5u2"  # CASE

            case = create_complex_case(
                case_name, temp_dir, run_dir, baseline_dir, True, mock_evv_output=True
            )

            test = MVK(case)

            test._compare_baseline()

            with open(run_dir / f"{case_name}.json", "r") as fd:
                config = json.load(fd)

            expected_config = {
                "20240515_212034_41b5u2": {
                    "test-case": "Test",
                    "test-dir": f"{run_dir}",
                    "ref-case": "Baseline",
                    "ref-dir": f"{baseline_dir}/",
                    "var-set": "default",
                    "ninst": 30,
                    "component": "eam",
                }
            }

            module = config["20240515_212034_41b5u2"].pop("module")

            assert (
                f'{sysconfig.get_paths()["purelib"]}/evv4esm/extensions/ks.py' == module
            )

            assert config == expected_config

            expected_comments = f"""BASELINE PASS for test '20240515_212034_41b5u2'.
    Test status: pass; Variables analyzed: v1; Rejecting: 2; Critical value: 12
    EVV results can be viewed at:
        {run_dir}/MVK.f19_g16.S.docker_gnu.20240515_212034_41b5u2.evv
    EVV viewing instructions can be found at:         https://github.com/E3SM-Project/E3SM/blob/master/cime/scripts/climate_reproducibility/README.md#test-passfail-and-extended-output"""

            append_testlog.assert_any_call(
                expected_comments, str(temp_dir)
            ), append_testlog.call_args.args

    @unittest.skipUnless(evv4esm, "evv4esm module not found")
    def test_generate_namelist_multiple_components(self):
        with contextlib.ExitStack() as stack:
            temp_dir = stack.enter_context(tempfile.TemporaryDirectory())

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
                "seed_clock = .true.\n",
                "seed_custom = 1\n",
            ]

    @unittest.skipUnless(evv4esm, "evv4esm module not found")
    def test_generate_namelist(self):
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
                "seed_clock = .true.\n",
                "seed_custom = 1\n",
            ]

    @unittest.skipUnless(evv4esm, "evv4esm module not found")
    def test_compare_baseline(self):
        case = create_simple_case()

        MVK(case)

        case.set_value.assert_any_call("COMPARE_BASELINE", True)

        case = create_simple_case(generate_baseline=True)

        MVK(case)

        case.set_value.assert_any_call("COMPARE_BASELINE", False)

        case = create_simple_case(resubmit=1, generate_baseline=True)

        MVK(case)

        case.set_value.assert_any_call("COMPARE_BASELINE", False)

    @unittest.skipUnless(evv4esm, "evv4esm module not found")
    def test_mvk(self):
        case = create_simple_case()

        test = MVK(case)

        assert test._config.component == "eam"
        assert test._config.components == ["eam"]

        case = create_simple_case("cesm")

        test = MVK(case)

        assert test._config.component == "cam"
        assert test._config.components == ["cam"]
