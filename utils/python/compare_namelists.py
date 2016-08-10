import os, re, logging

from CIME.namelist import expand_literal_list, is_valid_fortran_namelist_literal, \
    string_to_character_literal, literal_to_python_value, parse
from CIME.utils import expect
logger=logging.getLogger(__name__)

# pragma pylint: disable=unsubscriptable-object

###############################################################################
def normalize_string_value(name, value, case):
###############################################################################
    """
    Some of the string in namelists will contain data that's inherently prone
    to diffs, like file paths, etc. This function attempts to normalize that
    data so that it will not cause diffs.
    """
    value = str(value)
    # Any occurance of case must be normalized because test-ids might not match
    if (case is not None):
        case_re = re.compile(r'%s[.]([GC])[.]([^./\s]+)' % case)
        value = case_re.sub("%s.ACTION.TESTID" % case, value)

    if (name in ["runid", "model_version", "username"]):
        # Don't even attempt to diff these, we don't care
        return name.upper()
    elif (".log." in value):
        # Remove the part that's prone to diff
        components = value.split(".")
        return os.path.basename(".".join(components[0:-1]))
    elif (":" in value):
        items = value.split(":")
        items = [normalize_string_value(name, item, case) for item in items]
        return ":".join(items)
    elif ("/" in value):
        # File path, just return the basename
        return os.path.basename(value)
    else:
        return value

###############################################################################
def compare_scalar_values(name, gold_literal, comp_literal, case, do_print):
###############################################################################
    norm_gold = literal_to_python_value(gold_literal)
    norm_comp = literal_to_python_value(comp_literal)
    if isinstance(norm_gold, str) or isinstance(norm_gold, unicode):
        norm_gold = normalize_string_value(name, norm_gold, case)
        norm_comp = normalize_string_value(name, norm_comp, case)
    equal = norm_gold == norm_comp
    if do_print and not equal:
        print "  BASE: %s = %r" % (name, norm_gold)
        print "  COMP: %s = %r" % (name, norm_comp)
    return equal

###############################################################################
def is_dict_like(literals):
###############################################################################
    all_empty = True
    for literal in literals:
        if literal.strip() != '':
            all_empty = False
            if not is_valid_fortran_namelist_literal("character", literal) or '->' not in literal:
                return False
    return not all_empty

###############################################################################
def literal_list_to_dict(literals):
###############################################################################
    literal_dict = {}
    for literal in literals:
        scalar = literal_to_python_value(literal, type_="character")
        if scalar.strip() == '':
            continue
        key, _, value = scalar.partition('->')
        literal_dict[key.strip()] = string_to_character_literal(value.strip())
    return literal_dict

###############################################################################
def compare_values(name, gold_value, comp_value, case, do_print=False):
###############################################################################
    """
    Compare values for a specific variable in a namelist.
    """
    gold_literals = expand_literal_list(gold_value)
    comp_literals = expand_literal_list(comp_value)
    rv = True

    dict_mode = is_dict_like(gold_literals) and is_dict_like(comp_literals)
    if dict_mode:
        # Deal with '->' dictionaries-as-arrays.
        # Convert to dictionaries.
        gold_dict = literal_list_to_dict(gold_literals)
        comp_dict = literal_list_to_dict(comp_literals)
        for key, gold_literal in gold_dict.iteritems():
            if key in comp_dict:
                comp_literal = comp_dict[key]
                rv &= compare_scalar_values("%s dict item %s" % (name, key), gold_literal,
                                            comp_literal, case, do_print)
            else:
                rv = False
                if do_print:
                    print "  dict variable '%s' missing key %s with value %s" \
                        % (name, key, gold_literal)

        for key, comp_literal in comp_dict.iteritems():
            if key not in gold_dict:
                rv = False
                if do_print:
                    print "  dict variable '%s' has extra key %s with value %s" \
                        % (name, key, comp_literal)
    elif len(gold_literals) > 1 or len(comp_literals) > 1:
        # Non-dictionary list values.
        # Note, list values remain order sensitive
        for idx, gold_literal in enumerate(gold_literals):
            if idx < len(comp_literals):
                comp_literal = comp_literals[idx]
                rv &= compare_scalar_values("%s list item %d" % (name, idx), gold_literal,
                                            comp_literal, case, do_print)
            else:
                rv = False
                if do_print:
                    print "  list variable '%s' missing value %s" % (name, gold_literal)

        if len(comp_literals) > len(gold_literals):
            for comp_literal in comp_literals[len(gold_literals):]:
                rv = False
                if do_print:
                    print "  list variable '%s' has extra value %s" % (name, comp_literal)
    else:
        # Scalar values.
        rv = compare_scalar_values(name, gold_literals[0], comp_literals[0], case, do_print)
    return rv

###############################################################################
def compare_namelists(gold_namelist, comp_namelist, case):
###############################################################################
    """
    Compare two namelists. Print diff information if any. Return true if
    equivalent.

    Expect args in form: {namelist -> {key -> value} }.
      value can be an int, string, list, or dict

    >>> teststr = '''&nml
    ...   val = 'foo'
    ...   aval = 'one','two', 'three'
    ...   maval = 'one', 'two', 'three', 'four'
    ...   dval = 'one -> two', 'three -> four'
    ...   mdval = 'one -> two', 'three -> four', 'five -> six'
    ...   nval = 1850
    ... /
    ... &nml2
    ...   val2 = .false.
    ... /
    ... '''
    >>> compare_namelists(parse(text=teststr), parse(text=teststr), None)
    True

    >>> teststr1 = '''&nml1
    ...   val11 = 'foo'
    ... /
    ... &nml2
    ...   val21 = 'foo'
    ...   val22 = 'foo', 'bar', 'baz'
    ...   val23 = 'baz'
    ...   val24 = '1 -> 2', '2 -> 3', '3 -> 4'
    ... /
    ... &nml3
    ...   val31 = F
    ...   val32 = 0.2
    ...   val33 = +025
    ...   val34 = 2*'bazz'
    ... /'''
    >>> teststr2 = '''&nml01
    ...   val11 = 'foo'
    ... /
    ... &nml2
    ...   val21 = 'foo0'
    ...   val22 = 'foo', 'bar0', 'baz'
    ...   val230 = 'baz'
    ...   val24 = '1 -> 20', '2 -> 3', '30 -> 4'
    ... /
    ... &nml3
    ...   val31 = .false. , val32 = 2.e-1 , val33 = 25, val34 = "bazz", "bazz"
    ... /'''
    >>> compare_namelists(parse(text=teststr1), parse(text=teststr2), None)
    Differences in namelist group 'nml2':
      BASE: val21 = 'foo'
      COMP: val21 = 'foo0'
      BASE: val22 list item 1 = 'bar'
      COMP: val22 list item 1 = 'bar0'
      missing variable: 'val23'
      BASE: val24 dict item 1 = '2'
      COMP: val24 dict item 1 = '20'
      dict variable 'val24' missing key 3 with value "4"
      dict variable 'val24' has extra key 30 with value "4"
      found extra variable: 'val230'
    Missing namelist group: nml1
    Found extra namelist group: nml01
    False

    >>> teststr1 = '''&rad_cnst_nl
    ... icecldoptics           = 'mitchell'
    ... logfile                = 'cpl.log.150514-001533'
    ... case_name              = 'ERB.f19_g16.B1850C5.skybridge_intel.C.150513-230221'
    ... runid                  = 'FOO'
    ... model_version          = 'cam5_3_36'
    ... username               = 'jgfouca'
    ... iceopticsfile          = '/projects/ccsm/inputdata/atm/cam/physprops/iceoptics_c080917.nc'
    ... liqcldoptics           = 'gammadist'
    ... liqopticsfile          = '/projects/ccsm/inputdata/atm/cam/physprops/F_nwvl200_mu20_lam50_res64_t298_c080428.nc'
    ... mode_defs              = 'mam3_mode1:accum:=', 'A:num_a1:N:num_c1:num_mr:+',
    ...   'A:so4_a1:N:so4_c1:sulfate:/projects/ccsm/inputdata/atm/cam/physprops/sulfate_rrtmg_c080918.nc:+', 'A:pom_a1:N:pom_c1:p-organic:/projects/ccsm/inputdata/atm/cam/physprops/ocpho_rrtmg_c101112.nc:+',
    ...   'A:soa_a1:N:soa_c1:s-organic:/projects/ccsm/inputdata/atm/cam/physprops/ocphi_rrtmg_c100508.nc:+', 'A:bc_a1:N:bc_c1:black-c:/projects/ccsm/inputdata/atm/cam/physprops/bcpho_rrtmg_c100508.nc:+',
    ...   'A:dst_a1:N:dst_c1:dust:/projects/ccsm/inputdata/atm/cam/physprops/dust4_rrtmg_c090521.nc:+', 'A:ncl_a1:N:ncl_c1:seasalt:/projects/ccsm/inputdata/atm/cam/physprops/ssam_rrtmg_c100508.nc',
    ...   'mam3_mode2:aitken:=', 'A:num_a2:N:num_c2:num_mr:+',
    ...   'A:so4_a2:N:so4_c2:sulfate:/projects/ccsm/inputdata/atm/cam/physprops/sulfate_rrtmg_c080918.nc:+', 'A:soa_a2:N:soa_c2:s-organic:/projects/ccsm/inputdata/atm/cam/physprops/ocphi_rrtmg_c100508.nc:+',
    ...   'A:ncl_a2:N:ncl_c2:seasalt:/projects/ccsm/inputdata/atm/cam/physprops/ssam_rrtmg_c100508.nc', 'mam3_mode3:coarse:=',
    ...   'A:num_a3:N:num_c3:num_mr:+', 'A:dst_a3:N:dst_c3:dust:/projects/ccsm/inputdata/atm/cam/physprops/dust4_rrtmg_c090521.nc:+',
    ...   'A:ncl_a3:N:ncl_c3:seasalt:/projects/ccsm/inputdata/atm/cam/physprops/ssam_rrtmg_c100508.nc:+', 'A:so4_a3:N:so4_c3:sulfate:/projects/ccsm/inputdata/atm/cam/physprops/sulfate_rrtmg_c080918.nc'
    ... rad_climate            = 'A:Q:H2O', 'N:O2:O2', 'N:CO2:CO2',
    ...   'N:ozone:O3', 'N:N2O:N2O', 'N:CH4:CH4',
    ...   'N:CFC11:CFC11', 'N:CFC12:CFC12', 'M:mam3_mode1:/projects/ccsm/inputdata/atm/cam/physprops/mam3_mode1_rrtmg_c110318.nc',
    ...   'M:mam3_mode2:/projects/ccsm/inputdata/atm/cam/physprops/mam3_mode2_rrtmg_c110318.nc', 'M:mam3_mode3:/projects/ccsm/inputdata/atm/cam/physprops/mam3_mode3_rrtmg_c110318.nc'
    ... /'''
    >>> teststr2 = '''&rad_cnst_nl
    ... icecldoptics           = 'mitchell'
    ... logfile                = 'cpl.log.150514-2398745'
    ... case_name              = 'ERB.f19_g16.B1850C5.skybridge_intel.C.150513-1274213'
    ... runid                  = 'BAR'
    ... model_version          = 'cam5_3_36'
    ... username               = 'hudson'
    ... iceopticsfile          = '/something/else/inputdata/atm/cam/physprops/iceoptics_c080917.nc'
    ... liqcldoptics           = 'gammadist'
    ... liqopticsfile          = '/something/else/inputdata/atm/cam/physprops/F_nwvl200_mu20_lam50_res64_t298_c080428.nc'
    ... mode_defs              = 'mam3_mode1:accum:=', 'A:num_a1:N:num_c1:num_mr:+',
    ...   'A:so4_a1:N:so4_c1:sulfate:/something/else/inputdata/atm/cam/physprops/sulfate_rrtmg_c080918.nc:+', 'A:pom_a1:N:pom_c1:p-organic:/something/else/inputdata/atm/cam/physprops/ocpho_rrtmg_c101112.nc:+',
    ...   'A:soa_a1:N:soa_c1:s-organic:/something/else/inputdata/atm/cam/physprops/ocphi_rrtmg_c100508.nc:+', 'A:bc_a1:N:bc_c1:black-c:/something/else/inputdata/atm/cam/physprops/bcpho_rrtmg_c100508.nc:+',
    ...   'A:dst_a1:N:dst_c1:dust:/something/else/inputdata/atm/cam/physprops/dust4_rrtmg_c090521.nc:+', 'A:ncl_a1:N:ncl_c1:seasalt:/something/else/inputdata/atm/cam/physprops/ssam_rrtmg_c100508.nc',
    ...   'mam3_mode2:aitken:=', 'A:num_a2:N:num_c2:num_mr:+',
    ...   'A:so4_a2:N:so4_c2:sulfate:/something/else/inputdata/atm/cam/physprops/sulfate_rrtmg_c080918.nc:+', 'A:soa_a2:N:soa_c2:s-organic:/something/else/inputdata/atm/cam/physprops/ocphi_rrtmg_c100508.nc:+',
    ...   'A:ncl_a2:N:ncl_c2:seasalt:/something/else/inputdata/atm/cam/physprops/ssam_rrtmg_c100508.nc', 'mam3_mode3:coarse:=',
    ...   'A:num_a3:N:num_c3:num_mr:+', 'A:dst_a3:N:dst_c3:dust:/something/else/inputdata/atm/cam/physprops/dust4_rrtmg_c090521.nc:+',
    ...   'A:ncl_a3:N:ncl_c3:seasalt:/something/else/inputdata/atm/cam/physprops/ssam_rrtmg_c100508.nc:+', 'A:so4_a3:N:so4_c3:sulfate:/something/else/inputdata/atm/cam/physprops/sulfate_rrtmg_c080918.nc'
    ... rad_climate            = 'A:Q:H2O', 'N:O2:O2', 'N:CO2:CO2',
    ...   'N:ozone:O3', 'N:N2O:N2O', 'N:CH4:CH4',
    ...   'N:CFC11:CFC11', 'N:CFC12:CFC12', 'M:mam3_mode1:/something/else/inputdata/atm/cam/physprops/mam3_mode1_rrtmg_c110318.nc',
    ...   'M:mam3_mode2:/something/else/inputdata/atm/cam/physprops/mam3_mode2_rrtmg_c110318.nc', 'M:mam3_mode3:/something/else/inputdata/atm/cam/physprops/mam3_mode3_rrtmg_c110318.nc'
    ... /'''
    >>> compare_namelists(parse(text=teststr1), parse(text=teststr2), 'ERB.f19_g16.B1850C5.skybridge_intel')
    True
    """
    rv = True

    # We want to keep lists of differences and print results in a second pass,
    # in order to ensure that the order is not scrambled when we change Python
    # versions and/or parse implementation details.
    gold_groups = gold_namelist.get_group_names()
    comp_groups = comp_namelist.get_group_names()
    different_groups = []
    missing_groups = []
    for group_name in gold_groups:
        if (group_name not in comp_groups):
            rv = False
            missing_groups.append(group_name)
        else:
            gold_names = gold_namelist.get_variable_names(group_name)
            comp_names = comp_namelist.get_variable_names(group_name)
            namelists_equal = True
            for variable_name in gold_names:
                if (variable_name not in comp_names):
                    namelists_equal = False
                    break
                else:
                    gold_value = gold_namelist.get_variable_value(group_name,
                                                                  variable_name)
                    comp_value = comp_namelist.get_variable_value(group_name,
                                                                  variable_name)
                    if not compare_values(variable_name, gold_value, comp_value,
                                          case):
                        namelists_equal = False
                        break

            for variable_name in comp_names:
                if (variable_name not in gold_names):
                    namelists_equal = False
                    break

            if not namelists_equal:
                different_groups.append(group_name)
                rv = False

    for group_name in sorted(different_groups):
        print "Differences in namelist group '%s':" % group_name
        gold_names = gold_namelist.get_variable_names(group_name)
        comp_names = comp_namelist.get_variable_names(group_name)
        for variable_name in sorted(gold_names):
            if (variable_name not in comp_names):
                print "  missing variable: '%s'" % variable_name
            else:
                gold_value = gold_namelist.get_variable_value(group_name,
                                                              variable_name)
                comp_value = comp_namelist.get_variable_value(group_name,
                                                              variable_name)
                compare_values(variable_name, gold_value, comp_value, case,
                               do_print=True)
        for variable_name in sorted(comp_names):
            if variable_name not in gold_names:
                print "  found extra variable: '%s'" % variable_name

    for group_name in sorted(missing_groups):
        print "Missing namelist group:", group_name

    extra_groups = []
    for group_name in comp_groups:
        if (group_name not in gold_groups):
            rv = False
            extra_groups.append(group_name)

    for group_name in sorted(extra_groups):
        print "Found extra namelist group:", group_name

    return rv

###############################################################################
def compare_namelist_files(gold_file, compare_file, case=None):
###############################################################################
    expect(os.path.exists(gold_file), "File not found: %s" % gold_file)
    expect(os.path.exists(compare_file), "File not found: %s" % compare_file)

    gold_namelist = parse(in_file=gold_file)
    comp_namelist = parse(in_file=compare_file)

    return compare_namelists(gold_namelist, comp_namelist, case)

###############################################################################
def is_namelist_file(file_path):
###############################################################################
    try:
        parse(in_file=file_path)
    except SystemExit as e:
        assert "Unexpected end of file encountered in namelist." in str(e) or \
            "Error in parsing namelist" in str(e), str(e)
        return False
    return True
