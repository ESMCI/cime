# pragma pylint: disable=unused-import
"""
Standard imports for CIME XML modules.

This module is DEPRECATED. New code should use explicit imports instead of
`from CIME.XML.standard_module_setup import *`.

The exports are maintained for backward compatibility with external code
(E3SM, CESM, NorESM cime_config directories).
"""

import logging  # noqa: F401
import os  # noqa: F401
import re  # noqa: F401
import sys  # noqa: F401

LIB_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(LIB_DIR)

from CIME.utils import expect, get_cime_root, run_cmd, run_cmd_no_fail  # noqa: F401
