"""
Common interface to XML files which follow the grids format,
This is not an abstract class - but inherits from the abstact class GenericXML
"""

from collections import OrderedDict
from CIME.XML.standard_module_setup import *
from CIME.XML.files import Files
from CIME.XML.generic_xml import GenericXML

logger = logging.getLogger(__name__)

# Separator character for multiple grids within a single component (currently just used
# for GLC when there are multiple ice sheet grids). It is important that this character
# NOT appear in any file names - or anywhere in the path of directories holding input
# data.
GRID_SEP = ":"


class Grids(GenericXML):
    def __init__(self, infile=None, files=None, comp_interface=None):
        if files is None:
            files = Files(comp_interface=comp_interface)
        if infile is None:
            infile = files.get_value("GRIDS_SPEC_FILE")
        logger.debug(" Grid specification file is {}".format(infile))
        schema = files.get_schema("GRIDS_SPEC_FILE")
        expect(
            os.path.isfile(infile) and os.access(infile, os.R_OK),
            f" grid file not found {infile}",
        )
        try:
            GenericXML.__init__(self, infile, schema)
        except:
            # Getting false failures on izumi, change this to a warning
            logger.warning("Schema validity test fails for {}".format(infile))

        self._version = self.get_version()
        self._comp_gridnames = self._get_grid_names()

    def _get_grid_names(self):
        grids = self.get_child("grids")
        model_grid_defaults = self.get_child("model_grid_defaults", root=grids)
        nodes = self.get_children("grid", root=model_grid_defaults)
        gridnames = []
        for node in nodes:
            gn = self.get(node, "name")
            if gn not in gridnames:
                gridnames.append(gn)
        if "mask" not in gridnames:
            gridnames.append("mask")

        return gridnames

    def get_grid_info(self, name, compset, driver):
        """
        Find the matching grid node

        Returns a dictionary containing relevant grid variables: domains, gridmaps, etc.
        """
        gridinfo = {}
        atmnlev = None
        lndnlev = None

        # mechanism to specify atm levels
        atmlevregex = re.compile(r"([^_]+)z(\d+)(.*)$")
        levmatch = re.match(atmlevregex, name)
        if levmatch:
            atmnlev = levmatch.group(2)
            name = levmatch.group(1) + levmatch.group(3)

        # mechanism to specify lnd levels
        lndlevregex = re.compile(r"(.*_)([^_]+)z(\d+)(_[^m].*)$")
        levmatch = re.match(lndlevregex, name)
        if levmatch:
            lndnlev = levmatch.group(3)
            name = levmatch.group(1) + levmatch.group(2) + levmatch.group(4)

        # determine component_grids dictionary and grid longname
        lname = self._read_config_grids(name, compset, atmnlev, lndnlev)
        gridinfo["GRID"] = lname
        component_grids = _ComponentGrids(lname)

        # determine domains given component_grids
        domains = self._get_domains(component_grids, atmlevregex, lndlevregex, driver)

        gridinfo.update(domains)

        # determine gridmaps given component_grids
        gridmaps = self._get_gridmaps(component_grids, driver, compset)
        gridinfo.update(gridmaps)

        component_grids.check_num_elements(gridinfo)

        return gridinfo

    def _read_config_grids(self, name, compset, atmnlev, lndnlev):
        """
        read config_grids.xml with version 2.0 schema

        Returns a grid long name given the alias ('name' argument)
        """
        model_grid = {}
        for comp_gridname in self._comp_gridnames:
            model_grid[comp_gridname] = None

        # (1) set array of component grid defaults that match current compset
        grids_node = self.get_child("grids")
        grid_defaults_node = self.get_child("model_grid_defaults", root=grids_node)
        for grid_node in self.get_children("grid", root=grid_defaults_node):
            name_attrib = self.get(grid_node, "name")
            compset_attrib = self.get(grid_node, "compset")
            compset_match = re.search(compset_attrib, compset)
            if compset_match is not None:
                model_grid[name_attrib] = self.text(grid_node)

        # (2)loop over all of the "model grid" nodes and determine is there an alias match with the
        # input grid name -  if there is an alias match determine if the "compset" and "not_compset"
        # regular expression attributes match the match the input compset

        model_gridnodes = self.get_children("model_grid", root=grids_node)
        model_gridnode = None
        foundalias = False
        for node in model_gridnodes:
            alias = self.get(node, "alias")
            if alias == name:
                foundalias = True
                foundcompset = False
                compset_attrib = self.get(node, "compset")
                not_compset_attrib = self.get(node, "not_compset")
                if compset_attrib and not_compset_attrib:
                    compset_match = re.search(compset_attrib, compset)
                    not_compset_match = re.search(not_compset_attrib, compset)
                    if compset_match is not None and not_compset_match is None:
                        foundcompset = True
                        model_gridnode = node
                        logger.debug(
                            "Found match for {} with compset_match {} and not_compset_match {}".format(
                                alias, compset_attrib, not_compset_attrib
                            )
                        )
                        break
                elif compset_attrib:
                    compset_match = re.search(compset_attrib, compset)
                    if compset_match is not None:
                        foundcompset = True
                        model_gridnode = node
                        logger.debug(
                            "Found match for {} with compset_match {}".format(
                                alias, compset_attrib
                            )
                        )
                        break
                elif not_compset_attrib:
                    not_compset_match = re.search(not_compset_attrib, compset)
                    if not_compset_match is None:
                        foundcompset = True
                        model_gridnode = node
                        logger.debug(
                            "Found match for {} with not_compset_match {}".format(
                                alias, not_compset_attrib
                            )
                        )
                        break
                else:
                    foundcompset = True
                    model_gridnode = node
                    logger.debug("Found match for {}".format(alias))
                    break
        expect(foundalias, "no alias {} defined".format(name))
        # if no match is found in config_grids.xml - exit
        expect(
            foundcompset, "grid alias {} not valid for compset {}".format(name, compset)
        )

        # for the match - find all of the component grid settings
        grid_nodes = self.get_children("grid", root=model_gridnode)
        for grid_node in grid_nodes:
            name = self.get(grid_node, "name")
            value = self.text(grid_node)
            if model_grid[name] != "null":
                model_grid[name] = value
        mask_node = self.get_optional_child("mask", root=model_gridnode)
        if mask_node is not None:
            model_grid["mask"] = self.text(mask_node)
        else:
            model_grid["mask"] = model_grid["ocnice"]

        # determine component grids and associated required domains and gridmaps
        # TODO: this should be in XML, not here
        prefix = {
            "atm": "a%",
            "lnd": "l%",
            "ocnice": "oi%",
            "rof": "r%",
            "wav": "w%",
            "glc": "g%",
            "mask": "m%",
            "iac": "z%",
        }
        lname = ""
        for component_gridname in self._comp_gridnames:
            if lname:
                lname = lname + "_" + prefix[component_gridname]
            else:
                lname = prefix[component_gridname]
            if model_grid[component_gridname] is not None:
                lname += model_grid[component_gridname]
                if component_gridname == "atm" and atmnlev is not None:
                    if not ("a{:n}ull" in lname):
                        lname += "z" + atmnlev

                elif component_gridname == "lnd" and lndnlev is not None:
                    if not ("l{:n}ull" in lname):
                        lname += "z" + lndnlev

            else:
                lname += "null"
        return lname

    def _get_domains(self, component_grids, atmlevregex, lndlevregex, driver):
        """determine domains dictionary for config_grids.xml v2 schema"""
        domains = {}
        mask_name = component_grids.get_comp_gridname("mask")

        for comp_name in component_grids.get_compnames(include_mask=True):
            for grid_name in component_grids.get_comp_gridlist(comp_name):
                # Determine grid name with no nlev suffix if there is one
                grid_name_nonlev = grid_name
                levmatch = re.match(atmlevregex, grid_name)
                if levmatch:
                    grid_name_nonlev = levmatch.group(1) + levmatch.group(3)
                levmatch = re.match(lndlevregex, grid_name)
                if levmatch:
                    grid_name_nonlev = (
                        levmatch.group(1) + levmatch.group(2) + levmatch.group(4)
                    )
                self._get_domains_for_one_grid(
                    domains=domains,
                    comp_name=comp_name.upper(),
                    grid_name=grid_name,
                    grid_name_nonlev=grid_name_nonlev,
                    mask_name=mask_name,
                    driver=driver,
                )

        if driver == "nuopc":
            # Obtain the root node for the domain entry that sets the mask
            if domains["MASK_GRID"] != "null":
                mask_domain_node = self.get_optional_child(
                    "domain",
                    attributes={"name": domains["MASK_GRID"]},
                    root=self.get_child("domains"),
                )
                # Now obtain the mesh for the mask for the domain node for that component grid
                mesh_node = self.get_child("mesh", root=mask_domain_node)
                domains["MASK_MESH"] = self.text(mesh_node)

        return domains

    def _get_domains_for_one_grid(
        self, domains, comp_name, grid_name, grid_name_nonlev, mask_name, driver
    ):
        """Get domain information for the given grid, adding elements to the domains dictionary

        Args:
        - domains: dictionary of values, modified in place
        - comp_name: uppercase abbreviated name of component (e.g., "ATM")
        - grid_name: name of this grid
        - grid_name_nonlev: same as grid_name but with any level information stripped out
        - mask_name: the mask being used in this case
        - driver: the name of the driver being used in this case
        """
        domain_node = self.get_optional_child(
            "domain",
            attributes={"name": grid_name_nonlev},
            root=self.get_child("domains"),
        )
        if not domain_node:
            domain_root = self.get_optional_child("domains", {"driver": driver})
            if domain_root:
                domain_node = self.get_optional_child(
                    "domain", attributes={"name": grid_name_nonlev}, root=domain_root
                )
        if domain_node:
            # determine xml variable name
            if not "PTS_LAT" in domains:
                domains["PTS_LAT"] = "-999.99"
            if not "PTS_LON" in domains:
                domains["PTS_LON"] = "-999.99"
            if not comp_name == "MASK":
                if self.get_element_text("nx", root=domain_node):
                    # If there are multiple grids for this component, then the component
                    # _NX and _NY values won't end up being used, so we simply set them to 1
                    _add_grid_info(
                        domains,
                        comp_name + "_NX",
                        int(self.get_element_text("nx", root=domain_node)),
                        value_for_multiple=1,
                    )
                    _add_grid_info(
                        domains,
                        comp_name + "_NY",
                        int(self.get_element_text("ny", root=domain_node)),
                        value_for_multiple=1,
                    )
                elif self.get_element_text("lon", root=domain_node):
                    # No need to call _add_grid_info here because, for multiple grids, the
                    # end result will be the same as the hard-coded 1 used here
                    domains[comp_name + "_NX"] = 1
                    domains[comp_name + "_NY"] = 1
                    domains["PTS_LAT"] = self.get_element_text("lat", root=domain_node)
                    domains["PTS_LON"] = self.get_element_text("lon", root=domain_node)
                else:
                    # No need to call _add_grid_info here because, for multiple grids, the
                    # end result will be the same as the hard-coded 1 used here
                    domains[comp_name + "_NX"] = 1
                    domains[comp_name + "_NY"] = 1

            if driver == "mct" or driver == "moab":
                # mct
                file_nodes = self.get_children("file", root=domain_node)
                domain_file = ""
                for file_node in file_nodes:
                    grid_attrib = self.get(file_node, "grid")
                    mask_attrib = self.get(file_node, "mask")
                    if grid_attrib is not None and mask_attrib is not None:
                        grid_match = re.search(comp_name.lower(), grid_attrib)
                        mask_match = False
                        if mask_name is not None:
                            mask_match = mask_name == mask_attrib
                        if grid_match is not None and mask_match:
                            domain_file = self.text(file_node)
                    elif grid_attrib is not None:
                        grid_match = re.search(comp_name.lower(), grid_attrib)
                        if grid_match is not None:
                            domain_file = self.text(file_node)
                    elif mask_attrib is not None:
                        mask_match = mask_name == mask_attrib
                        if mask_match:
                            domain_file = self.text(file_node)
                if domain_file:
                    _add_grid_info(
                        domains,
                        comp_name + "_DOMAIN_FILE",
                        os.path.basename(domain_file),
                    )
                    path = os.path.dirname(domain_file)
                    if len(path) > 0:
                        _add_grid_info(domains, comp_name + "_DOMAIN_PATH", path)

            if driver == "nuopc":
                if not comp_name == "MASK":
                    mesh_nodes = self.get_children("mesh", root=domain_node)
                    mesh_file = ""
                    for mesh_node in mesh_nodes:
                        mesh_file = self.text(mesh_node)
                    if mesh_file:
                        _add_grid_info(domains, comp_name + "_DOMAIN_MESH", mesh_file)
                    if comp_name == "LND" or comp_name == "ATM":
                        # Note: ONLY want to define PTS_DOMAINFILE for land and ATM
                        file_node = self.get_optional_child("file", root=domain_node)
                        if file_node is not None and self.text(file_node) != "unset":
                            domains["PTS_DOMAINFILE"] = self.text(file_node)
        # set up dictionary of domain files for every component
        _add_grid_info(domains, comp_name + "_GRID", grid_name)

    def _get_gridmaps(self, component_grids, driver, compset):
        """Set all mapping files for config_grids.xml v2 schema

        If a component (e.g., GLC) has multiple grids, then each mapping file variable for
        that component will be a colon-delimited list with the appropriate number of
        elements.

        If a given gridmap is required but not given explicitly, then its value will be
        either "unset" or "idmap". Even in the case of a component with multiple grids
        (e.g., GLC), there will only be a single "unset" or "idmap" value. (We do not
        currently handle the possibility that some grids will have an "idmap" value while
        others have an explicit mapping file. So it is currently an error for "idmap" to
        appear in a mapping file variable for a component with multiple grids; this will
        be checked elsewhere.)

        """
        gridmaps = {}

        # (1) determine values of gridmaps for target grid
        #
        # Exclude the ice component from the list of compnames because it is assumed to be
        # on the same grid as ocn, so doesn't have any gridmaps of its own
        compnames = component_grids.get_compnames(
            include_mask=False, exclude_comps=["ice"]
        )
        for idx, compname in enumerate(compnames):
            for other_compname in compnames[idx + 1 :]:
                for gridvalue in component_grids.get_comp_gridlist(compname):
                    for other_gridvalue in component_grids.get_comp_gridlist(
                        other_compname
                    ):
                        self._get_gridmaps_for_one_grid_pair(
                            gridmaps=gridmaps,
                            driver=driver,
                            compname=compname,
                            other_compname=other_compname,
                            gridvalue=gridvalue,
                            other_gridvalue=other_gridvalue,
                        )

        # (2) set all possibly required gridmaps to 'idmap' for mct and 'unset/idmap' for
        # nuopc, if they aren't already set
        required_gridmaps_node = self.get_child("required_gridmaps")
        tmp_gridmap_nodes = self.get_children(
            "required_gridmap", root=required_gridmaps_node
        )
        required_gridmap_nodes = []
        for node in tmp_gridmap_nodes:
            compset_att = self.get(node, "compset")
            not_compset_att = self.get(node, "not_compset")
            if (
                compset_att
                and not compset_att in compset
                or not_compset_att
                and not_compset_att in compset
            ):
                continue
            required_gridmap_nodes.append(node)
            mapname = self.text(node)
            if mapname not in gridmaps:
                gridmaps[mapname] = _get_unset_gridmap_value(
                    mapname, component_grids, driver
                )

        # (3) check that all necessary maps are not set to idmap
        #
        # NOTE(wjs, 2021-05-18) This could probably be combined with the above loop, but
        # I'm avoiding making that change now due to fear of breaking this complex logic
        # that isn't covered by unit tests.
        atm_gridvalue = component_grids.get_comp_gridname("atm")
        for node in required_gridmap_nodes:
            comp1_name = _strip_grid_from_name(self.get(node, "grid1"))
            comp2_name = _strip_grid_from_name(self.get(node, "grid2"))
            grid1_value = component_grids.get_comp_gridname(comp1_name)
            grid2_value = component_grids.get_comp_gridname(comp2_name)
            if grid1_value is not None and grid2_value is not None:
                if (
                    grid1_value != grid2_value
                    and grid1_value != "null"
                    and grid2_value != "null"
                ):
                    map_ = gridmaps[self.text(node)]
                    if map_ == "idmap":
                        if comp1_name == "ocn" and grid1_value == atm_gridvalue:
                            logger.debug(
                                "ocn_grid == atm_grid so this is not an idmap error"
                            )
                        else:
                            if driver == "nuopc":
                                gridmaps[self.text(node)] = "unset"
                            else:
                                logger.warning(
                                    "Warning: missing non-idmap {} for {}, {} and {} {} ".format(
                                        self.text(node),
                                        comp1_name,
                                        grid1_value,
                                        comp2_name,
                                        grid2_value,
                                    )
                                )

        return gridmaps

    def _get_gridmaps_for_one_grid_pair(
        self, gridmaps, driver, compname, other_compname, gridvalue, other_gridvalue
    ):
        """Get gridmap information for one pair of grids, adding elements to the gridmaps dictionary

        Args:
        - gridmaps: dictionary of values, modified in place
        - driver: the name of the driver being used in this case
        - compname: abbreviated name of component (e.g., "atm")
        - other_compname: abbreviated name of other component (e.g., "ocn")
        - gridvalue: name of grid for compname
        - other_gridvalue: name of grid for other_compname
        """
        gridmaps_roots = self.get_children("gridmaps")
        gridmap_nodes = []
        for root in gridmaps_roots:
            gmdriver = self.get(root, "driver")
            if gmdriver is None or gmdriver == driver:
                gridname = compname + "_grid"
                other_gridname = other_compname + "_grid"
                gridmap_nodes.extend(
                    self.get_children(
                        "gridmap",
                        root=root,
                        attributes={
                            gridname: gridvalue,
                            other_gridname: other_gridvalue,
                        },
                    )
                )

        # We first create a dictionary of gridmaps just for this pair of grids, then later
        # add these grids to the main gridmaps dict using _add_grid_info. The reason for
        # doing this in two steps, using the intermediate these_gridmaps variable, is: If
        # there are multiple definitions of a given gridmap for a given grid pair, we just
        # want to use one of them, rather than adding them all to the final gridmaps dict.
        # (This may not occur in practice, but the logic allowed for this possibility
        # before extending it to handle multiple grids for a given component, so we are
        # leaving this possibility in place.)
        these_gridmaps = {}
        for gridmap_node in gridmap_nodes:
            expect(
                len(self.attrib(gridmap_node)) == 2,
                " Bad attribute count in gridmap node %s" % self.attrib(gridmap_node),
            )
            map_nodes = self.get_children("map", root=gridmap_node)
            for map_node in map_nodes:
                name = self.get(map_node, "name")
                value = self.text(map_node)
                if name is not None and value is not None:
                    these_gridmaps[name] = value
                    logger.debug(" gridmap name,value are {}: {}".format(name, value))

        for name, value in these_gridmaps.items():
            _add_grid_info(gridmaps, name, value)

    def print_values(self, long_output=None):
        # write out help message
        helptext = self.get_element_text("help")
        logger.info("{} ".format(helptext))

        logger.info(
            "{:5s}-------------------------------------------------------------".format(
                ""
            )
        )
        logger.info("{:10s}  default component grids:\n".format(""))
        logger.info("     component         compset       value ")
        logger.info(
            "{:5s}-------------------------------------------------------------".format(
                ""
            )
        )
        default_nodes = self.get_children(
            "model_grid_defaults", root=self.get_child("grids")
        )
        for default_node in default_nodes:
            grid_nodes = self.get_children("grid", root=default_node)
            for grid_node in grid_nodes:
                name = self.get(grid_node, "name")
                compset = self.get(grid_node, "compset")
                value = self.text(grid_node)
                logger.info("     {:6s}   {:15s}   {:10s}".format(name, compset, value))
        logger.info(
            "{:5s}-------------------------------------------------------------".format(
                ""
            )
        )

        domains = {}
        if long_output is not None:
            domain_nodes = self.get_children("domain", root=self.get_child("domains"))
            for domain_node in domain_nodes:
                name = self.get(domain_node, "name")
                if name == "null":
                    continue
                desc = self.text(self.get_child("desc", root=domain_node))
                files = ""
                file_nodes = self.get_children("file", root=domain_node)
                for file_node in file_nodes:
                    filename = self.text(file_node)
                    mask_attrib = self.get(file_node, "mask")
                    grid_attrib = self.get(file_node, "grid")
                    files += "\n       " + filename
                    if mask_attrib or grid_attrib:
                        files += " (only for"
                    if mask_attrib:
                        files += " mask: " + mask_attrib
                    if grid_attrib:
                        files += " grid match: " + grid_attrib
                    if mask_attrib or grid_attrib:
                        files += ")"
                domains[name] = "\n       {} with domain file(s): {} ".format(
                    desc, files
                )

        model_grid_nodes = self.get_children("model_grid", root=self.get_child("grids"))
        for model_grid_node in model_grid_nodes:
            alias = self.get(model_grid_node, "alias")
            compset = self.get(model_grid_node, "compset")
            not_compset = self.get(model_grid_node, "not_compset")
            restriction = ""
            if compset:
                restriction += "only for compsets that are {} ".format(compset)
            if not_compset:
                restriction += "only for compsets that are not {} ".format(not_compset)
            if restriction:
                logger.info("\n     alias: {} ({})".format(alias, restriction))
            else:
                logger.info("\n     alias: {}".format(alias))
            grid_nodes = self.get_children("grid", root=model_grid_node)
            grids = ""
            gridnames = []
            for grid_node in grid_nodes:
                gridnames.append(self.text(grid_node))
                grids += self.get(grid_node, "name") + ":" + self.text(grid_node) + "  "
            logger.info("       non-default grids are: {}".format(grids))
            mask_nodes = self.get_children("mask", root=model_grid_node)
            for mask_node in mask_nodes:
                logger.info("       mask is: {}".format(self.text(mask_node)))
            if long_output is not None:
                gridnames = set(gridnames)
                for gridname in gridnames:
                    if gridname != "null":
                        logger.info("    {}".format(domains[gridname]))


# ------------------------------------------------------------------------
# Helper class: _ComponentGrids
# ------------------------------------------------------------------------


class _ComponentGrids(object):
    """This class stores the grid names for each component and allows retrieval in a variety
    of formats

    """

    # Mappings from component names to the single characters used in the grid long name.
    # Ordering is potentially important here, because it will determine the order in the
    # list returned by get_compnames, which will in turn impact ordering of components in
    # iterations.
    #
    # TODO: this should be in XML, not here
    _COMP_NAMES = OrderedDict(
        [
            ("atm", "a"),
            ("lnd", "l"),
            ("ocn", "o"),
            ("ice", "i"),
            ("rof", "r"),
            ("glc", "g"),
            ("wav", "w"),
            ("iac", "z"),
            ("mask", "m"),
        ]
    )

    def __init__(self, grid_longname):
        self._comp_gridnames = self._get_component_grids_from_longname(grid_longname)

    def _get_component_grids_from_longname(self, name):
        """Return a dictionary mapping each compname to its gridname"""
        grid_re = re.compile(r"[_]{0,1}[a-z]{1,2}%")
        grids = grid_re.split(name)[1:]
        prefixes = re.findall("[a-z]+%", name)
        component_grids = {}
        i = 0
        while i < len(grids):
            # In the following, [:-1] strips the trailing '%'
            prefix = prefixes[i][:-1]
            grid = grids[i]
            component_grids[prefix] = grid
            i += 1
        component_grids["i"] = component_grids["oi"]
        component_grids["o"] = component_grids["oi"]
        del component_grids["oi"]

        result = {}
        for compname, prefix in self._COMP_NAMES.items():
            result[compname] = component_grids[prefix]
        return result

    def get_compnames(self, include_mask=True, exclude_comps=None):
        """Return a list of all component names (lower case)

        This can be used for iterating through the grid names

        If include_mask is True (the default), then 'mask' is included in the list of
        returned component names.

        If exclude_comps is given, then it should be a list of component names to exclude
        from the returned list. For example, if it is ['ice', 'rof'], then 'ice' and 'rof'
        are NOT included in the returned list.

        """
        if exclude_comps is None:
            all_exclude_comps = []
        else:
            all_exclude_comps = exclude_comps
        if not include_mask:
            all_exclude_comps.append("mask")
        result = [k for k in self._COMP_NAMES if k not in all_exclude_comps]
        return result

    def get_comp_gridname(self, compname):
        """Return the grid name for the given component name"""
        return self._comp_gridnames[compname]

    def get_comp_gridlist(self, compname):
        """Return a list of individual grids for the given component name

        Usually this list has only a single grid (so the return value will be a
        single-element list like ["0.9x1.25"]). However, the glc component (glc) can have
        multiple grids, separated by GRID_SEP. In this situation, the return value for
        GLC will have multiple elements.

        """
        gridname = self.get_comp_gridname(compname)
        return gridname.split(GRID_SEP)

    def get_comp_numgrids(self, compname):
        """Return the number of grids for the given component name

        Usually this is one, but the glc component can have multiple grids.
        """
        return len(self.get_comp_gridlist(compname))

    def get_gridmap_total_nmaps(self, gridmap_name):
        """Given a gridmap_name like ATM2OCN_FMAPNAME, return the total number of maps needed between the two components

        In most cases, this will be 1, but if either or both components has multiple grids,
        then this will be the product of the number of grids for each component.

        """
        comp1_name, comp2_name = _get_compnames_from_mapname(gridmap_name)
        comp1_ngrids = self.get_comp_numgrids(comp1_name)
        comp2_ngrids = self.get_comp_numgrids(comp2_name)
        total_nmaps = comp1_ngrids * comp2_ngrids
        return total_nmaps

    def check_num_elements(self, gridinfo):
        """Check each member of gridinfo to make sure that it has the correct number of elements

        gridinfo is a dict mapping variable names to their values

        """
        for compname in self.get_compnames(include_mask=False):
            for name, value in gridinfo.items():
                if not isinstance(value, str):
                    # Non-string values only hold a single element, regardless of how many
                    # grids there are for a component. This is enforced in _add_grid_info
                    # by requiring value_for_multiple to be provided for non-string
                    # values. For now, it is *only* those non-string values that only
                    # carry a single element regardless of the number of grids. If, in the
                    # future, other variables are added with this property, then this
                    # logic would need to be extended to skip those variables as well.
                    # (This could be done by hard-coding some suffixes to skip here. A
                    # better alternative could be to do away with the value_for_multiple
                    # argument in _add_grid_info, instead setting a module-level
                    # dictionary mapping suffixes to their value_for_multiple, and
                    # referencing that dictionary in both _add_grid_info and here. For
                    # example: _VALUE_FOR_MULTIPLE = {'_NX': 1, '_NY': 1, '_FOO': 'bar'}.)
                    continue
                name_lower = name.lower()
                if name_lower.startswith(compname):
                    if name_lower.startswith(compname + "_"):
                        expected_num_elements = self.get_comp_numgrids(compname)
                    elif name_lower.startswith(compname + "2"):
                        expected_num_elements = self.get_gridmap_total_nmaps(name)
                    else:
                        # We don't know what to expect if the character after compname is
                        # neither "_" nor "2"
                        continue
                    if value.lower() == "unset":
                        # It's okay for there to be a single "unset" value even for a
                        # component with multiple grids
                        continue
                    num_elements = len(value.split(GRID_SEP))
                    expect(
                        num_elements == expected_num_elements,
                        "Unexpected number of colon-delimited elements in {}: {} (expected {} elements)".format(
                            name, value, expected_num_elements
                        ),
                    )


# ------------------------------------------------------------------------
# Some helper functions
# ------------------------------------------------------------------------


def _get_compnames_from_mapname(mapname):
    """Given a mapname like ATM2OCN_FMAPNAME, return the two component names

    The returned component names are lowercase. So, for example, if mapname is
    ATM2OCN_FMAPNAME, then this function returns a tuple ('atm', 'ocn')

    """
    comp1_name = mapname[0:3].lower()
    comp2_name = mapname[4:7].lower()
    return comp1_name, comp2_name


def _strip_grid_from_name(name):
    """Given some string 'name', strip trailing '_grid' from name and return result

    Raises an exception if 'name' doesn't end with '_grid'
    """
    expect(name.endswith("_grid"), "{} does not end with _grid".format(name))
    return name[: -len("_grid")]


def _add_grid_info(info_dict, key, value, value_for_multiple=None):
    """Add a value to info_dict, handling the possibility of multiple grids for a component

    In the basic case, where key is not yet present in info_dict, this is equivalent to
    setting:
        info_dict[key] = value

    However, if the given key is already present, then instead of overriding the old
    value, we instead concatenate, separated by GRID_SEP. This is used in case there are
    multiple grids for a given component. An exception to this behavior is: If
    value_for_multiple is specified (not None) then, if we find an existing value, then we
    instead replace the value with the value given by value_for_multiple.

    value_for_multiple must be specified if value is not a string

    """
    if not isinstance(value, str):
        expect(
            value_for_multiple is not None,
            "_add_grid_info: value_for_multiple must be specified if value is not a string",
        )
    if key in info_dict:
        if value_for_multiple is not None:
            info_dict[key] = value_for_multiple
        else:
            info_dict[key] += GRID_SEP + value
    else:
        info_dict[key] = value


def _get_unset_gridmap_value(mapname, component_grids, driver):
    """Return the appropriate setting for a given gridmap that has not been explicitly set

    This will be 'unset' or 'idmap' depending on various parameters.
    """
    if driver == "nuopc":
        comp1_name, comp2_name = _get_compnames_from_mapname(mapname)
        grid1 = component_grids.get_comp_gridname(comp1_name)
        grid2 = component_grids.get_comp_gridname(comp2_name)
        if grid1 == grid2:
            if grid1 != "null" and grid2 != "null":
                gridmap = "idmap"
            else:
                gridmap = "unset"
        else:
            gridmap = "unset"
    else:
        gridmap = "idmap"

    return gridmap
