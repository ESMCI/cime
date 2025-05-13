#!/usr/bin/env python3

import glob
import re
import os
import stat
import doctest
import sys
import pkgutil
import unittest
import functools

import CIME
from CIME import utils
from CIME.tests import base


class TestDocs(base.BaseTestCase):
    def test_lib_docs(self):
        cime_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

        ignore_patterns = [
            "/tests/",
            "mvk.py",
            "pgn.py",
            "tsc.py",
        ]

        for dirpath, _, filenames in os.walk(os.path.join(cime_root, "CIME")):
            for filepath in map(lambda x: os.path.join(dirpath, x), filenames):
                if not filepath.endswith(".py") or any(
                    [x in filepath for x in ignore_patterns]
                ):
                    continue

                # Couldn't use doctest.DocFileSuite due to sys.path issue
                self.run_cmd_assert_result(
                    f"PYTHONPATH={cime_root}:$PYTHONPATH python3 -m doctest {filepath} 2>&1",
                    from_dir=cime_root,
                )
