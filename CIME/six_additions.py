"""Additions to the CIME.six library needed for python 2/3 compatibility"""

import CIME.six

if CIME.six.PY3:
    # This is only available in python3.2 and later, so this code won't
    # run with python3 versions prior to 3.2
    _assertNotRegex = "assertNotRegex"
else:
    _assertNotRegex = "assertNotRegexpMatches"


def assertNotRegex(self, *args, **kwargs):
    return getattr(self, _assertNotRegex)(*args, **kwargs)
