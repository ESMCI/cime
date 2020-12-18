
from __future__ import print_function
from collections import OrderedDict
import os
import re
from abc import ABC, abstractmethod
from copy import deepcopy
from paramgen_utils import get_str_type, is_logical_expr
from paramgen_utils import has_expandable_var, eval_formula

class ParamGen(ABC):
    """
    Base class for CIME Flexible Parameter Generator.
    Attributes
    ----------
    data : dict or OrderedDict
        The data attribute to operate over. See Methods for the list of operations.
    Methods
    -------
    from_json(input_path)
        Reads in a given json input file and initializes a ParamGen object.
    from_yaml(input_path)
        Reads in a given yalm input file and initializes a ParamGen object.
    """

    def __init__(self, data_dict, match='last'):
        assert type(data_dict) in [dict, OrderedDict], \
            "ParamGen class requires a dict or OrderedDict as the initial data."
        #self._validate_schema(data_dict)
        self._data = deepcopy(data_dict)
        self._reduced = False
        self._match = match

    @property
    def data(self):
        """Returns the data attribute of the ParamGen instance."""
        return self._data

    @classmethod
    def from_json(cls, input_path):
        """
        Reads in a given json input file and initializes a ParamGen object.
        Parameters
        ----------
        input_path: str
            Path to json input file containing the defaults.
        Returns
        -------
        ParamGen
            A ParamGen object with the data read from input_path.
        """

        import json
        with open(input_path) as json_file:
            _data = json.load(json_file, object_pairs_hook=OrderedDict)
        return cls(_data)

    @classmethod
    def from_yaml(cls, input_path):
        """
        Reads in a given yaml input file and initializes a ParamGen object.
        Parameters
        ----------
        input_path: str
            Path to yaml input file containing the defaults.
        Returns
        -------
        ParamGen
            A ParamGen object with the data read from input_path.
        """

        import yaml
        with open(input_path) as yaml_file:
            _data = yaml.safe_load(yaml_file)
        return cls(_data)


    @classmethod
    def expand_var(cls, expr, expand_func):
        assert isinstance(expr, get_str_type()), "Expression passed to expand_var must be string."
        expandable_vars = re.findall(r'(\$\w+|\${\w+\})',expr)
        for word in expandable_vars:
            word_stripped = word.\
                replace("$","").\
                replace("{","").\
                replace("}","")
            word_expanded = expand_func(word_stripped)
            assert word_expanded!=None, "Cannot expand the variable "+word+" using the given expand_func."
            expr = expr.replace(word,word_expanded)
        return expr

    def _impose_guards(self, data_dict):

        def _is_guarded_dict():
            """ returns true if all the keys of a dictionary are logical expressions, i.e., guards."""
            assert type(data_dict) in [dict, OrderedDict]

            keys_logical = [is_logical_expr(str(key)) for key in data_dict]
            if all(keys_logical):
                return True
            elif any(keys_logical):
                print("data_dict: ", data_dict)
                raise RuntimeError("Only subset of the keys of the above dict are guards, i.e., logical expressions")
            else:
                return False

        def _eval_guard(guard):
            """ returns true if a guard evaluates to true."""
            assert isinstance(guard, get_str_type()), "Expression passed to expand_var must be string."

            if has_expandable_var(guard):
                raise RuntimeError("The guard "+guard+" has an expandable case variable! "+\
                    "All variables must already be expanded before guards can be evaluated.")
            
            guard_evaluated = eval_formula(guard)
            assert type(guard_evaluated)==type(True), "Guard is not boolean: "+guard
            return guard_evaluated


        if not _is_guarded_dict():
            return data_dict
        else:

            guards_eval_true = [] # list of guards that evaluate to true.
            for guard in data_dict:
                if guard=="else" or _eval_guard(str(guard)) == True:
                    guards_eval_true.append(guard)
                    
            if len(guards_eval_true)>1 and "else" in guards_eval_true:
                guards_eval_true.remove("else")
            
            if self._match == 'first':
                return data_dict[guards_eval_true[0]]
            elif self._match == 'last':
                return data_dict[guards_eval_true[-1]]
            else:
                raise RuntimeError("Unknown match option.")


    def _reduce_bfirst(self, data_dict, expand_func):
 
        # data copy to manipulate while iterating over original.
        # while the original data is a dictionary, the reduced data
        # may be a single element depending on the "guards".
        reduced_data = data_dict.copy()

        # First, expand the variables in keys:
        for key in data_dict:
            if has_expandable_var(key):
                new_key = ParamGen.expand_var(key, expand_func)
                reduced_data[new_key] = reduced_data.pop(key)

        # Now, evaluate guards if all the keys ofdata_dict are guards, i.e., logical expressions
        reduced_data = self._impose_guards(reduced_data)

        # if the reduced data is still a dictionary, recursively call _reduce_bfirst before returning
        if isinstance(reduced_data,(dict,OrderedDict)):

            keys_of_remaining_dicts = []
            for key, val in reduced_data.items():
                if isinstance(val,(dict,OrderedDict)):
                    keys_of_remaining_dicts.append(key)
                else:
                    print(val)

            for key in keys_of_remaining_dicts:
                reduced_data[key] = self._reduce_bfirst(reduced_data[key], expand_func)

        return reduced_data


    def reduce(self, expand_func, search_method="bfirst"):
        """
        Reduces the data of a ParamGen instances by recursively (1) expanding its variables,
        (2) dropping entries whose conditional guards evaluate to true and (3) evaluating
        formulas to determine the final values
        """

        assert callable(expand_func), "expand_func argument must be a function"
        assert not self._reduced, "ParamGen data already reduced."
        assert len(self._data)>0, "Empty ParamGen data."

        if search_method=="bfirst":
            self._data = self._reduce_bfirst(self._data, expand_func)
        #elif search_method=="dfirst"
        #    todo
        else:
            raise RuntimeError("Unknown search method.")

        self._reduced = True