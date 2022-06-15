import unittest
from sys import path

path.append("..")
from paramgen import ParamGen


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


class TestYamlConstructor(unittest.TestCase):
    """A unit test class for testing ParamGen's yaml constructor."""

    def test_mom_input(self):
        """ " Test MOM_input file generation via a subset of original MOM_input.yaml"""
        mom_input = ParamGen.from_yaml("yaml_test_files/MOM_input.yaml")

        def input_data_list_expand_func(varname):
            val = case.get_value(varname)
            if val == None:
                val = str(mom_input.data["Global"][varname]["value"]).strip()
            if val == None:
                raise RuntimeError("Cannot determine the value of variable: " + varname)
            return val

        mom_input.reduce(input_data_list_expand_func)
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
        """ " Test mom.input_data_list file generation via a subset of original input_data_list.yaml"""
        mom_input = ParamGen.from_yaml("yaml_test_files/MOM_input.yaml")

        def input_data_list_expand_func(varname):
            val = case.get_value(varname)
            if val == None:
                val = str(mom_input.data["Global"][varname]["value"]).strip()
            if val == None:
                raise RuntimeError("Cannot determine the value of variable: " + varname)
            return val

        mom_input.reduce(input_data_list_expand_func)

        input_data_list = ParamGen.from_yaml("yaml_test_files/mom.input_data_list.yaml")
        input_data_list.reduce(input_data_list_expand_func)
        self.assertEqual(
            input_data_list.data,
            {
                "mom.input_data_list": {
                    "ocean_hgrid": "/foo/inputdata/ocn/mom/tx0.66v1/ocean_hgrid_180829.nc",
                    "tempsalt": "/foo/inputdata/ocn/mom/tx0.66v1/woa18_04_initial_conditions.nc",
                }
            },
        )


if __name__ == "__main__":
    unittest.main()
