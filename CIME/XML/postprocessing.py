"""
Interface to the config_postprocessing.xml file.  This class inherits from EntryID
"""

from CIME.XML.standard_module_setup import *
from CIME.XML.entry_id import EntryID
from CIME.XML.files import Files
from CIME.utils import expect

logger = logging.getLogger(__name__)


class Postprocessing(EntryID):
    def __init__(self, infile=None, files=None):
        """
        initialize an object
        """
        if files is None:
            files = Files()
        if infile is None:
            infile = files.get_value("POSTPROCESSING_SPEC_FILE")
        if infile is not None:
            self.file_exists = os.path.isfile(infile)
        else:
            self.file_exists = False
        if not self.file_exists:
            return
        expect(infile, "No postprocessing file defined in {}".format(files.filename))

        schema = files.get_schema("POSTPROCESSING_SPEC_FILE")

        EntryID.__init__(self, infile, schema=schema)

        # Append the contents of $HOME/.cime/config_postprocessing.xml if it exists
        # This could cause problems if node matchs are repeated when only one is expected
        infile = os.path.join(
            os.environ.get("HOME"), ".cime", "config_postprocessing.xml"
        )
        if os.path.exists(infile):
            EntryID.read(self, infile)
