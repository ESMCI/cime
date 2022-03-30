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
    assert sys.version_info[0] > major or (
        sys.version_info[0] == major and sys.version_info[1] >= minor
    ), msg


check_minimum_python_version(3, 6)

real_file_dir = os.path.dirname(os.path.realpath(__file__))
cimeroot = os.path.abspath(os.path.join(real_file_dir, "..", ".."))
sys.path.insert(0, cimeroot)

# Important: Allows external tools to link up with CIME
os.environ["CIMEROOT"] = cimeroot

import CIME.utils


CIME.utils.stop_buffering_output()
import logging, argparse
