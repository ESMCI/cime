from collections import OrderedDict
import tempfile
import unittest
from unittest import mock

from CIME.nmlgen import NamelistGenerator

# pylint: disable=protected-access
class TestNamelistGenerator(unittest.TestCase):
    def test_init_defaults(self):
        test_nml_infile = b"""&test
test1 = 'test1_updated'
/"""

        test_data = """<?xml version="1.0"?>
<?xml-stylesheet type="text/xsl" href="http://www.cgd.ucar.edu/~cam/namelist/namelist_definition.xsl"?>

<entry_id version="2.0">
    <entry id="test1">
        <type>char</type>
        <category>test</category>
        <group>test_nml</group>
        <valid_values>test1_value,test1_updated</valid_values>
        <values>
            <value>test1_value</value>
        </values>
    </entry>
    <entry id="test2">
        <type>char</type>
        <category>test</category>
        <group>test_nml</group>
        <values>
            <value>test2_value</value>
        </values>
    </entry>
</entry_id>"""

        with tempfile.NamedTemporaryFile() as temp, tempfile.NamedTemporaryFile() as temp2:
            temp.write(test_data.encode())
            temp.flush()

            temp2.write(test_nml_infile)
            temp2.flush()

            case = mock.MagicMock()

            nmlgen = NamelistGenerator(case, [temp.name])

            nmlgen.init_defaults([temp2.name], None)

            expected_groups = OrderedDict(
                {"test_nml": {"test1": ["'test1_updated'"], "test2": ['"test2_value"']}}
            )

            assert nmlgen._namelist._groups == expected_groups


if __name__ == "__main__":
    unittest.main()
