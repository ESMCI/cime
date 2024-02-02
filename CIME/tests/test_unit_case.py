#!/usr/bin/env python3

import os
import unittest
from unittest import mock
import tempfile

from CIME.case import case_submit
from CIME.case import Case
from CIME import utils as cime_utils


def make_valid_case(path):
    """Make the given path look like a valid case to avoid errors"""
    # Case validity is determined by checking for an env_case.xml file. So put one there
    # to suggest that this directory is a valid case directory. Open in append mode in
    # case the file already exists.
    with open(os.path.join(path, "env_case.xml"), "a"):
        pass


class TestCaseSubmit(unittest.TestCase):
    def test_check_case(self):
        case = mock.MagicMock()
        # get_value arguments TEST, COMP_WAV, COMP_INTERFACE, BUILD_COMPLETE
        case.get_value.side_effect = [False, "", "", True]
        case_submit.check_case(case, chksum=True)

        case.check_all_input_data.assert_called_with(chksum=True)

    def test_check_case_test(self):
        case = mock.MagicMock()
        # get_value arguments TEST, COMP_WAV, COMP_INTERFACE, BUILD_COMPLETE
        case.get_value.side_effect = [True, "", "", True]
        case_submit.check_case(case, chksum=True)

        case.check_all_input_data.assert_not_called()

    @mock.patch("CIME.case.case_submit.lock_file")
    @mock.patch("CIME.case.case_submit.unlock_file")
    @mock.patch("os.path.basename")
    def test__submit(
        self, lock_file, unlock_file, basename
    ):  # pylint: disable=unused-argument
        case = mock.MagicMock()

        case_submit._submit(case, chksum=True)  # pylint: disable=protected-access

        case.check_case.assert_called_with(skip_pnl=False, chksum=True)

    @mock.patch("CIME.case.case_submit._submit")
    @mock.patch("CIME.case.case.Case.initialize_derived_attributes")
    @mock.patch("CIME.case.case.Case.get_value")
    @mock.patch("CIME.case.case.Case.read_xml")
    def test_submit(
        self, read_xml, get_value, init, _submit
    ):  # pylint: disable=unused-argument
        with tempfile.TemporaryDirectory() as tempdir:
            get_value.side_effect = [
                tempdir,
                tempdir,
                tempdir,
                "test",
                tempdir,
                True,
                "baseid",
                None,
                True,
            ]

            make_valid_case(tempdir)
            with Case(tempdir, non_local=True) as case:
                case.submit(chksum=True)

            _submit.assert_called_with(
                case,
                job=None,
                no_batch=False,
                prereq=None,
                allow_fail=False,
                resubmit=False,
                resubmit_immediate=False,
                skip_pnl=False,
                mail_user=None,
                mail_type=None,
                batch_args=None,
                workflow=True,
                chksum=True,
                dryrun=False,
            )


class TestCase(unittest.TestCase):
    def setUp(self):
        self.srcroot = os.path.abspath(cime_utils.get_src_root())
        self.tempdir = tempfile.TemporaryDirectory()

    @mock.patch("CIME.case.case.Case.read_xml")
    def test_fix_sys_argv_quotes(self, read_xml):
        input_data = ["./xmlquery", "--val", "PIO"]
        expected_data = ["./xmlquery", "--val", "PIO"]

        with tempfile.TemporaryDirectory() as tempdir:
            make_valid_case(tempdir)

            with Case(tempdir) as case:
                output_data = case.fix_sys_argv_quotes(input_data)

        assert output_data == expected_data

    @mock.patch("CIME.case.case.Case.read_xml")
    def test_fix_sys_argv_quotes_incomplete(self, read_xml):
        input_data = ["./xmlquery", "--val"]
        expected_data = ["./xmlquery", "--val"]

        with tempfile.TemporaryDirectory() as tempdir:
            make_valid_case(tempdir)

            with Case(tempdir) as case:
                output_data = case.fix_sys_argv_quotes(input_data)

        assert output_data == expected_data

    @mock.patch("CIME.case.case.Case.read_xml")
    def test_fix_sys_argv_quotes_val(self, read_xml):
        input_data = ["./xmlquery", "--val", "-test"]
        expected_data = ["./xmlquery", "--val", "-test"]

        with tempfile.TemporaryDirectory() as tempdir:
            make_valid_case(tempdir)

            with Case(tempdir) as case:
                output_data = case.fix_sys_argv_quotes(input_data)

        assert output_data == expected_data

    @mock.patch("CIME.case.case.Case.read_xml")
    def test_fix_sys_argv_quotes_val_quoted(self, read_xml):
        input_data = ["./xmlquery", "--val", " -nlev 267 "]
        expected_data = ["./xmlquery", "--val", '" -nlev 267 "']

        with tempfile.TemporaryDirectory() as tempdir:
            make_valid_case(tempdir)

            with Case(tempdir) as case:
                output_data = case.fix_sys_argv_quotes(input_data)

        assert output_data == expected_data

    @mock.patch("CIME.case.case.Case.read_xml")
    def test_fix_sys_argv_quotes_kv(self, read_xml):
        input_data = ["./xmlquery", "CAM_CONFIG_OPTS= -nlev 267", "OTHER_OPTS=-test"]
        expected_data = [
            "./xmlquery",
            'CAM_CONFIG_OPTS=" -nlev 267"',
            "OTHER_OPTS=-test",
        ]

        with tempfile.TemporaryDirectory() as tempdir:
            make_valid_case(tempdir)

            with Case(tempdir) as case:
                output_data = case.fix_sys_argv_quotes(input_data)

        assert output_data == expected_data

    @mock.patch("CIME.case.case.Case.read_xml")
    @mock.patch("sys.argv", ["/src/create_newcase", "--machine", "docker"])
    @mock.patch("time.strftime", return_value="00:00:00")
    @mock.patch("socket.getfqdn", return_value="host1")
    @mock.patch("getpass.getuser", side_effect=["root", "root", "johndoe"])
    def test_new_hash(
        self, getuser, getfqdn, strftime, read_xml
    ):  # pylint: disable=unused-argument
        with self.tempdir as tempdir:
            make_valid_case(tempdir)
            with Case(tempdir) as case:
                expected = (
                    "134a939f62115fb44bf08a46bfb2bd13426833b5c8848cf7c4884af7af05b91a"
                )

                # Check idempotency
                for _ in range(2):
                    value = case.new_hash()

                    self.assertTrue(
                        value == expected, "{} != {}".format(value, expected)
                    )

                expected = (
                    "bb59f1c473ac07e9dd30bfab153c0530a777f89280b716cf42e6fe2f49811a6e"
                )

                value = case.new_hash()

                self.assertTrue(value == expected, "{} != {}".format(value, expected))

    @mock.patch("CIME.case.case.Case.read_xml")
    @mock.patch("sys.argv", ["/src/create_newcase", "--machine", "docker"])
    @mock.patch("time.strftime", return_value="00:00:00")
    @mock.patch("CIME.case.case.lock_file")
    @mock.patch("CIME.case.case.Case.set_lookup_value")
    @mock.patch("CIME.case.case.Case.apply_user_mods")
    @mock.patch("CIME.case.case.Case.create_caseroot")
    @mock.patch("CIME.case.case.Case.configure")
    @mock.patch("socket.getfqdn", return_value="host1")
    @mock.patch("getpass.getuser", return_value="root")
    @mock.patch.dict(os.environ, {"CIME_MODEL": "cesm"})
    def test_copy(
        self,
        getuser,
        getfqdn,
        configure,
        create_caseroot,  # pylint: disable=unused-argument
        apply_user_mods,
        set_lookup_value,
        lock_file,
        strftime,  # pylint: disable=unused-argument
        read_xml,
    ):  # pylint: disable=unused-argument
        expected_first_hash = (
            "134a939f62115fb44bf08a46bfb2bd13426833b5c8848cf7c4884af7af05b91a"
        )
        expected_second_hash = (
            "3561339a49daab999e3c4ea2f03a9c6acc33296a5bc35f1bfb82e7b5e10bdf38"
        )

        with self.tempdir as tempdir:
            caseroot = os.path.join(tempdir, "test1")
            with Case(caseroot, read_only=False) as case:
                case.create(
                    "test1",
                    self.srcroot,
                    "A",
                    "f19_g16_rx1",
                    machine_name="perlmutter",
                )

                # Check that they're all called
                configure.assert_called_with(
                    "A",
                    "f19_g16_rx1",
                    machine_name="perlmutter",
                    project=None,
                    pecount=None,
                    compiler=None,
                    mpilib=None,
                    pesfile=None,
                    gridfile=None,
                    multi_driver=False,
                    ninst=1,
                    test=False,
                    walltime=None,
                    queue=None,
                    output_root=None,
                    run_unsupported=False,
                    answer=None,
                    input_dir=None,
                    driver=None,
                    workflowid="default",
                    non_local=False,
                    extra_machines_dir=None,
                    case_group=None,
                    ngpus_per_node=0,
                    gpu_type=None,
                    gpu_offload=None,
                )
                create_caseroot.assert_called()
                apply_user_mods.assert_called()
                lock_file.assert_called()

                set_lookup_value.assert_called_with("CASE_HASH", expected_first_hash)

                strftime.return_value = "10:00:00"
                with mock.patch(
                    "CIME.case.case.Case.set_value"
                ) as set_value, mock.patch("sys.argv", ["/src/create_clone"]):
                    case.copy("test2", "{}_2".format(tempdir))

                    set_value.assert_called_with("CASE_HASH", expected_second_hash)

    @mock.patch("CIME.case.case.Case.read_xml")
    @mock.patch("sys.argv", ["/src/create_newcase", "--machine", "docker"])
    @mock.patch("time.strftime", return_value="00:00:00")
    @mock.patch("CIME.case.case.lock_file")
    @mock.patch("CIME.case.case.Case.set_lookup_value")
    @mock.patch("CIME.case.case.Case.apply_user_mods")
    @mock.patch("CIME.case.case.Case.create_caseroot")
    @mock.patch("CIME.case.case.Case.configure")
    @mock.patch("socket.getfqdn", return_value="host1")
    @mock.patch("getpass.getuser", return_value="root")
    @mock.patch.dict(os.environ, {"CIME_MODEL": "cesm"})
    def test_create(
        self,
        get_user,
        getfqdn,
        configure,
        create_caseroot,  # pylint: disable=unused-argument
        apply_user_mods,
        set_lookup_value,
        lock_file,
        strftime,  # pylint: disable=unused-argument
        read_xml,
    ):  # pylint: disable=unused-argument
        with self.tempdir as tempdir:
            caseroot = os.path.join(tempdir, "test1")
            with Case(caseroot, read_only=False) as case:
                case.create(
                    "test1",
                    self.srcroot,
                    "A",
                    "f19_g16_rx1",
                    machine_name="perlmutter",
                )

                # Check that they're all called
                configure.assert_called_with(
                    "A",
                    "f19_g16_rx1",
                    machine_name="perlmutter",
                    project=None,
                    pecount=None,
                    compiler=None,
                    mpilib=None,
                    pesfile=None,
                    gridfile=None,
                    multi_driver=False,
                    ninst=1,
                    test=False,
                    walltime=None,
                    queue=None,
                    output_root=None,
                    run_unsupported=False,
                    answer=None,
                    input_dir=None,
                    driver=None,
                    workflowid="default",
                    non_local=False,
                    extra_machines_dir=None,
                    case_group=None,
                    ngpus_per_node=0,
                    gpu_type=None,
                    gpu_offload=None,
                )
                create_caseroot.assert_called()
                apply_user_mods.assert_called()
                lock_file.assert_called()

                set_lookup_value.assert_called_with(
                    "CASE_HASH",
                    "134a939f62115fb44bf08a46bfb2bd13426833b5c8848cf7c4884af7af05b91a",
                )


class TestCase_RecordCmd(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()

    def assert_calls_match(self, calls, expected):
        self.assertTrue(len(calls) == len(expected), calls)

        for x, y in zip(calls, expected):
            self.assertTrue(x == y, calls)

    @mock.patch("CIME.case.case.Case.__init__", return_value=None)
    @mock.patch("CIME.case.case.Case.flush")
    @mock.patch("CIME.case.case.Case.get_value")
    @mock.patch("CIME.case.case.open", mock.mock_open())
    @mock.patch("time.strftime", return_value="00:00:00")
    @mock.patch("sys.argv", ["/src/create_newcase"])
    def test_error(
        self, strftime, get_value, flush, init
    ):  # pylint: disable=unused-argument
        Case._force_read_only = False  # pylint: disable=protected-access

        with self.tempdir as tempdir, mock.patch(
            "CIME.case.case.open", mock.mock_open()
        ) as m:
            m.side_effect = PermissionError()

            with Case(tempdir) as case:
                get_value.side_effect = [tempdir, "/src"]

                # We didn't need to make tempdir look like a valid case for the Case
                # constructor because we mock that constructor, but we *do* need to make
                # it look like a valid case for record_cmd.
                make_valid_case(tempdir)
                case.record_cmd()

    @mock.patch("CIME.case.case.Case.__init__", return_value=None)
    @mock.patch("CIME.case.case.Case.flush")
    @mock.patch("CIME.case.case.Case.get_value")
    @mock.patch("CIME.case.case.open", mock.mock_open())
    @mock.patch("time.strftime", return_value="00:00:00")
    @mock.patch("sys.argv", ["/src/create_newcase"])
    def test_init(
        self, strftime, get_value, flush, init
    ):  # pylint: disable=unused-argument
        Case._force_read_only = False  # pylint: disable=protected-access

        mocked_open = mock.mock_open()

        with self.tempdir as tempdir, mock.patch("CIME.case.case.open", mocked_open):
            with Case(tempdir) as case:
                get_value.side_effect = [tempdir, "/src"]

                case.record_cmd(init=True)

        mocked_open.assert_called_with(f"{tempdir}/replay.sh", "a")

        handle = mocked_open()

        handle.writelines.assert_called_with(
            [
                "#!/bin/bash\n\n",
                "set -e\n\n",
                "# Created 00:00:00\n\n",
                'CASEDIR="{}"\n\n'.format(tempdir),
                "/src/create_newcase\n\n",
                'cd "${CASEDIR}"\n\n',
            ]
        )

    @mock.patch("CIME.case.case.Case.__init__", return_value=None)
    @mock.patch("CIME.case.case.Case.flush")
    @mock.patch("CIME.case.case.Case.get_value")
    @mock.patch("CIME.case.case.open", mock.mock_open())
    @mock.patch("time.strftime", return_value="00:00:00")
    @mock.patch("sys.argv", ["/src/scripts/create_newcase"])
    def test_sub_relative(
        self, strftime, get_value, flush, init
    ):  # pylint: disable=unused-argument
        Case._force_read_only = False  # pylint: disable=protected-access

        mocked_open = mock.mock_open()

        with self.tempdir as tempdir, mock.patch("CIME.case.case.open", mocked_open):
            with Case(tempdir) as case:
                get_value.side_effect = [tempdir, "/src"]

                case.record_cmd(init=True)

        expected = [
            "#!/bin/bash\n\n",
            "set -e\n\n",
            "# Created 00:00:00\n\n",
            'CASEDIR="{}"\n\n'.format(tempdir),
            "/src/scripts/create_newcase\n\n",
            'cd "${CASEDIR}"\n\n',
        ]

        handle = mocked_open()
        handle.writelines.assert_called_with(expected)

    @mock.patch("CIME.case.case.Case.__init__", return_value=None)
    @mock.patch("CIME.case.case.Case.flush")
    @mock.patch("CIME.case.case.Case.get_value")
    def test_cmd_arg(self, get_value, flush, init):  # pylint: disable=unused-argument
        Case._force_read_only = False  # pylint: disable=protected-access

        mocked_open = mock.mock_open()

        with self.tempdir as tempdir, mock.patch("CIME.case.case.open", mocked_open):
            with Case(tempdir) as case:
                get_value.side_effect = [
                    tempdir,
                    "/src",
                ]

                # We didn't need to make tempdir look like a valid case for the Case
                # constructor because we mock that constructor, but we *do* need to make
                # it look like a valid case for record_cmd.
                make_valid_case(tempdir)
                case.record_cmd(["/some/custom/command", "arg1"])

        expected = [
            "/some/custom/command arg1\n\n",
        ]

        handle = mocked_open()
        handle.writelines.assert_called_with(expected)


if __name__ == "__main__":
    unittest.main()
