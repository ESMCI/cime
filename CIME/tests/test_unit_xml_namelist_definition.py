import tempfile
import unittest

from CIME.XML.namelist_definition import NamelistDefinition

# pylint: disable=protected-access


class TestXMLNamelistDefinition(unittest.TestCase):
    def test_set_nodes(self):
        test_data = """<?xml version="1.0"?>
<?xml-stylesheet type="text/xsl" href="http://www.cgd.ucar.edu/~cam/namelist/namelist_definition.xsl"?>

<entry_id version="2.0">
    <entry id="test1">
        <type>char</type>
        <category>test</category>
    </entry>
    <entry id="test2">
        <type>char</type>
        <category>test</category>
    </entry>
</entry_id>"""

        with tempfile.NamedTemporaryFile() as temp:
            temp.write(test_data.encode())
            temp.flush()

            nmldef = NamelistDefinition(temp.name)

            nmldef.set_nodes()

            assert len(nmldef._entry_nodes) == 2
            assert nmldef._entry_ids == ["test1", "test2"]
            assert len(nmldef._nodes) == 2
            assert nmldef._entry_types == {"test1": "char", "test2": "char"}
            assert nmldef._valid_values == {"test1": None, "test2": None}
            assert nmldef._group_names == {"test1": None, "test2": None}


if __name__ == "__main__":
    unittest.main()
