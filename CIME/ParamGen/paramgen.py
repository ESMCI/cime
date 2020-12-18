
from __future__ import print_function
from collections import OrderedDict
import os
import re
from abc import ABC, abstractmethod
from copy import deepcopy
from paramgen_utils import get_str_type, is_logical_expr
from paramgen_utils import has_expandable_var

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

    def __init__(self, data_dict):
        assert type(data_dict) in [dict, OrderedDict], \
            "ParamGen class requires a dict or OrderedDict as the initial data."
        #self._validate_schema(data_dict)
        self._data = deepcopy(data_dict)
        self._reduced = False

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

    @classmethod
    def _eval_guards(cls, data_dict):

        def _is_guarded_dict():
            """ returns true if all the keys of a dictionary are logical expressions, i.e., guards."""
            assert type(data_dict) in [dict, OrderedDict]

            keys_logical = [is_logical_expr(key) for key in data_dict]
            if all(keys_logical):
                return True
            elif any(keys_logical):
                print("data_dict: ", data_dict)
                raise RuntimeError("Only subset of the keys of the above dict are guards, i.e., logical expressions")
            else:
                return False

        if not _is_guarded_dict():
            return
        else:
            raise NotImplementedError();
            pass #todo


    @classmethod
    def _reduce_bfirst(cls, data_dict, expand_func):
        
        # first, expand the variables in keys:
        data_dict_copy = data_dict.copy() # copy to iteate over while manipulating the original
        for key, val in data_dict_copy.items():
            if has_expandable_var(key):
                new_key = ParamGen.expand_var(key, expand_func)
                data_dict[new_key] = data_dict.pop(key)

        # now, evaluate guards if data_dict corresponds to a guarded entry
        ParamGen._eval_guards(data_dict)

        
        q = []
        for key, val in data_dict.items():
            if isinstance(val,(dict,OrderedDict)):
                q.append(key)
            else:
                print(val)

        for key in q:
            cls._reduce_bfirst(data_dict[key], expand_func)
        

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
            ParamGen._reduce_bfirst(self._data, expand_func)
        #elif search_method=="dfirst"
        #    todo
        else:
            raise RuntimeError("Unknown search method.")
            
        self._reduced = True