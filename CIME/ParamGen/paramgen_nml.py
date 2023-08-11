import re

try:
    from paramgen import ParamGen
except ModuleNotFoundError:
    from CIME.ParamGen.paramgen import ParamGen

class ParamGen_NML(ParamGen):
    """Fortran Namelist Data wrapper"""

    @classmethod
    def from_nml_file(cls, file_path):
        data_dict = cls.parse_nml_file(file_path)
        return cls(data_dict)

    @classmethod
    def parse_nml_file(cls, file_path):
        
        no_group = 'no_group'
        data_dict = {no_group:{}}
        
        with open(file_path) as f:

            within_group = False
            value_contd = False
            group_name = no_group
            var_name = None
            value = None
            
            for line in f:
                line = line.strip()

                if len(line) == 0:
                    continue # empty line
                if line[0] == '!':
                    continue # comment line
                
                # discard any trailing comment:
                line = line.split('!')[0]

                if line[0] == '&':
                    # check group start syntax
                    assert re.match('^&\w*\s*$',line) is not None, "Unsupported nml syntax:\n\t"+line
                    # check if already within a group
                    assert not within_group, "Encountered a group start while already within a group:\n\t"+line
                    within_group = True
                    
                    group_name = line[1:]
                    if group_name not in data_dict:
                        data_dict[group_name] = {}
                
                elif line[-1] == '/':
                    assert within_group, "Encountered a group end character while not within a group:\n\t"+line
                    within_group = False
                    group_name = no_group
            
                else: # key = value pair, or value continuation
                    
                    if re.match('^\w*\s*=\s*\S+', line): # key = value pair
                        var_name, value = line.split('=')
                        var_name, value = var_name.strip(), value.strip()
                        assert '=' not in value, "Unsupported nml syntax:\n\t"+line
                        data_dict[group_name][var_name] = {'values': value}
                        
                    
                    else: # value continuation
                        assert value_contd is True, "Unsupported nml syntax:\n\t"+line
                        data_dict[group_name][var_name]['values'] += '\n'+line
                        
                    value_contd = line[-1] == ','
                    
        
        # drop empty groups
        data_dict = {group:vlist for group,vlist in data_dict.items() if len(data_dict[group])>0}

        return data_dict

    # todo, move write_nml from ParamGen to this derived class.
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
                if vls is None:
                    continue # no values, likely because all guards evaluate to False.
                if not isinstance(vls, dict):
                    print("------------------------")
                    print(vls)
                    print("------------------------")
                assert isinstance(vls, dict), "Invalid data format"
                for val in vls:
                    # val is a value in the values dict
                    assert isinstance(val, str), "Invalid data format"

        # write the namelist file
        with open(output_path, "w") as nml:
            for module in self._data:
                nml.write("&{}\n".format(module))
                for var in self._data[module]:
                    if self._data[module][var] is None or self._data[module][var]["values"] is None:
                        # if the value of a particular variable is None (because all guards are false),
                        # then, skip writing the variable.
                        continue
                    val = str(self._data[module][var]["values"]).strip()
                    if val is not None:
                        nml.write("    {} = {}\n".format(var, val))
                nml.write("/\n\n")