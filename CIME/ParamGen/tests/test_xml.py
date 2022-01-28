import unittest
from sys import path; path.append('..')
from paramgen import ParamGen

def expand_func_demo(varname):
    return {
    'ICE_GRID': 'gx1v6',
    'DIN_LOC_ROOT': '/glade/p/cesmdata/cseg/inputdata',
    'cice_mode': 'thermo_only',
    'some_bool': "True",
    'some_int': 2,
    'some_float': "3.1415",
    }[varname]

class TestXmlConstructor(unittest.TestCase):
    """ A unit test class for testing ParamGen's xml namelist constructor. """

    def test_single_key_val_guard(self):
        """Test xml entry values with single key=value guards"""
        pg = ParamGen.from_xml_nml("./xml/my_template.xml")
        pg.reduce(expand_func_demo)
        self.assertEqual(pg.data['test_nml']['foo']['values'], 'beta')

    def test_mixed_guard(self):
        """Tests multiple key=value guards mixed with explicit (flexible) guards."""
        pg = ParamGen.from_xml_nml("./xml/my_template.xml")
        pg.reduce(expand_func_demo)
        self.assertEqual(pg.data['test_nml']['bar']['values'], 'epsilon')

    def test_mixed_guard_first(self):
        """Tests multiple key=value guards mixed with explicit (flexible) guards
        with match=first option."""
        pg = ParamGen.from_xml_nml("./xml/my_template.xml", match="first")
        pg.reduce(expand_func_demo)
        self.assertEqual(pg.data['test_nml']['bar']['values'], 'delta')

    def test_no_match(self):
        """Tests an xml entry with no match, i.e., no guards evaluating to True."""
        pg = ParamGen.from_xml_nml("./xml/my_template.xml")
        pg.reduce(expand_func_demo)
        self.assertEqual(pg.data['test_nml']['baz']['values'], None)

    def test_default_var(self):
        """Test to check if default val is assigned when all guards eval to False"""
        pg = ParamGen.from_xml_nml("./xml/my_template.xml")
        pg.reduce(lambda varname: "_")
        self.assertEqual(pg.data['test_nml']['foo']['values'], 'alpha')

    def test_duplicate_entry_error(self):
        """
        Test to make sure duplicate ids raise the correct error
        when the "no_duplicates" flag is True.
        """
        with self.assertRaises(ValueError) as verr:
            pg = ParamGen.from_xml_nml("./xml/duplicate_ids.xml",
                                       no_duplicates=True)

        emsg = "Entry id 'foo' listed twice in file:\n'./xml/duplicate_ids.xml'"
        self.assertEqual(emsg, str(verr.exception))

if __name__ == '__main__':
    unittest.main()
