"""
Encapsulate the importing of python utils and logging setup, things
that every script should do.
"""
# pylint: disable=unused-import

import sys, os
import __main__ as main


def check_minimum_python_version(major, minor, warn_only=False):
    """
    Check your python version.

    >>> check_minimum_python_version(3, 5)
    >>>
    """
    check = sys.version_info[0] > major or (
        sys.version_info[0] == major and sys.version_info[1] >= minor
    )
    if check:
        return
    msg = (
        "Python "
        + str(major)
        + "."
        + str(minor)
        + " is required to run CIME. You have "
        + str(sys.version_info[0])
        + "."
        + str(sys.version_info[1])
    )
    if warn_only:
        print(msg.replace("required", "recommended") + ".", file=sys.stderr)
        return
    raise RuntimeError(msg + " - please use a newer version of Python.")


# Require users to be using >=3.9
check_minimum_python_version(3, 9)
# Warn users if they are using <3.10
check_minimum_python_version(3, 10, warn_only=True)

real_file_dir = os.path.dirname(os.path.realpath(__file__))
cimeroot = os.path.abspath(os.path.join(real_file_dir, "..", ".."))
sys.path.insert(0, cimeroot)

# Important: Allows external tools to link up with CIME
os.environ["CIMEROOT"] = cimeroot

import CIME.utils

CIME.utils.stop_buffering_output()
import argparse, logging
