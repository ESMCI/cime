"""
Encapsulate the importing of python utils and logging setup, things
that every script should do.
"""
# pylint: disable=unused-import

import sys, os
import __main__ as main

real_file_dir = os.path.dirname(os.path.realpath(__file__))
cimeroot = os.path.abspath(os.path.join(real_file_dir, "..", ".."))
sys.path.insert(0, cimeroot)

# Important: Allows external tools to link up with CIME
os.environ["CIMEROOT"] = cimeroot

import CIME.utils

CIME.utils.check_minimum_python_version(3, 6)
CIME.utils.stop_buffering_output()
import logging, argparse
