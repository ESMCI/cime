import os
import sys

# Ensure the CIME repo root (the directory containing this package) is on
# sys.path so that CIME sub-packages are importable regardless of how this
# package was reached.  We use append (not insert) to match the legacy
# behaviour of CIME/XML/standard_module_setup.py and to avoid shadowing any
# paths the caller has explicitly placed at the front of sys.path.
#
# This replaces the side-effect that was previously triggered by
# ``from CIME.XML.standard_module_setup import *`` in ~200 internal modules.
# Those star-imports were removed in the standard_module_setup refactor; this
# centralised guard restores the bootstrap guarantee for any consumer that
# imports any CIME sub-package, including external downstream repos
# (e.g. cime_config) that relied on the implicit sys.path append.
#
# The guard will be revisited when CIME.XML is relocated as part of the
# ongoing refactor — at that point a DeprecationWarning can be emitted here to
# give downstream consumers a migration window.
_CIMEROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _CIMEROOT not in sys.path:
    sys.path.append(_CIMEROOT)
