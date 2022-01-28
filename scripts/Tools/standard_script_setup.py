"""
Encapsulate the importing of python utils and logging setup, things
that every script should do.
"""
# pylint: disable=unused-import

import sys, os
import __main__ as main

def check_minimum_python_version(major, minor):
    """
    Check your python version.

    >>> check_minimum_python_version(sys.version_info[0], sys.version_info[1])
    >>>
    """
    msg = (
        "Python "
        + str(major)
        + ", minor version "
        + str(minor)
        + " is required, you have "
        + str(sys.version_info[0])
        + "."
        + str(sys.version_info[1])
    )
    assert sys.version_info[0] > major \
        or (sys.version_info[0] == major and sys.version_info[1] >= minor), \
        msg
    
check_minimum_python_version(3, 6)

_CIMEROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
_LIB_DIR = os.path.join(_CIMEROOT, "scripts", "lib")
sys.path.append(_LIB_DIR)

# Important: Allows external tools to link up with CIME
os.environ["CIMEROOT"] = _CIMEROOT

import CIME.utils


CIME.utils.stop_buffering_output()
import logging, argparse
