#!/usr/bin/env python3

"""
This module tests *some* functionality of CIME.ParamGen.paramgen's ParamGen class
"""

# Ignore privacy concerns for unit tests, so that unit tests can access
# protected members of the system under test
#
# pylint:disable=protected-access

# Also ignore too-long lines, since these are common in unit tests
#
# pylint:disable=line-too-long

import unittest
import tempfile
from CIME.ParamGen.paramgen import ParamGen

###############
# Example inputs
###############

_MOM_INPUT_YAML = """
Global:
    INPUTDIR:
        value: ${DIN_LOC_ROOT}/ocn/mom/${OCN_GRID}
    RESTORE_SALINITY:
        value:
            $OCN_GRID == "tx0.66v1" and $COMP_ATM == "datm": True  # for C and G compsets on tx0.66v1
            else: False
    INIT_LAYERS_FROM_Z_FILE:
        value:
            $OCN_GRID == "gx1v6": True
            $OCN_GRID == "tx0.66v1": True
            $OCN_GRID == "tx0.25v1": True
    TEMP_SALT_Z_INIT_FILE:
        value:
            $OCN_GRID == "gx1v6": "WOA05_pottemp_salt.nc"
            $OCN_GRID == "tx0.66v1": "woa18_04_initial_conditions.nc"
            $OCN_GRID == "tx0.25v1": "MOM6_IC_TS.nc"
"""

_MOM_INPUT_DATA_LIST_YAML = """
mom.input_data_list:
    ocean_hgrid:
        $OCN_GRID == "gx1v6":    "${INPUTDIR}/ocean_hgrid.nc"
        $OCN_GRID == "tx0.66v1": "${INPUTDIR}/ocean_hgrid_180829.nc"
        $OCN_GRID == "tx0.25v1": "${INPUTDIR}/ocean_hgrid.nc"
    tempsalt:
        $OCN_GRID in ["gx1v6", "tx0.66v1", "tx0.25v1"]:
            $INIT_LAYERS_FROM_Z_FILE == "True":
                "${INPUTDIR}/${TEMP_SALT_Z_INIT_FILE}"
"""

_MY_TEMPLATE_XML = """<?xml version="1.0"?>

<entry_id_pg version="0.1">

  <entry id="foo">
    <type>string</type>
    <group>test_nml</group>
    <desc>a dummy parameter for testing single key=value guards</desc>
    <values>
      <value>alpha</value>
      <value cice_mode="thermo_only">beta</value>
      <value cice_mode="prescribed">gamma</value>
    </values>
  </entry>

  <entry id="bar">
    <type>string</type>
    <group>test_nml</group>
    <desc>another dummy parameter for multiple key=value guards mixed with explicit (flexible) guards</desc>
    <values>
      <value some_int="2" some_bool="True" some_float="3.1415">delta</value>
      <value guard='$ICE_GRID .startswith("gx1v")'>epsilon</value>
    </values>
  </entry>

  <entry id="baz">
    <type>string</type>
    <group>test_nml</group>
    <desc>parameter to test the case where there is no match</desc>
    <values>
      <value some_int="-9999">zeta</value>
      <value guard='not $ICE_GRID .startswith("gx1v")'>eta</value>
    </values>
  </entry>

  </entry_id_pg>
"""

_DUPLICATE_IDS_XML = """<?xml version="1.0"?>

<entry_id_pg version="0.1">

  <entry id="foo">
    <type>string</type>
    <group>test_nml</group>
    <desc>a dummy parameter for testing single key=value guards</desc>
    <values>
      <value>alpha</value>
      <value cice_mode="thermo_only">beta</value>
      <value cice_mode="prescribed">gamma</value>
    </values>
  </entry>

  <entry id="foo">
    <type>string</type>
    <group>test_nml</group>
    <desc>another dummy parameter for multiple key=value guards mixed with explicit (flexible) guards</desc>
    <values>
      <value some_int="2" some_bool="True" some_float="3.1415">delta</value>
      <value guard='$ICE_GRID .startswith("gx1v")'>epsilon</value>
    </values>
  </entry>

  </entry_id_pg>
"""

############################
# Dummy functions and classes
############################


class DummyCase:
    """A dummy Case class that mimics CIME class objects' get_value method."""

    def get_value(self, varname):
        d = {
            "DIN_LOC_ROOT": "/foo/inputdata",
            "OCN_GRID": "tx0.66v1",
            "COMP_ATM": "datm",
        }
        return d[varname] if varname in d else None


case = DummyCase()

#####


def _expand_func_demo(varname):
    return {
        "ICE_GRID": "gx1v6",
        "DIN_LOC_ROOT": "/glade/p/cesmdata/cseg/inputdata",
        "cice_mode": "thermo_only",
        "some_bool": "True",
        "some_int": 2,
        "some_float": "3.1415",
    }[varname]


################
# Unitest classes
################


class TestParamGen(unittest.TestCase):
    """
    Tests some basic functionality of the
    CIME.ParamGen.paramgen's ParamGen class
    """

    def test_init_data(self):
        """Tests the ParamGen initializer with and without an initial data."""
        # empty
        _ = ParamGen({})
        # with data
        data_dict = {"a": 1, "b": 2}
        _ = ParamGen(data_dict)

    def test_reduce(self):
        """Tests the reduce method of ParamGen on data with explicit guards (True or False)."""
        data_dict = {"False": 1, "True": 2}
        obj = ParamGen(data_dict)
        obj.reduce()
        self.assertEqual(obj.data, 2)

    def test_nested_reduce(self):
        """Tests the reduce method of ParamGen on data with nested guards."""
        data_dict = {"False": 1, "True": {"2>3": 0, "2<3": 2}}
        obj = ParamGen(data_dict)
        obj.reduce()
        self.assertEqual(obj.data, 2)

    def test_outer_guards(self):
        """Tests the reduce method on data with outer guards enclosing parameter definitions."""
        data_dict = {
            "False": {"param": "foo"},
            "True": {"param": "bar"},
        }
        obj = ParamGen(data_dict)
        obj.reduce()
        self.assertEqual(obj.data, {"param": "bar"})

    def test_match(self):
        """Tests the default behavior of returning the last match and the optional behavior of returning the
        first match."""

        data_dict = {
            "1<2": "foo",
            "2<3": "bar",
            "3<4": "baz",
        }

        obj = ParamGen(data_dict)  # by default, match='last'
        obj.reduce()
        self.assertEqual(obj.data, "baz")

        obj = ParamGen(data_dict, match="first")
        obj.reduce()
        self.assertEqual(obj.data, "foo")

    def test_undefined_var(self):
        """Tests the reduce method of ParamGen on nested guards where an undefined expandable var is specified
        below a guard that evaluates to False. The undefined var should not lead to an error since the enclosing
        guard evaluates to false."""

        # define an expansion function, i.e., a mapping for expandable var names to their values
        test_map = {"alpha": 1, "beta": False}
        expand_func = lambda var: test_map[var]

        # define a data dict
        data_dict = {"param": {"$alpha >= 1": "foo", "${beta}": {"${zeta}": "bar"}}}

        # Instantiate a ParamGen object and reduce its data to obtain the final parameter set
        obj = ParamGen(data_dict)
        obj.reduce(expand_func)
        self.assertEqual(obj.data, {"param": "foo"})

    def test_expandable_vars(self):
        """Tests the reduce method of ParamGen expandable vars in guards."""

        # define an expansion function, i.e., a mapping for expandable var names to their values
        test_map = {"alpha": 1, "beta": False, "gamma": "xyz"}
        expand_func = lambda var: test_map[var]

        # define a data dict
        data_dict = {
            "param": {"$alpha > 1": "foo", "${beta}": "bar", '"x" in $gamma': "baz"}
        }

        # Instantiate a ParamGen object and reduce its data to obtain the final parameter set
        obj = ParamGen(data_dict)
        obj.reduce(expand_func)
        self.assertEqual(obj.data, {"param": "baz"})

    def test_formula_expansion(self):
        """Tests the formula expansion feature of ParamGen."""

        # define an expansion function, i.e., a mapping for expandable var names to their values
        test_map = {"alpha": 3}
        expand_func = lambda var: test_map[var]

        # define a data dict
        data_dict = {"x": "= $alpha **2", "y": "= [i for i in range(3)]"}

        # Instantiate a ParamGen object and reduce its data to obtain the final parameter set
        obj = ParamGen(data_dict)
        obj.reduce(expand_func)
        self.assertEqual(obj.data["x"], 9)
        self.assertEqual(obj.data["y"], [0, 1, 2])


#####


class TestParamGenYamlConstructor(unittest.TestCase):
    """A unit test class for testing ParamGen's yaml constructor."""

    def test_mom_input(self):
        """Test MOM_input file generation via a subset of original MOM_input.yaml"""

        # Create temporary YAML file:
        with tempfile.NamedTemporaryFile() as temp:
            temp.write(_MOM_INPUT_YAML.encode())
            temp.flush()

            # Open YAML file using ParamGen:
            mom_input = ParamGen.from_yaml(temp.name)

        # Define a local ParamGen reducing function:
        def input_data_list_expand_func(varname):
            val = case.get_value(varname)
            if val == None:
                val = str(mom_input.data["Global"][varname]["value"]).strip()
            if val == None:
                raise RuntimeError("Cannot determine the value of variable: " + varname)
            return val

        # Reduce ParamGen entries:
        mom_input.reduce(input_data_list_expand_func)

        # Check output:
        self.assertEqual(
            mom_input.data,
            {
                "Global": {
                    "INPUTDIR": {"value": "/foo/inputdata/ocn/mom/tx0.66v1"},
                    "RESTORE_SALINITY": {"value": True},
                    "INIT_LAYERS_FROM_Z_FILE": {"value": True},
                    "TEMP_SALT_Z_INIT_FILE": {
                        "value": "woa18_04_initial_conditions.nc"
                    },
                }
            },
        )

    def test_input_data_list(self):
        """Test mom.input_data_list file generation via a subset of original input_data_list.yaml"""

        # Create temporary YAML file:
        with tempfile.NamedTemporaryFile() as temp:
            temp.write(_MOM_INPUT_YAML.encode())
            temp.flush()

            # Open YAML file using ParamGen:
            mom_input = ParamGen.from_yaml(temp.name)

        # Define a local ParamGen reducing function:
        def input_data_list_expand_func(varname):
            val = case.get_value(varname)
            if val == None:
                val = str(mom_input.data["Global"][varname]["value"]).strip()
            if val == None:
                raise RuntimeError("Cannot determine the value of variable: " + varname)
            return val

        # Reduce ParamGen entries:
        mom_input.reduce(input_data_list_expand_func)

        # Create a second temporary YAML file:
        with tempfile.NamedTemporaryFile() as temp2:
            temp2.write(_MOM_INPUT_DATA_LIST_YAML.encode())
            temp2.flush()

            # Open second YAML file using ParamGen:
            input_data_list = ParamGen.from_yaml(temp2.name)

        # Reduce ParamGen entries:
        input_data_list.reduce(input_data_list_expand_func)

        # Check output:
        self.assertEqual(
            input_data_list.data,
            {
                "mom.input_data_list": {
                    "ocean_hgrid": "/foo/inputdata/ocn/mom/tx0.66v1/ocean_hgrid_180829.nc",
                    "tempsalt": "/foo/inputdata/ocn/mom/tx0.66v1/woa18_04_initial_conditions.nc",
                }
            },
        )


#####


class TestParamGenXmlConstructor(unittest.TestCase):
    """A unit test class for testing ParamGen's xml constructor."""

    def test_single_key_val_guard(self):
        """Test xml entry values with single key=value guards"""

        # Create temporary YAML file:
        with tempfile.NamedTemporaryFile() as temp:
            temp.write(_MY_TEMPLATE_XML.encode())
            temp.flush()

            # Open XML file using ParamGen:
            pg = ParamGen.from_xml_nml(temp.name)

        # Reduce ParamGen entries:
        pg.reduce(_expand_func_demo)

        # Check output:
        self.assertEqual(pg.data["test_nml"]["foo"]["values"], "beta")

    def test_mixed_guard(self):
        """Tests multiple key=value guards mixed with explicit (flexible) guards."""

        # Create temporary YAML file:
        with tempfile.NamedTemporaryFile() as temp:
            temp.write(_MY_TEMPLATE_XML.encode())
            temp.flush()

            # Open XML file using ParamGen:
            pg = ParamGen.from_xml_nml(temp.name)

        # Reduce ParamGen entries:
        pg.reduce(_expand_func_demo)

        # Check output:
        self.assertEqual(pg.data["test_nml"]["bar"]["values"], "epsilon")

    def test_mixed_guard_first(self):
        """Tests multiple key=value guards mixed with explicit (flexible) guards
        with match=first option."""

        # Create temporary YAML file:
        with tempfile.NamedTemporaryFile() as temp:
            temp.write(_MY_TEMPLATE_XML.encode())
            temp.flush()

            # Open XML file using ParamGen:
            pg = ParamGen.from_xml_nml(temp.name, match="first")

        # Reduce ParamGen entries:
        pg.reduce(_expand_func_demo)

        # Check output:
        self.assertEqual(pg.data["test_nml"]["bar"]["values"], "delta")

    def test_no_match(self):
        """Tests an xml entry with no match, i.e., no guards evaluating to True."""

        # Create temporary YAML file:
        with tempfile.NamedTemporaryFile() as temp:
            temp.write(_MY_TEMPLATE_XML.encode())
            temp.flush()

            # Open XML file using ParamGen:
            pg = ParamGen.from_xml_nml(temp.name)

        # Reduce ParamGen entries:
        pg.reduce(_expand_func_demo)

        # Check output:
        self.assertEqual(pg.data["test_nml"]["baz"]["values"], None)

    def test_default_var(self):
        """Test to check if default val is assigned when all guards eval to False"""

        # Create temporary YAML file:
        with tempfile.NamedTemporaryFile() as temp:
            temp.write(_MY_TEMPLATE_XML.encode())
            temp.flush()

            # Open XML file using ParamGen:
            pg = ParamGen.from_xml_nml(temp.name)

        # Reduce ParamGen entries:
        pg.reduce(lambda varname: "_")

        # Check output:
        self.assertEqual(pg.data["test_nml"]["foo"]["values"], "alpha")

    def test_duplicate_entry_error(self):
        """
        Test to make sure duplicate ids raise the correct error
        when the "no_duplicates" flag is True.
        """
        with self.assertRaises(ValueError) as verr:

            # Create temporary YAML file:
            with tempfile.NamedTemporaryFile() as temp:
                temp.write(_DUPLICATE_IDS_XML.encode())
                temp.flush()

                _ = ParamGen.from_xml_nml(temp.name, no_duplicates=True)

            emsg = "Entry id 'foo' listed twice in file:\n'./xml_test_files/duplicate_ids.xml'"
            self.assertEqual(emsg, str(verr.exception))


if __name__ == "__main__":
    unittest.main()
