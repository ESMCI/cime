"""Auxiliary functions to be used in ParamGen and derived classes"""

import re


def is_number(var):
    """
    Returns True if the passed var (of type string) is a number. Returns
    False if var is not a string or if it is not a number.
    This function is an alternative to isnumeric(), which can't handle
    scientific notation.

    Parameters
    ----------
    var: str
        variable to check whether number or not
    Returns
    -------
    True or False

    Example
    -------
    >>> "1e-6".isnumeric()
    False
    >>> is_number("1e-6") and is_number(1) and is_number(3.14)
    True
    >>> is_number([1,2]) or is_number("hello")
    False
    """
    try:
        float(var)
    except ValueError:
        return False
    except TypeError:
        return False
    return True


def is_logical_expr(expr):
    """
    Returns True if a string is a logical expression.

    Please note that fortran array syntax allows for
    the use of parantheses and colons in namelist
    variable names, which "eval" counts as a syntax error.

    Parameters
    ----------
    expr: str
        expression to check whether logical or not
    Returns
    -------
    True or False

    Example
    -------
    >>> is_logical_expr("0 > 1000")
    True
    >>> is_logical_expr("3+4")
    False
    """

    assert isinstance(
        expr, str
    ), "Expression passed to is_logical_expr function must be a string."

    # special case:
    if expr.strip() == "else":
        return True

    try:
        return isinstance(eval(expr), bool)
    except (NameError, SyntaxError):
        return False


def is_formula(expr):
    """
    Returns True if expr is a ParamGen formula to evaluate. This is determined by
    checking whether expr is a string with a length of 1 or greater and if the
    first character of expr is '='.

    Parameters
    ----------
    expr: str
        expression to check whether formula or not
    Returns
    -------
    True or False

    Example
    -------
    >>> is_formula("3*5")
    False
    >>> is_formula("= 3*5")
    True
    """

    return isinstance(expr, str) and len(expr) > 0 and expr.strip()[0] == "="


def has_unexpanded_var(expr):
    """
    Checks if a given expression has an expandable variable, e.g., $OCN_GRID,
    that's not expanded yet.

    Parameters
    ----------
    expr: str
        expression to check
    Returns
    -------
    True or False

    Example
    -------
    >>> has_unexpanded_var("${OCN_GRID} == tx0.66v1")
    True
    """

    return isinstance(expr, str) and bool(re.search(r"(\$\w+|\${\w+\})", expr))


def get_expandable_vars(expr):
    """
    Returns the set of expandable vars from an expression.

    Parameters
    ----------
    expr: str
        expression to look for
    Returns
    -------
        a set of strings containing the expandable var names.

    Example
    -------
    >>> get_expandable_vars("var1 $var2")
    {'var2'}
    >>> get_expandable_vars("var3 ${var4}")
    {'var4'}
    """
    expandable_vars = re.findall(r"(\$\w+|\${\w+\})", expr)
    expandable_vars_stripped = set()
    for var in expandable_vars:
        var_stripped = var.strip().replace("$", "").replace("{", "").replace("}", "")
        expandable_vars_stripped.add(var_stripped)
    return expandable_vars_stripped


def _check_comparison_types(formula):
    """
    A check to detect the comparison of different data types. This function
    replaces equality comparisons with order comparisons to check whether
    any variables of different types are compared. From Python 3.6 documentation:
    A default order comparison (<, >, <=, and >=) is not provided; an attempt
    raises TypeError. A motivation for this default behavior is the lack of a
    similar invariant as for equality.

    Parameters
    ----------
    formula: str
        formula to check if it includes comparisons of different data types
    Returns
    -------
    True (or raises TypeError)

    Example
    -------
    >>> _check_comparison_types("3.1 > 3")
    True
    >>> _check_comparison_types("'3.1' == 3.1")
    Traceback (most recent call last):
    ...
    TypeError: The following formula may be comparing different types of variables: '3.1' == 3.1
    """
    guard_test = formula.replace("==", ">").replace("!=", ">").replace("<>", ">")
    try:
        eval(guard_test)
    except TypeError as type_error:
        raise TypeError(
            "The following formula may be comparing different types of variables: {}".format(
                formula
            )
        ) from type_error
    return True


def eval_formula(formula):
    """
    This function evaluates a given formula and returns the result. It also
    carries out several sanity checks before evaluation.

    Parameters
    ----------
    formula: str
        formula to evaluate
    Returns
    -------
    eval(formula)

    Example
    -------
    >>> eval_formula("3*5")
    15
    >>> eval_formula("'tx0.66v1' != 'gx1v6'")
    True
    >>> eval_formula('$OCN_GRID != "gx1v6"')
    Traceback (most recent call last):
    ...
    AssertionError
    """

    # make sure no expandable var exists in the formula. (They must already
    # be expanded before this function is called.)
    assert not has_unexpanded_var(formula)

    # Check whether any different data types are being compared
    _check_comparison_types(formula)

    # now try to evaluate the formula:
    try:
        result = eval(formula)
    except (TypeError, NameError, SyntaxError) as error:
        raise RuntimeError("Cannot evaluate formula: " + formula) from error

    return result


if __name__ == "__main__":
    import doctest

    doctest.testmod()
