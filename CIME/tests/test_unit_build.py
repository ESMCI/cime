#!/usr/bin/env python3

import os
import unittest
from unittest import mock
from pathlib import Path

from CIME import build
from CIME.tests.utils import mock_case


class TestBuild(unittest.TestCase):
    @mock_case()
    @mock.patch("CIME.build.uses_kokkos")
    @mock.patch("CIME.build.generate_makefile_macro")  # no need for makefile macros
    @mock.patch(
        "CIME.build.Files"
    )  # used to check expected behavior by checking libs variable
    def test__build_libraries_case_support_libraries(
        self, Files, _, uses_kokkos, case, caseroot, **kwargs
    ):
        uses_kokkos.return_value = False

        exeroot = os.path.join(caseroot, "bld")
        cimeroot = os.getcwd()
        libroot = os.path.join(caseroot, "libs")
        buildlist = []
        complist = []

        case.get_values = mock.MagicMock(
            side_effect=[
                ["gptl", "mct"],  # CASE_SUPPORT_LIBRARIES
            ]
        )

        case.get_value = mock.MagicMock(
            side_effect=[
                "",  # SHAREDLIBROOT
                False,  # TEST
            ]
        )

        build._build_libraries(
            case,
            exeroot,
            "shared",
            caseroot,
            cimeroot,
            libroot,
            "unique",
            "gnu",
            buildlist,
            "mct",
            complist,
        )

        get_value = Files.return_value.get_value

        expected = [
            mock.call("BUILD_LIB_FILE", {"lib": "gptl"}, attribute_required=True),
            mock.call("BUILD_LIB_FILE", {"lib": "mct"}, attribute_required=True),
        ]

        assert get_value.call_args_list == expected, get_value.call_args_list

    @mock.patch.dict(os.environ, {"UFS_DRIVER": "nems"})
    @mock_case()
    @mock.patch("CIME.build.uses_kokkos")
    @mock.patch("CIME.build.generate_makefile_macro")  # no need for makefile macros
    @mock.patch(
        "CIME.build.Files"
    )  # used to check expected behavior by checking libs variable
    def test__build_libraries_ufs_driver(
        self, Files, _, uses_kokkos, case, caseroot, **kwargs
    ):
        uses_kokkos.return_value = False

        exeroot = os.path.join(caseroot, "bld")
        cimeroot = os.getcwd()
        libroot = os.path.join(caseroot, "libs")
        buildlist = ["cpl"]
        complist = []

        case.get_values = mock.MagicMock(
            side_effect=[
                [],  # CASE_SUPPORT_LIBRARIES
            ]
        )

        case.get_value = mock.MagicMock(
            side_effect=[
                "openmpi",  # MPILIB
                "e3sm",  # MODEL
                "e3sm",  # MODEL
                "",  # COMP_OCN
                "",  # CAM_DYCORE
                "",  # SHAREDLIBROOT
                False,  # TEST
            ]
        )

        build._build_libraries(
            case,
            exeroot,
            "shared",
            caseroot,
            cimeroot,
            libroot,
            "unique",
            "gnu",
            buildlist,
            "mct",
            complist,
        )

        get_value = Files.return_value.get_value

        expected = [
            mock.call("BUILD_LIB_FILE", {"lib": "FTorch"}, attribute_required=True),
        ]

        assert get_value.call_args_list == expected, get_value.call_args_list

    @mock_case()
    @mock.patch("CIME.build.uses_kokkos")
    @mock.patch("CIME.build.generate_makefile_macro")  # no need for makefile macros
    @mock.patch(
        "CIME.build.Files"
    )  # used to check expected behavior by checking libs variable
    def test__build_libraries_cesm_model(
        self, Files, _, uses_kokkos, case, caseroot, **kwargs
    ):
        uses_kokkos.return_value = False

        exeroot = os.path.join(caseroot, "bld")
        cimeroot = os.getcwd()
        libroot = os.path.join(caseroot, "libs")
        buildlist = []
        complist = []

        case.get_values = mock.MagicMock(
            side_effect=[
                [],  # CASE_SUPPORT_LIBRARIES
            ]
        )

        case.get_value = mock.MagicMock(
            side_effect=[
                "openmpi",  # MPILIB
                "cesm",  # MODEL
                "cesm",  # MODEL
                "",  # COMP_OCN
                "",  # CAM_DYCORE
                "",  # SHAREDLIBROOT
                False,  # TEST
            ]
        )

        build._build_libraries(
            case,
            exeroot,
            "shared",
            caseroot,
            cimeroot,
            libroot,
            "unique",
            "gnu",
            buildlist,
            "mct",
            complist,
        )

        get_value = Files.return_value.get_value

        expected = [
            mock.call("BUILD_LIB_FILE", {"lib": "gptl"}, attribute_required=True),
            mock.call("BUILD_LIB_FILE", {"lib": "pio"}, attribute_required=True),
            mock.call("BUILD_LIB_FILE", {"lib": "csm_share"}, attribute_required=True),
            mock.call("BUILD_LIB_FILE", {"lib": "FTorch"}, attribute_required=True),
        ]

        assert get_value.call_args_list == expected, get_value.call_args_list

    @mock_case()
    @mock.patch("CIME.build.uses_kokkos")
    @mock.patch("CIME.build.generate_makefile_macro")  # no need for makefile macros
    @mock.patch(
        "CIME.build.Files"
    )  # used to check expected behavior by checking libs variable
    def test__build_libraries_other_model(
        self, Files, _, uses_kokkos, case, caseroot, **kwargs
    ):
        uses_kokkos.return_value = False

        exeroot = os.path.join(caseroot, "bld")
        cimeroot = os.getcwd()
        libroot = os.path.join(caseroot, "libs")
        buildlist = []
        complist = []

        case.get_values = mock.MagicMock(
            side_effect=[
                [],  # CASE_SUPPORT_LIBRARIES
            ]
        )

        case.get_value = mock.MagicMock(
            side_effect=[
                "openmpi",  # MPILIB
                "new",  # MODEL
                "new",  # MODEL
                "",  # COMP_OCN
                "",  # CAM_DYCORE
                "",  # SHAREDLIBROOT
                False,  # TEST
            ]
        )

        build._build_libraries(
            case,
            exeroot,
            "shared",
            caseroot,
            cimeroot,
            libroot,
            "unique",
            "gnu",
            buildlist,
            "mct",
            complist,
        )

        get_value = Files.return_value.get_value

        expected = [
            mock.call("BUILD_LIB_FILE", {"lib": "gptl"}, attribute_required=True),
            mock.call("BUILD_LIB_FILE", {"lib": "mct"}, attribute_required=True),
            mock.call("BUILD_LIB_FILE", {"lib": "pio"}, attribute_required=True),
            mock.call("BUILD_LIB_FILE", {"lib": "csm_share"}, attribute_required=True),
            mock.call("BUILD_LIB_FILE", {"lib": "FTorch"}, attribute_required=True),
        ]

        assert get_value.call_args_list == expected, get_value.call_args_list

    @mock_case()
    @mock.patch("CIME.build.uses_kokkos")
    @mock.patch("CIME.build.generate_makefile_macro")  # no need for makefile macros
    @mock.patch(
        "CIME.build.Files"
    )  # used to check expected behavior by checking libs variable
    def test__build_libraries_mpi_serial(
        self, Files, _, uses_kokkos, case, caseroot, **kwargs
    ):
        uses_kokkos.return_value = False

        exeroot = os.path.join(caseroot, "bld")
        cimeroot = os.getcwd()
        libroot = os.path.join(caseroot, "libs")
        buildlist = []
        complist = []

        case.get_values = mock.MagicMock(
            side_effect=[
                [],  # CASE_SUPPORT_LIBRARIES
            ]
        )

        case.get_value = mock.MagicMock(
            side_effect=[
                "mpi-serial",  # MPILIB
                "e3sm",  # MODEL
                "e3sm",  # MODEL
                "",  # COMP_OCN
                "",  # CAM_DYCORE
                "",  # SHAREDLIBROOT
                False,  # TEST
            ]
        )

        build._build_libraries(
            case,
            exeroot,
            "shared",
            caseroot,
            cimeroot,
            libroot,
            "unique",
            "gnu",
            buildlist,
            "mct",
            complist,
        )

        get_value = Files.return_value.get_value

        expected = [
            mock.call("BUILD_LIB_FILE", {"lib": "mpi-serial"}, attribute_required=True),
            mock.call("BUILD_LIB_FILE", {"lib": "gptl"}, attribute_required=True),
            mock.call("BUILD_LIB_FILE", {"lib": "mct"}, attribute_required=True),
            mock.call("BUILD_LIB_FILE", {"lib": "spio"}, attribute_required=True),
            mock.call("BUILD_LIB_FILE", {"lib": "csm_share"}, attribute_required=True),
            mock.call("BUILD_LIB_FILE", {"lib": "FTorch"}, attribute_required=True),
        ]

        assert get_value.call_args_list == expected, get_value.call_args_list

    @mock_case()
    @mock.patch("CIME.build.uses_kokkos")
    @mock.patch("CIME.build.generate_makefile_macro")  # no need for makefile macros
    @mock.patch(
        "CIME.build.Files"
    )  # used to check expected behavior by checking libs variable
    def test__build_libraries_use_kokkos(
        self, Files, _, uses_kokkos, case, caseroot, **kwargs
    ):
        uses_kokkos.return_value = True

        exeroot = os.path.join(caseroot, "bld")
        cimeroot = os.getcwd()
        libroot = os.path.join(caseroot, "libs")
        buildlist = []
        complist = []

        case.get_values = mock.MagicMock(
            side_effect=[
                [],  # CASE_SUPPORT_LIBRARIES
            ]
        )

        case.get_value = mock.MagicMock(
            side_effect=[
                "openmpi",  # MPILIB
                "e3sm",  # MODEL
                "e3sm",  # MODEL
                "",  # COMP_OCN
                "",  # CAM_DYCORE
                "",  # SHAREDLIBROOT
                False,  # TEST
            ]
        )

        build._build_libraries(
            case,
            exeroot,
            "shared",
            caseroot,
            cimeroot,
            libroot,
            "unique",
            "gnu",
            buildlist,
            "mct",
            complist,
        )

        get_value = Files.return_value.get_value

        expected = [
            mock.call("BUILD_LIB_FILE", {"lib": "gptl"}, attribute_required=True),
            mock.call("BUILD_LIB_FILE", {"lib": "mct"}, attribute_required=True),
            mock.call("BUILD_LIB_FILE", {"lib": "spio"}, attribute_required=True),
            mock.call("BUILD_LIB_FILE", {"lib": "csm_share"}, attribute_required=True),
            mock.call("BUILD_LIB_FILE", {"lib": "FTorch"}, attribute_required=True),
            mock.call("BUILD_LIB_FILE", {"lib": "ekat"}, attribute_required=True),
        ]

        assert get_value.call_args_list == expected, get_value.call_args_list

    @mock_case()
    @mock.patch("CIME.build.uses_kokkos")
    @mock.patch("CIME.build.generate_makefile_macro")  # no need for makefile macros
    @mock.patch(
        "CIME.build.Files"
    )  # used to check expected behavior by checking libs variable
    def test__build_libraries_nuopc(
        self, Files, _, uses_kokkos, case, caseroot, **kwargs
    ):
        uses_kokkos.return_value = False

        exeroot = os.path.join(caseroot, "bld")
        cimeroot = os.getcwd()
        libroot = os.path.join(caseroot, "libs")
        buildlist = []
        complist = []

        case.get_values = mock.MagicMock(
            side_effect=[
                [],  # CASE_SUPPORT_LIBRARIES
            ]
        )

        case.get_value = mock.MagicMock(
            side_effect=[
                "openmpi",  # MPILIB
                "e3sm",  # MODEL
                "e3sm",  # MODEL
                "",  # COMP_OCN
                "",  # CAM_DYCORE
                "",  # SHAREDLIBROOT
                False,  # TEST
            ]
        )

        build._build_libraries(
            case,
            exeroot,
            "shared",
            caseroot,
            cimeroot,
            libroot,
            "unique",
            "gnu",
            buildlist,
            "nuopc",
            complist,
        )

        get_value = Files.return_value.get_value

        expected = [
            mock.call("BUILD_LIB_FILE", {"lib": "gptl"}, attribute_required=True),
            mock.call("BUILD_LIB_FILE", {"lib": "mct"}, attribute_required=True),
            mock.call("BUILD_LIB_FILE", {"lib": "spio"}, attribute_required=True),
            mock.call("BUILD_LIB_FILE", {"lib": "csm_share"}, attribute_required=True),
            mock.call("BUILD_LIB_FILE", {"lib": "FTorch"}, attribute_required=True),
            mock.call("BUILD_LIB_FILE", {"lib": "CDEPS"}, attribute_required=True),
        ]

        assert get_value.call_args_list == expected, get_value.call_args_list

    @mock_case()
    @mock.patch("CIME.build.uses_kokkos")
    @mock.patch("CIME.build.generate_makefile_macro")  # no need for makefile macros
    @mock.patch(
        "CIME.build.Files"
    )  # used to check expected behavior by checking libs variable
    def test__build_libraries_fms(
        self, Files, _, uses_kokkos, case, caseroot, **kwargs
    ):
        uses_kokkos.return_value = False

        exeroot = os.path.join(caseroot, "bld")
        cimeroot = os.getcwd()
        libroot = os.path.join(caseroot, "libs")
        buildlist = []
        complist = []

        case.get_values = mock.MagicMock(
            side_effect=[
                [],  # CASE_SUPPORT_LIBRARIES
            ]
        )

        case.get_value = mock.MagicMock(
            side_effect=[
                "openmpi",  # MPILIB
                "e3sm",  # MODEL
                "e3sm",  # MODEL
                "mom",  # COMP_OCN
                "fv3",  # CAM_DYCORE
                "",  # SHAREDLIBROOT
                False,  # TEST
            ]
        )

        build._build_libraries(
            case,
            exeroot,
            "shared",
            caseroot,
            cimeroot,
            libroot,
            "unique",
            "gnu",
            buildlist,
            "mct",
            complist,
        )

        get_value = Files.return_value.get_value

        expected = [
            mock.call("BUILD_LIB_FILE", {"lib": "gptl"}, attribute_required=True),
            mock.call("BUILD_LIB_FILE", {"lib": "mct"}, attribute_required=True),
            mock.call("BUILD_LIB_FILE", {"lib": "spio"}, attribute_required=True),
            mock.call("BUILD_LIB_FILE", {"lib": "csm_share"}, attribute_required=True),
            mock.call("BUILD_LIB_FILE", {"lib": "FTorch"}, attribute_required=True),
            mock.call("BUILD_LIB_FILE", {"lib": "FMS"}, attribute_required=True),
        ]

        assert get_value.call_args_list == expected, get_value.call_args_list

    @mock_case()
    @mock.patch("CIME.build.uses_kokkos")
    @mock.patch("CIME.build.generate_makefile_macro")  # no need for makefile macros
    @mock.patch(
        "CIME.build.Files"
    )  # used to check expected behavior by checking libs variable
    def test__build_libraries(self, Files, _, uses_kokkos, case, caseroot, **kwargs):
        uses_kokkos.return_value = False

        exeroot = os.path.join(caseroot, "bld")
        cimeroot = os.getcwd()
        libroot = os.path.join(caseroot, "libs")
        buildlist = []
        complist = []

        case.get_values = mock.MagicMock(
            side_effect=[
                [],  # CASE_SUPPORT_LIBRARIES
            ]
        )

        case.get_value = mock.MagicMock(
            side_effect=[
                "openmpi",  # MPILIB
                "e3sm",  # MODEL
                "e3sm",  # MODEL
                "",  # COMP_OCN
                "",  # CAM_DYCORE
                "",  # SHAREDLIBROOT
                False,  # TEST
            ]
        )

        build._build_libraries(
            case,
            exeroot,
            "shared",
            caseroot,
            cimeroot,
            libroot,
            "unique",
            "gnu",
            buildlist,
            "mct",
            complist,
        )

        get_value = Files.return_value.get_value

        expected = [
            mock.call("BUILD_LIB_FILE", {"lib": "gptl"}, attribute_required=True),
            mock.call("BUILD_LIB_FILE", {"lib": "mct"}, attribute_required=True),
            mock.call("BUILD_LIB_FILE", {"lib": "spio"}, attribute_required=True),
            mock.call("BUILD_LIB_FILE", {"lib": "csm_share"}, attribute_required=True),
            mock.call("BUILD_LIB_FILE", {"lib": "FTorch"}, attribute_required=True),
        ]

        assert get_value.call_args_list == expected, get_value.call_args_list
