"""
CIME ERRI test  This class inherits from ERR
ERRI tests short term archiving and restart capabilities with "incomplete" (unzipped) log files
"""

import glob
import gzip
import logging
import os
import shutil

from CIME.SystemTests.err import ERR

logger = logging.getLogger(__name__)


class ERRI(ERR):
    def __init__(self, case, **kwargs):
        """
        initialize an object interface to the ERU system test
        """
        ERR.__init__(self, case, **kwargs)

    def _case_two_custom_postrun_action(self):
        rundir = self._case.get_value("RUNDIR")
        for logname_gz in glob.glob(os.path.join(rundir, "*.log*.gz")):
            # gzipped logfile names are of the form $LOGNAME.gz
            # Removing the last three characters restores the original name
            logname = logname_gz[:-3]
            with gzip.open(logname_gz, "rb") as f_in, open(logname, "w") as f_out:
                shutil.copyfileobj(f_in, f_out)
            os.remove(logname_gz)
