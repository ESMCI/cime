import os
import sys
import re
from copy import deepcopy
import logging
import subprocess
import shutil

try:
    from paramgen_utils import is_logical_expr, is_formula, has_unexpanded_var
    from paramgen_utils import eval_formula
except ModuleNotFoundError:
    from CIME.ParamGen.paramgen_utils import (
        is_logical_expr,
        is_formula,
        has_unexpanded_var,
    )
    from CIME.ParamGen.paramgen_utils import eval_formula

assert (
    sys.version_info.major == 3 and sys.version_info.minor >= 6
), "ParamGen requires Python 3.6 or later."

logger = logging.getLogger(__name__)


class ParamGen:
    """
    ParamGen is a versatile, generic, lightweight base class to be used when developing namelist
    and parameter generator tools for scientific modeling applications.

    Attributes
    ----------
    data : dict
        The data attribute to operate over. See Methods for the list of operations.
    match: str
        "first" or "last".

    Methods
    -------
    from_json(input_path)
        Reads in a given json input file and initializes a ParamGen object.
    from_yaml(input_path)
        Reads in a given yaml input file and initializes a ParamGen object.
    """

    def __init__(self, data_dict, match="last"):
        assert isinstance(
            data_dict, dict
        ), "ParamGen class requires a dict as the initial data."
        # self._validate_schema(data_dict)
        self._original_data = deepcopy(data_dict)
        self._data = deepcopy(data_dict)
        self._reduced = False
        self._match = match

    @property
    def data(self):
        """Returns the data attribute of the ParamGen instance."""
        return self._data

    @property
    def reduced(self):
        """Returns True if reduce() method is called for this instance of ParamGen."""
        return self._reduced

    @property
    def is_empty(self):
        """Returns True if the data property is empty."""
        return len(self._data) == 0

    @classmethod
    def from_json(cls, input_path, match="last"):
        """
        Reads in a given json input file and initializes a ParamGen object.

        Parameters
        ----------
        input_path: str
            Path to json input file containing the defaults.
        match: str
            "first" or "last"
        Returns
        -------
        ParamGen
            A ParamGen object with the data read from input_path.
        """

        import json

        with open(input_path) as json_file:
            _data = json.load(json_file)
        return cls(_data, match)

    @classmethod
    def from_yaml(cls, input_path, match="last"):
        """
        Reads in a given yaml input file and initializes a ParamGen object.

        Parameters
        ----------
        input_path: str
            Path to yaml input file containing the defaults.
        match: str
            "first" or "last"
        Returns
        -------
        ParamGen
            A ParamGen object with the data read from input_path.
        """

        import yaml

        with open(input_path) as yaml_file:
            _data = yaml.safe_load(yaml_file)
        return cls(_data, match)

    @classmethod
    def from_xml_nml(cls, input_path, match="last", no_duplicates=False):
        """
        Reads in a given xml input file and initializes a ParamGen object. The XML file must conform to the
        entry_id_pg.xsd schema that's defined within ParamGen.

        Parameters
        ----------
        input_path: str
            Path to xml input file containing the defaults.
        match: str
            "first" or "last"
        no_duplicates: bool
            If True, then any duplicate entry ids in the XML file will result in an error.

        Returns
        -------
        ParamGen
            A ParamGen object with the data read from input_path.
        """

        # First check whether the given xml file conforms to the entry_id_pg.xsd schema
        xmllint = shutil.which("xmllint")
        if xmllint is None:
            logger.warning("Couldn't find xmllint. Skipping schema check")
        else:
            schema_path = os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                "xml_schema",
                "entry_id_pg.xsd",
            )
            xmllint_cmd = "{} --xinclude --noout --schema {} {}".format(
                xmllint, schema_path, input_path
            )
            stat = subprocess.run(
                xmllint_cmd, shell=True, capture_output=True, text=True, check=True
            )
            assert (
                stat.returncode == 0
            ), "While checking file {} against nml schema, received following errmsg: {}".format(
                input_path, stat.stderr
            )

        import xml.etree.ElementTree as ET

        xml_tree = ET.parse(input_path)
        root = xml_tree.getroot()
        data = {}

        # Loop over all entries (namelist variables)
        for entry in list(root):
            # where each entry corresponds to a namelist variable, i.e., parameter
            param_name = entry.attrib["id"]
            if no_duplicates and param_name in data:
                # No duplicate namelist entries allowed, so raise error:
                emsg = "Entry id '{}' listed twice in file:\n'{}'"
                raise ValueError(emsg.format(param_name, input_path))
            else:
                data[param_name] = {}

            # loop over child entries and attributes of the parameter
            for child in list(entry):
                if child.tag == "values":
                    data[param_name]["values"] = {}
                    values = list(child)

                    # check if the values have logical guards as propositions
                    guards = {}
                    for value in values:
                        if "guard" in value.attrib:
                            assert len(value.attrib) == 1, (
                                "If an explicit guard attribute is provided for a value,"
                                + "no other attribute may be provided. Check parameter {}".format(
                                    param_name
                                )
                            )
                            guards[value] = value.attrib["guard"]
                        elif len(value.attrib) > 0:
                            guards[value] = " and ".join(
                                [
                                    '"${{{}}}" == "{}"'.format(
                                        str(guard_var), str(guard_val)
                                    )
                                    for guard_var, guard_val in value.attrib.items()
                                ]
                            )
                        else:
                            assert "else" not in guards.values(), (
                                "Multiple values with no guards (proposition)"
                                + "detected in variable {}".format(param_name)
                            )
                            guards[value] = "else"

                    if len(values) == 1 and guards[values[0]] == "else":
                        data[param_name]["values"] = list(values)[0].text.strip()
                    else:
                        for value, guard in guards.items():
                            data[param_name]["values"][guard] = value.text.strip()

                else:
                    # a child element other than the <values> element (.e.g, type, desc, group, etc.)
                    data[param_name][child.tag] = child.text.strip()

            # now group the parameters according to their group_id's:
            _data = {}  # grouped data
            for param_name in data:
                param_group = data[param_name]["group"]
                if param_group not in _data:
                    _data[param_group] = {}
                _data[param_group][param_name] = data[param_name]

        return cls(_data, match)

    @staticmethod
    def _expand_vars(expr, expand_func):
        """Replaces the expandable variables with their values in a given expression (expr) of type str.

        Parameters
        ----------
        expr: str
            expression with expandable variables, e.g., "$OCN_GRID == "tx0.66v1"
        expand_func:
            a callable objects that can return the value of any expandable variable specified in expr"
        Returns
        -------
            an expresion of type string where the expandable variables are replaced with their values.

        Example
        -------
        >>> ParamGen._expand_vars("$x + 2 == $z", (lambda var: 1 if var=='x' else 3) )
        '1 + 2 == 3'
        """

        if expand_func is None:
            return expr  # No expansion function is provided, so return.

        assert isinstance(
            expr, str
        ), "Expression passed to _expand_vars must be string."
        expandable_vars = re.findall(r"(\$\w+|\${\w+\})", expr)
        for word in expandable_vars:
            word_stripped = (
                word.strip().replace("$", "").replace("{", "").replace("}", "")
            )
            word_expanded = expand_func(word_stripped)
            assert (
                word_expanded is not None
            ), "Cannot determine the value of the variable: {}.".format(word)

            # enclose with quotes if expanded var is a string and is expression sans curly braces
            if isinstance(word_expanded, str) and word[1] != "{":
                word_expanded = '"' + word_expanded + '"'
            else:
                word_expanded = str(word_expanded)

            expr = re.sub(
                r"(\$\b" + word_stripped + r"\b|\$\{" + word_stripped + r"\})",
                word_expanded,
                expr,
            )

        return expr

    @staticmethod
    def _is_guarded_dict(data_dict):
        """Returns true if all the keys of a dictionary are logical expressions, i.e., guards.

        Parameters
        ----------
        data_dict: dict
            A dictionary where the keys may be logical expressions (of type string)

        Example
        -------
        >>> ParamGen._is_guarded_dict({True: 'x', 'False': 'y'})
        True
        >>> ParamGen._is_guarded_dict({ "'tx0.66v1' == 'tx0.66v1'": 'x', False: 'y'})
        True
        >>> ParamGen._is_guarded_dict({'i':'x', 'j':'y'})
        False
        """
        if not isinstance(data_dict, dict):
            return False

        keys_logical = [is_logical_expr(str(key)) for key in data_dict]
        if all(keys_logical):
            return True
        if any(keys_logical):
            raise RuntimeError(
                "Only subset of the following are guarded entries, i.e., logical "
                + "expressions as keys:\n\t"
                + str(data_dict)
            )
        return False

    def _impose_guards(self, data_dict):

        """Given a data_dict with guarded entries, evaluates the guards and returns the entry whose guard (key)
        evaluates to True. If multiple guards evaluate to true, the first or the last entry with the True guard is
        returned, depending on the "match" arg passed to ParamGen initializer. This method is intended to be called
        from _reduce_recursive only.

        Parameters
        ----------
        data_dict: dict
            A dictionary whose keys are all logical expressions, i.e., guards.

        Example
        -------
        >>> obj = ParamGen({1>2: 'a', 3>2: 'b'})
        >>> new_data = obj._impose_guards(obj.data)
        >>> new_data
        'b'
        """

        def _eval_guard(guard):
            """returns true if a guard evaluates to true."""
            assert isinstance(
                guard, str
            ), "Expression passed to _eval_guard must be string."

            if has_unexpanded_var(guard):
                raise RuntimeError(
                    "The guard "
                    + guard
                    + " has an expandable variable ($var) "
                    + "that's not expanded yet. All variables must already be expanded before "
                    + "guards can be evaluated."
                )

            guard_evaluated = eval_formula(guard)
            assert isinstance(guard_evaluated, bool), "Guard is not boolean: {}".format(
                guard
            )
            return guard_evaluated

        if not ParamGen._is_guarded_dict(data_dict):
            return data_dict

        guards_eval_true = []  # list of guards that evaluate to true.
        for guard in data_dict:
            if guard == "else" or _eval_guard(str(guard)) is True:
                guards_eval_true.append(guard)

        if len(guards_eval_true) > 1 and "else" in guards_eval_true:
            guards_eval_true.remove("else")
        elif len(guards_eval_true) == 0:
            return None

        if self._match == "first":
            return data_dict[guards_eval_true[0]]
        if self._match == "last":
            return data_dict[guards_eval_true[-1]]
        raise RuntimeError("Unknown match option.")

    def _reduce_recursive(self, data_dict, expand_func=None):

        """A recursive method to reduce a given data_dict. This method is intended to be called by the reduce method
        only. Check the docstring of the reduce method for more information."""

        # (1) Expand variables in keys, .e.g, "$OCN_GRID" to "gx1v7":
        def _expand_vars_in_keys(data_dict):
            if expand_func is not None:
                new_data_dict = {}
                for key in data_dict:
                    new_key = key
                    if has_unexpanded_var(key):
                        new_key = ParamGen._expand_vars(key, expand_func)
                    new_data_dict[new_key] = data_dict[key]
                return new_data_dict
            return data_dict

        data_dict = _expand_vars_in_keys(data_dict)

        # (2) Evaluate the keys if they are all logical expressions, i.e., guards.
        # Pick the value of the first or last key evaluating to True and drop everything else.
        while ParamGen._is_guarded_dict(data_dict):
            data_dict = self._impose_guards(data_dict)
            if isinstance(data_dict, dict):
                data_dict = _expand_vars_in_keys(data_dict)

        # If the data_dict is reduced to a string, expand vars and eval formulas as a last step.
        if isinstance(data_dict, str):

            # (3) Expand variables in values, .e.g, "$OCN_GRID" to "gx1v7":
            data_dict = ParamGen._expand_vars(data_dict, expand_func)

            # (4) Evaluate the formulas as values, e.g., "= 3+4", "= [i for i in range(5)]", etc.
            if is_formula(data_dict):
                data_dict = eval_formula(data_dict.strip()[1:])

        # Continue reducing the data if it is still a dictionary (nested or not).
        elif isinstance(data_dict, dict):

            # (3) Expand variables in values, .e.g, "$OCN_GRID" to "gx1v7":
            for key, val in data_dict.copy().items():
                if isinstance(val, str):
                    data_dict[key] = ParamGen._expand_vars(val, expand_func)

            # (4) Evaluate the formulas as values, e.g., "= 3+4", "= [i for i in range(5)]", etc.
            for key, val in data_dict.copy().items():
                if is_formula(val):
                    data_dict[key] = eval_formula(val.strip()[1:])

            # (5) Recursively call _reduce_recursive for the remaining nested dicts before returning
            keys_of_nested_dicts = []  # i.e., keys of values that are of type dict
            for key, val in data_dict.items():
                if isinstance(val, dict):
                    keys_of_nested_dicts.append(key)
            for key in keys_of_nested_dicts:
                data_dict[key] = self._reduce_recursive(data_dict[key], expand_func)

        return data_dict

    def reduce(self, expand_func=None):
        """
        Reduces the data of a ParamGen instances by recursively expanding its variables,
        imposing conditional guards, and evaluating the formulas in values to determine
        the final values of parameters.

        Parameters
        ----------
        expand_func: (optional)
            a callable objects that can return the value of any expandable variable specified."

        Example
        -------
        >>> obj = ParamGen({1>2: 'a', 3>2: 'b'})
        >>> obj.reduce()
        >>> obj.data
        'b'
        """

        assert (
            callable(expand_func) or expand_func is None
        ), "expand_func argument must be a function"
        assert not self.reduced, "ParamGen data already reduced."
        assert not self.is_empty, "Empty ParamGen data."

        self._data = self._reduce_recursive(self._data, expand_func)
        self._reduced = True

    def append(self, pg_obj):
        """Adds the data of a given ParamGen instance to the self data. If a data entry already exists in self,
            the value is overriden. Otherwise, the new data entry is simply added to self.

        Parameters
        ----------
        pg_obj: ParamGen object
            A ParamGen instance whose data is to be appended to the self data

        Example
        -------
        >>> obj1 = ParamGen({'a':1, 'b':2})
        >>> obj2 = ParamGen({'b':3, 'c':4})
        >>> obj1.append(obj2)
        >>> obj1.data
        {'a': 1, 'b': 3, 'c': 4}
        """

        assert isinstance(pg_obj, ParamGen), "can only append ParamGen to Paramgen"
        assert (
            self.reduced == pg_obj.reduced
        ), "Cannot append reduced ParamGen instance to unreduced, and vice versa."

        def _append_recursive(old_dict, new_dict):
            for key, val in new_dict.items():
                if key in old_dict:
                    old_val = old_dict[key]
                    if isinstance(val, dict) and isinstance(old_val, dict):
                        _append_recursive(old_dict[key], new_dict[key])
                    else:
                        old_dict[key] = new_dict[key]
                else:
                    old_dict[key] = new_dict[key]

        _append_recursive(self._data, pg_obj._data)

    def reset(self):
        """Resets the ParamGen object to its initial state, i.e., undoes the reduce method.

        Example
        -------
        >>> obj = ParamGen({True:1, False:0})
        >>> obj.reduce()
        >>> obj.data
        1
        >>> obj.reset()
        >>> obj.data
        {True: 1, False: 0}
        """
        self._data = deepcopy(self._original_data)
        self._reduced = False

    def write_nml(self, output_path):
        """Writes the reduced data in Fortran namelist format if the data conforms to the format.

        Parameters
        ----------
        output_path: str object
            Path to the namelist file to be created.
        """

        assert (
            self._reduced
        ), "The data may be written only after the reduce method is called."

        # check *schema* after reduction
        for grp, var in self.data.items():
            # grp is the namelist module name, while var is a dictionary corresponding to the vars in namelist
            assert isinstance(grp, str), "Invalid data format"
            assert isinstance(var, dict), "Invalid data format"
            for vls in var.values():
                # vnm is the var name, and vls is its values element
                assert isinstance(vls, dict), "Invalid data format"
                for val in vls:
                    # val is a value in the values dict
                    assert isinstance(val, str), "Invalid data format"

        # write the namelist file
        with open(output_path, "w") as nml:
            for module in self._data:
                nml.write("&{}\n".format(module))
                for var in self._data[module]:
                    val = str(self._data[module][var]["values"]).strip()
                    if val is not None:
                        nml.write("    {} = {}\n".format(var, val))
                nml.write("/\n\n")
