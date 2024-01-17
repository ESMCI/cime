import unittest
from unittest import mock

from CIME import aprun

# NTASKS, NTHRDS, ROOTPE, PSTRID
DEFAULT_COMP_ATTRS = [
    512,
    2,
    0,
    1,
    675,
    2,
    0,
    1,
    168,
    2,
    512,
    1,
    512,
    2,
    0,
    1,
    128,
    4,
    680,
    1,
    168,
    2,
    512,
    1,
    168,
    2,
    512,
    1,
    512,
    2,
    0,
    1,
    1,
    1,
    0,
    1,
]

# MAX_TASKS_PER_NODE, MAX_MPITASKS_PER_NODE, PIO_NUMTASKS, PIO_ASYNC_INTERFACE, COMPILER, MACH
DEFAULT_ARGS = [
    16,
    16,
    -1,
    False,
    "gnu",
    "docker",
]


class TestUnitAprun(unittest.TestCase):
    def test_aprun_extra_args(self):
        case = mock.MagicMock()

        case.get_values.return_value = [
            "CPL",
            "ATM",
            "LND",
            "ICE",
            "OCN",
            "ROF",
            "GLC",
            "WAV",
            "IAC",
        ]

        case.get_value.side_effect = DEFAULT_COMP_ATTRS + DEFAULT_ARGS

        extra_args = {
            "-e DEBUG=true": {"position": "global"},
            "-j 20": {"position": "per"},
        }

        (
            aprun_args,
            total_node_count,
            total_task_count,
            min_tasks_per_node,
            max_thread_count,
        ) = aprun.get_aprun_cmd_for_case(case, "e3sm.exe", extra_args=extra_args)

        assert (
            aprun_args
            == " -e DEBUG=true -n 680 -N 8 -d 2 -j 20 e3sm.exe : -n 128 -N 4 -d 4 -j 20 e3sm.exe "
        )
        assert total_node_count == 117
        assert total_task_count == 808
        assert min_tasks_per_node == 4
        assert max_thread_count == 4

    def test_aprun(self):
        case = mock.MagicMock()

        case.get_values.return_value = [
            "CPL",
            "ATM",
            "LND",
            "ICE",
            "OCN",
            "ROF",
            "GLC",
            "WAV",
            "IAC",
        ]

        case.get_value.side_effect = DEFAULT_COMP_ATTRS + DEFAULT_ARGS

        (
            aprun_args,
            total_node_count,
            total_task_count,
            min_tasks_per_node,
            max_thread_count,
        ) = aprun.get_aprun_cmd_for_case(case, "e3sm.exe")

        assert (
            aprun_args == "  -n 680 -N 8 -d 2  e3sm.exe : -n 128 -N 4 -d 4  e3sm.exe "
        )
        assert total_node_count == 117
        assert total_task_count == 808
        assert min_tasks_per_node == 4
        assert max_thread_count == 4
