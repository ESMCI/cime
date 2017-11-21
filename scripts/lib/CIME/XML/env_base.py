"""
Base class for env files.  This class inherits from EntryID.py
"""
from CIME.XML.standard_module_setup import *
from CIME.XML.entry_id import EntryID
from CIME.XML.headers import Headers
from CIME.utils import convert_to_type
logger = logging.getLogger(__name__)

class EnvBase(EntryID):

    def __init__(self, case_root, infile, schema=None):
        if case_root is None:
            case_root = os.getcwd()

        if os.path.isabs(infile):
            fullpath = infile
        else:
            fullpath = os.path.join(case_root, infile)

        EntryID.__init__(self, fullpath, schema=schema)
        if not os.path.isfile(fullpath):
            headerobj = Headers()
            headernode = headerobj.get_header_node(os.path.basename(fullpath))
            self.root.append(headernode)

    def set_components(self, components):
        if hasattr(self, '_components'):
            # pylint: disable=attribute-defined-outside-init
            self._components = components

    def check_if_comp_var(self, vid, attribute=None):
        nodes = self.get_nodes("entry", {"id" : vid})
        node = None
        comp = None
        if len(nodes):
            node = nodes[0]
        if node:
            valnodes = node.findall(".//value[@compclass]")
            if len(valnodes) == 0:
                logger.debug("vid {} is not a compvar".format(vid))
                return vid, None, False
            else:
                logger.debug("vid {} is a compvar".format(vid))
                if attribute is not None:
                    comp = attribute["compclass"]
                return vid, comp, True
        else:
            if hasattr(self, "_components"):
                new_vid = None
                for comp in self._components:
                    if "_"+comp in vid:
                        new_vid = vid.replace('_'+comp, '', 1)
                    elif comp+"_" in vid:
                        new_vid = vid.replace(comp+'_', '', 1)

                    if new_vid is not None:
                        break
                if new_vid is not None:
                    logger.debug("vid {} is a compvar with comp {}".format(vid, comp))
                    return new_vid, comp, True

        return vid, None, False

    def get_value(self, vid, attribute=None, resolved=True, subgroup=None):
        """
        Get a value for entry with id attribute vid.
        or from the values field if the attribute argument is provided
        and matches
        """
        value = None
        vid, comp, iscompvar = self.check_if_comp_var(vid, attribute)
        logger.debug("vid {} comp {} iscompvar {}".format(vid, comp, iscompvar))
        if iscompvar:
            if comp is None:
                if subgroup is not None:
                    comp = subgroup
                else:
                    logger.debug("Not enough info to get value for {}".format(vid))
                    return value
            if attribute is None:
                attribute = {"compclass" : comp}
            else:
                attribute["compclass"] = comp
            node = self.get_optional_node("entry", {"id":vid})
            if node is not None:
                type_str = self._get_type_info(node)
                val = self.get_element_text("value", attribute, root=node)
                if val is not None:
                    if val.startswith("$"):
                        value = val
                    else:
                        value = convert_to_type(val,type_str, vid)
                return value
        return EntryID.get_value(self, vid, attribute=attribute, resolved=resolved, subgroup=subgroup)

    def set_value(self, vid, value, subgroup=None, ignore_type=False):
        """
        Set the value of an entry-id field to value
        Returns the value or None if not found
        subgroup is ignored in the general routine and applied in specific methods
        """
        vid, comp, iscompvar = self.check_if_comp_var(vid, None)
        val = None
        root = self.root if subgroup is None else self.get_optional_node("group", {"id":subgroup})
        node = self.get_optional_node("entry", {"id":vid}, root=root)
        if node is not None:
            if iscompvar and comp is None:
                # pylint: disable=no-member
                for comp in self._components:
                    val = self._set_value(node, value, vid, subgroup, ignore_type, compclass=comp)
            else:
                val = self._set_value(node, value, vid, subgroup, ignore_type, compclass=comp)
        return val

    # pylint: disable=arguments-differ
    def _set_value(self, node, value, vid=None, subgroup=None, ignore_type=False, compclass=None):
        if vid is None:
            vid = node.get("id")
        vid, _, iscompvar = self.check_if_comp_var(vid, None)

        if iscompvar:
            attribute = {"compclass":compclass}
            str_value = self.get_valid_value_string(node, value, vid, ignore_type)
            val = self.set_element_text("value", str_value, attribute, root=node)
        else:
            val = EntryID._set_value(self, node, value, vid, subgroup, ignore_type)
        return val

    def get_nodes_by_id(self, varid):
        varid, _, _ = self.check_if_comp_var(varid, None)
        return EntryID.get_nodes_by_id(self, varid)

    def cleanupnode(self, node):
        """
        Remove the <group>, <file>, <values> and <value> childnodes from node
        """
        fnode = node.find(".//file")
        node.remove(fnode)
        gnode = node.find(".//group")
        node.remove(gnode)
        dnode = node.find(".//default_value")
        if dnode is not None:
            node.remove(dnode)
        vnode = node.find(".//values")
        if vnode is not None:
            componentatt = vnode.findall(".//value[@component=\"ATM\"]")
            # backward compatibility (compclasses and component were mixed
            # now we seperated into component and compclass)
            if len(componentatt) > 0:
                for ccnode in vnode.findall(".//value[@component]"):
                    val = ccnode.attrib.get("component")
                    ccnode.attrib.pop("component")
                    ccnode.set("compclass",val)
            compclassatt = vnode.findall(".//value[@compclass]")

            if len(compclassatt) == 0:
                node.remove(vnode)

        return node
