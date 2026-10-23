from CIME.compare_namelists import normalized_dict_compare


CASE = "ERS_Ln9.ne4_ne4.F2000-SCREAMv1-AQP1.mappy_gnu.eamxx-output-preset-2"


def test_normalized_dict_compare_identical():
    # Context
    data = {"a": 1, "b": {"c": "x"}, "d": [1, 2, 3]}

    # Act
    output = normalized_dict_compare("top-level", data, dict(data), CASE)

    # Assert
    assert output == ""


def test_normalized_dict_compare_value_mismatch():
    # Context
    data1 = {"output_control": {"frequency": 9}}
    data2 = {"output_control": {"frequency": 8}}

    # Act
    output = normalized_dict_compare("top-level", data1, data2, CASE)

    # Assert
    assert output == "frequency had mismatched values, baseline=9, case=8\n"


def test_normalized_dict_compare_key_missing_in_case():
    # Context
    data1 = {"fields": {"physics_gll": {}, "constant_fields": {}}}
    data2 = {"fields": {"physics_gll": {}}}

    # Act
    output = normalized_dict_compare("top-level", data1, data2, CASE)

    # Assert
    assert "fields baseline has keys not in case: {'constant_fields'}\n" == output


def test_normalized_dict_compare_key_missing_in_baseline():
    # Context
    data1 = {"fields": {"physics_gll": {}}}
    data2 = {"fields": {"physics_gll": {}, "constant_fields": {}}}

    # Act
    output = normalized_dict_compare("top-level", data1, data2, CASE)

    # Assert
    assert "fields case has keys not in baseline: {'constant_fields'}\n" == output


def test_normalized_dict_compare_mismatched_types():
    # Context
    data1 = {"a": 1}
    data2 = {"a": "1"}

    # Act
    output = normalized_dict_compare("top-level", data1, data2, CASE)

    # Assert
    assert output == (
        "For a, data does not have the same type. "
        "Baseline=<class 'int'>, case=<class 'str'>\n"
    )


def test_normalized_dict_compare_list_items():
    # Context
    data1 = {"field_names": ["T_mid", "p_int"]}
    data2 = {"field_names": ["T_mid", "p_mid"]}

    # Act
    output = normalized_dict_compare("top-level", data1, data2, CASE)

    # Assert
    assert "field_names baseline has list items not in case: {'p_int'}\n" in output
    assert "field_names case has list items not in baseline: {'p_mid'}\n" in output


def test_normalized_dict_compare_list_order_insensitive():
    # Context
    data1 = {"field_names": ["T_mid", "p_int", "tracers"]}
    data2 = {"field_names": ["p_int", "tracers", "T_mid"]}

    # Act
    output = normalized_dict_compare("top-level", data1, data2, CASE)

    # Assert
    assert output == ""


def test_normalized_dict_compare_string_mismatch():
    # Context
    data1 = {"averaging_type": "average"}
    data2 = {"averaging_type": "instant"}

    # Act
    output = normalized_dict_compare("top-level", data1, data2, CASE)

    # Assert
    assert (
        output
        == "averaging_type had mismatched values, baseline='average', case='instant'\n"
    )
