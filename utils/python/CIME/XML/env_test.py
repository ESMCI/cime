"""
Interface to the env_test.xml file.  This class inherits from EnvBase
"""
from standard_module_setup import *

from env_base import EnvBase

logger = logging.getLogger(__name__)

class EnvTest(EnvBase):

    def __init__(self, case_root=os.getcwd(), infile="env_test.xml"):
        """
        initialize an object interface to file env_test.xml in the case directory
        """
        EnvBase.__init__(self, case_root, infile)

    def add_test(self,testnode):
        self.root.append(testnode)
        self.write()

    def set_initial_values(self, case):
        tnode = self.get_node("test")
        for child in tnode:
            if child.tag != "BUILD" and child.tag != "RUN":
                case.set_value(child.tag,child.text)



    def get_step_phase_cnt(self,step):
        bldnodes = self.get_nodes(step)
        cnt = 0
        for node in bldnodes:
            cnt = max(cnt, int(node.attrib["phase"]))
        return cnt

    def get_settings_for_phase(self, name, cnt):
        node = self.get_node(name,{"phase":cnt})
        settings = []
        for child in node:
            logger.debug ("Here child is %s with value %s"%(child.tag,child.text))
            settings.append((child.tag, child.text))

        return settings

    def run_phase_requires_clone(self, phase):
        node = self.get_node("RUN",{"phase":phase})
        if clone in node.attrib:
            return node.attrib["clone"]
        return None

