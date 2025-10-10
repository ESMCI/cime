import tempfile
import unittest

from CIME.XML.namelist_definition import NamelistDefinition

# pylint: disable=protected-access


class TestXMLNamelistDefinition(unittest.TestCase):
    def test_set_nodes_basic(self):
        test_data = """<?xml version="1.0"?>
<?xml-stylesheet type="text/xsl" href="http://www.cgd.ucar.edu/~cam/namelist/namelist_definition.xsl"?>

<entry_id version="2.0">
    <entry id="test1">
        <type>char</type>
        <category>test</category>
    </entry>
    <entry id="test2">
        <type>real</type>
        <category>test</category>
    </entry>
</entry_id>"""

        with tempfile.NamedTemporaryFile() as temp:
            temp.write(test_data.encode())
            temp.flush()

            nmldef = NamelistDefinition(temp.name)

        nmldef.set_nodes()

        assert nmldef._var_names == ["test1", "test2"]
        assert nmldef._nodes.keys() == {"test1", "test2"}
        assert nmldef._entry_types == {"test1": "char", "test2": "real"}
        assert nmldef._valid_values == {"test1": None, "test2": None}
        assert nmldef._group_names == {"test1": None, "test2": None}

    def test_set_nodes_multi_variable_mappings_two(self):
        """
        Test set_nodes with an entry in multi_variable_mappings that maps to two final variables
        """
        test_data = """<?xml version="1.0"?>
<?xml-stylesheet type="text/xsl" href="http://www.cgd.ucar.edu/~cam/namelist/namelist_definition.xsl"?>

<entry_id version="2.0">
    <entry id="test1">
        <type>char</type>
        <category>test</category>
    </entry>
    <entry id="test2" multi_variable_entry="true">
        <type>real</type>
        <category>test</category>
    </entry>
</entry_id>"""

        with tempfile.NamedTemporaryFile() as temp:
            temp.write(test_data.encode())
            temp.flush()

            nmldef = NamelistDefinition(temp.name)

        multi_variable_mappings = {"test2": ["test2_a", "test2_b"]}
        nmldef.set_nodes(multi_variable_mappings=multi_variable_mappings)

        assert nmldef._var_names == ["test1", "test2_a", "test2_b"]
        assert nmldef._nodes.keys() == {"test1", "test2_a", "test2_b"}
        assert nmldef._entry_types == {
            "test1": "char",
            "test2_a": "real",
            "test2_b": "real",
        }
        assert nmldef._valid_values == {"test1": None, "test2_a": None, "test2_b": None}
        assert nmldef._group_names == {"test1": None, "test2_a": None, "test2_b": None}

    def test_set_nodes_multi_variable_mappings_zero(self):
        """
        Test set_nodes with an entry in multi_variable_mappings that maps to zero final variables
        """
        test_data = """<?xml version="1.0"?>
<?xml-stylesheet type="text/xsl" href="http://www.cgd.ucar.edu/~cam/namelist/namelist_definition.xsl"?>

<entry_id version="2.0">
    <entry id="test1">
        <type>char</type>
        <category>test</category>
    </entry>
    <entry id="test2" multi_variable_entry="true">
        <type>real</type>
        <category>test</category>
    </entry>
</entry_id>"""

        with tempfile.NamedTemporaryFile() as temp:
            temp.write(test_data.encode())
            temp.flush()

            nmldef = NamelistDefinition(temp.name)

        multi_variable_mappings = {"test2": []}
        nmldef.set_nodes(multi_variable_mappings=multi_variable_mappings)

        assert nmldef._var_names == ["test1"]
        assert nmldef._nodes.keys() == {"test1"}
        assert nmldef._entry_types == {"test1": "char"}
        assert nmldef._valid_values == {"test1": None}
        assert nmldef._group_names == {"test1": None}


if __name__ == "__main__":
    unittest.main()
