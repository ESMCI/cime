import unittest
from paramgen import ParamGen

class TestParamGen(unittest.TestCase):
    """ A unit test class for testing ParamGen. """

    def test_init_data(self):
        """ Tests the ParamGen initializer with and without an initial data. """
        # empty
        obj = ParamGen({})
        # with data
        data_dict = {'a': 1, 'b': 2}
        obj = ParamGen(data_dict)

    def test_reduce(self):
        """ Tests the reduce method of ParamGen on data with explicit guards (True or False). """
        data_dict = {'False': 1, 'True': 2}
        obj = ParamGen(data_dict)
        obj.reduce()
        self.assertEqual(obj.data, 2)

    def test_nested_reduce(self):
        """ Tests the reduce method of ParamGen on data with nested guards. """
        data_dict = {
            'False': 1,
            'True': {
                "2>3": 0,
                "2<3": 2
            }
        }
        obj = ParamGen(data_dict)
        obj.reduce()
        self.assertEqual(obj.data, 2)

    def test_outer_guards(self):
        """ Tests the reduce method on data with outer guards enclosing parameter definitions. """
        data_dict = {
            'False': {
                'param': 'foo'
            },
            'True': {
                'param': 'bar'
            },
        }
        obj = ParamGen(data_dict)
        obj.reduce()
        self.assertEqual(obj.data, {'param':'bar'})

    def test_match(self):
        """ Tests the default behavior of returning the last match and the optional behavior of returning the
        first match. """

        data_dict = {
            '1<2': 'foo',
            '2<3': 'bar',
            '3<4': 'baz',
        }

        obj = ParamGen(data_dict) # by default, match='last'
        obj.reduce()
        self.assertEqual(obj.data, 'baz')

        obj = ParamGen(data_dict, match='first')
        obj.reduce()
        self.assertEqual(obj.data, 'foo')

    def test_undefined_var(self):
        """ Tests the reduce method of ParamGen on nested guards where an undefined expandable var is specified
        below a guard that evaluates to False. The undefined var should not lead to an error since the enclosing
        guard evaluates to false. """

        # define an expansion function, i.e., a mapping for expandable var names to their values
        map = {'alpha': 1, 'beta': False}
        expand_func = lambda var: map[var]

        # define a data dict
        data_dict = {
            'param':
            {
                '$alpha >= 1': 'foo',
                '${beta}':{
                    '${zeta}': 'bar'
                }
            }
        }

        # Instantiate a ParamGen object and reduce its data to obtain the final parameter set
        obj = ParamGen(data_dict)
        obj.reduce(expand_func)
        self.assertEqual(obj.data, {'param':'foo'})

    def test_expandable_vars(self):
        """ Tests the reduce method of ParamGen expandable vars in guards. """

        # define an expansion function, i.e., a mapping for expandable var names to their values
        map = {'alpha': 1, 'beta': False, 'gamma': 'xyz'}
        expand_func = lambda var: map[var]

        # define a data dict
        data_dict = {
            'param':
            {
                '$alpha > 1': 'foo',
                '${beta}': 'bar',
                '"x" in $gamma': 'baz'
            }
        }

        # Instantiate a ParamGen object and reduce its data to obtain the final parameter set
        obj = ParamGen(data_dict)
        obj.reduce(expand_func)
        self.assertEqual(obj.data, {'param':'baz'})

    def test_formula_expansion(self):
        """ Tests the formula expansion feature of ParamGen. """

        # define an expansion function, i.e., a mapping for expandable var names to their values
        map = {'alpha': 3}
        expand_func = lambda var: map[var]

        # define a data dict
        data_dict = {
            'x': '= $alpha **2',
            'y': '= [i for i in range(3)]'
        }

        # Instantiate a ParamGen object and reduce its data to obtain the final parameter set
        obj = ParamGen(data_dict)
        obj.reduce(expand_func)
        self.assertEqual(obj.data['x'], 9)
        self.assertEqual(obj.data['y'], [0,1,2])

if __name__ == '__main__':
    unittest.main()