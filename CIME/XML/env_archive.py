"""
Interface to the env_archive.xml file.  This class inherits from EnvBase
"""
from CIME.XML.standard_module_setup import *
from CIME import utils
from CIME.XML.archive_base import ArchiveBase
from CIME.XML.env_base import EnvBase

logger = logging.getLogger(__name__)
# pylint: disable=super-init-not-called
class EnvArchive(ArchiveBase, EnvBase):
    def __init__(self, case_root=None, infile="env_archive.xml", read_only=False):
        """
        initialize an object interface to file env_archive.xml in the case directory
        """
        schema = os.path.join(utils.get_schema_path(), "env_archive.xsd")
        EnvBase.__init__(self, case_root, infile, schema=schema, read_only=read_only)

    def get_archive_specs(self):
        components_element = self.get_child("components")

        return self.get_children("comp_archive_spec", root=components_element)

    def get_rpointer_nodes(self, root):
        assert root.name == "comp_archive_spec"

        return self.get_children("rpointer", root=root)

    def get_rpointers(self, root):
        for node in self.get_rpointer_nodes(root):
            file = self.get_child("rpointer_file", root=node).text

            content = self.get_child("rpointer_content", root=node).text

            yield file, content

    def get_type_info(self, vid):
        return "char"
