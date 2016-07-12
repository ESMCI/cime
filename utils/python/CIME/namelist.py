"""Module containing tools for dealing with Fortran namelists.

Most Fortran syntax rules implemented here are compatible with Fortran 2008
(which is usually the same as previous standards as well, and anticipated to be
similar to Fortran 2015). The only exceptions should be cases where (a) we
deliberately prohibit "troublesome" behavior that would be allowed by the
standard, or (b) we rely on conventions shared by all major compilers. These
should be documented in the particular functions where the exception is most
relevant.
"""

import re

from CIME.XML.standard_module_setup import *
from CIME.utils import expect

logger = logging.getLogger(__name__)

# Fortran syntax regular expressions.
# Variable names.
FORTRAN_NAME_REGEX = re.compile(r"^[a-z][a-z0-9_]{0,62}$", re.IGNORECASE)
FORTRAN_LITERAL_REGEXES = {}
# Integer literals.
_int_re_string = r"(\+|-)?[0-9]+"
FORTRAN_LITERAL_REGEXES['integer'] = re.compile("^ *" + _int_re_string + " *$")
# Real/complex literals.
_ieee_exceptional_re_string = r"inf(inity)?|nan(\([^)]+\))?"
_float_re_string = r"((\+|-)?([0-9]+(\.[0-9]*)?|\.[0-9]+)([ed]?%s)?|%s)" % \
                   (_int_re_string, _ieee_exceptional_re_string)
FORTRAN_LITERAL_REGEXES['real'] = re.compile("^ *" + _float_re_string + " *$",
                                             re.IGNORECASE)
FORTRAN_LITERAL_REGEXES['complex'] = re.compile(r"^ *\([ \n]*" +
                                                _float_re_string +
                                                r"[ \n]*,[ \n]*" +
                                                _float_re_string +
                                                r"[ \n]*\) *$", re.IGNORECASE)
# Character literals.
_char_single_re_string = r"'[^']*(''[^']*)*'"
_char_double_re_string = r'"[^"]*(""[^"]*)*"'
FORTRAN_LITERAL_REGEXES['character'] = re.compile("^ *(" +
                                                  _char_single_re_string + "|" +
                                                  _char_double_re_string +
                                                  ") *$")
# Logical literals.
FORTRAN_LITERAL_REGEXES['logical'] = re.compile(r"^ *\.?[tf][^=/ \n]* *$",
                                                re.IGNORECASE)

def is_valid_fortran_name(string):
    """Check that a variable name is allowed in Fortran.

    The rules are:
    1. The name must start with a letter.
    2. All characters in a name must be alphanumeric (or underscores).
    3. The maximum name length is 63 characters.

    >>> is_valid_fortran_name("")
    False
    >>> is_valid_fortran_name("a")
    True
    >>> is_valid_fortran_name("A")
    True
    >>> is_valid_fortran_name("2")
    False
    >>> is_valid_fortran_name("_")
    False
    >>> is_valid_fortran_name("abc#123")
    False
    >>> is_valid_fortran_name("aLiBi_123")
    True
    >>> is_valid_fortran_name("A" * 64)
    False
    >>> is_valid_fortran_name("A" * 63)
    True
    """
    return FORTRAN_NAME_REGEX.search(string) is not None

def is_valid_fortran_namelist_literal(type_, string):
    r"""Determine whether a literal is valid in a Fortran namelist.

    Note that kind parameters are *not* allowed in namelists, which simplifies
    this check a bit. We always assume that a period (".") is the decimal
    separator, not a comma (","). Internal whitespace is allowed for complex and
    character literals only. BOZ literals and compiler extensions (e.g.
    backslash escapes) are not allowed.

    Detailed rules and examples follow.

    Integers: Must be a sequence of one or more digits, with an optional sign.

    >>> is_valid_fortran_namelist_literal("integer", "")
    False
    >>> is_valid_fortran_namelist_literal("integer", "1")
    True
    >>> is_valid_fortran_namelist_literal("integer", "a")
    False
    >>> is_valid_fortran_namelist_literal("integer", " 1")
    True
    >>> is_valid_fortran_namelist_literal("integer", "1 ")
    True
    >>> is_valid_fortran_namelist_literal("integer", "1 2")
    False
    >>> is_valid_fortran_namelist_literal("integer", "0123456789")
    True
    >>> is_valid_fortran_namelist_literal("integer", "+22")
    True
    >>> is_valid_fortran_namelist_literal("integer", "-26")
    True
    >>> is_valid_fortran_namelist_literal("integer", "2A")
    False
    >>> is_valid_fortran_namelist_literal("integer", "1_8")
    False
    >>> is_valid_fortran_namelist_literal("integer", "2.1")
    False
    >>> is_valid_fortran_namelist_literal("integer", "2e6")
    False

    Reals:
    - For fixed-point format, there is an optional sign, followed by an integer
    part, or a decimal point followed by a fractional part, or both.
    - Scientific notation is allowed, with an optional, case-insensitive "e" or
    "d" followed by an optionally-signed integer exponent. (Either the "e"/"d"
    or a sign must be present to separate the number from the exponent.)
    - The (case-insensitive) strings "inf", "infinity", and "nan" are allowed.
    NaN values can also contain additional information in parentheses, e.g.
    "NaN(x1234ABCD)".

    >>> is_valid_fortran_namelist_literal("real", "")
    False
    >>> is_valid_fortran_namelist_literal("real", "a")
    False
    >>> is_valid_fortran_namelist_literal("real", "1")
    True
    >>> is_valid_fortran_namelist_literal("real", " 1")
    True
    >>> is_valid_fortran_namelist_literal("real", "1 ")
    True
    >>> is_valid_fortran_namelist_literal("real", "1 2")
    False
    >>> is_valid_fortran_namelist_literal("real", "+1")
    True
    >>> is_valid_fortran_namelist_literal("real", "-1")
    True
    >>> is_valid_fortran_namelist_literal("real", "1.")
    True
    >>> is_valid_fortran_namelist_literal("real", "1.5")
    True
    >>> is_valid_fortran_namelist_literal("real", ".5")
    True
    >>> is_valid_fortran_namelist_literal("real", "+.5")
    True
    >>> is_valid_fortran_namelist_literal("real", ".")
    False
    >>> is_valid_fortran_namelist_literal("real", "+")
    False
    >>> is_valid_fortran_namelist_literal("real", "1e6")
    True
    >>> is_valid_fortran_namelist_literal("real", "1e-6")
    True
    >>> is_valid_fortran_namelist_literal("real", "1e+6")
    True
    >>> is_valid_fortran_namelist_literal("real", ".5e6")
    True
    >>> is_valid_fortran_namelist_literal("real", "1e")
    False
    >>> is_valid_fortran_namelist_literal("real", "1D6")
    True
    >>> is_valid_fortran_namelist_literal("real", "1q6")
    False
    >>> is_valid_fortran_namelist_literal("real", "1+6")
    True
    >>> is_valid_fortran_namelist_literal("real", "1.6.5")
    False
    >>> is_valid_fortran_namelist_literal("real", "1._8")
    False
    >>> is_valid_fortran_namelist_literal("real", "1,5")
    False
    >>> is_valid_fortran_namelist_literal("real", "inf")
    True
    >>> is_valid_fortran_namelist_literal("real", "INFINITY")
    True
    >>> is_valid_fortran_namelist_literal("real", "NaN")
    True
    >>> is_valid_fortran_namelist_literal("real", "nan(x56)")
    True

    Complex numbers:
    - A pair of real numbers enclosed by parentheses, and separated by a comma.
    - Any number of spaces or newlines may be placed before or after each real.

    >>> is_valid_fortran_namelist_literal("complex", "")
    False
    >>> is_valid_fortran_namelist_literal("complex", "()")
    False
    >>> is_valid_fortran_namelist_literal("complex", "(,)")
    False
    >>> is_valid_fortran_namelist_literal("complex", "( ,\n)")
    False
    >>> is_valid_fortran_namelist_literal("complex", "(a,2.)")
    False
    >>> is_valid_fortran_namelist_literal("complex", "(1.,b)")
    False
    >>> is_valid_fortran_namelist_literal("complex", "(1,2)")
    True
    >>> is_valid_fortran_namelist_literal("complex", "(-1.e+06,+2.d-5)")
    True
    >>> is_valid_fortran_namelist_literal("complex", "(inf,NaN)")
    True
    >>> is_valid_fortran_namelist_literal("complex", "(  1. ,  2. )")
    True
    >>> is_valid_fortran_namelist_literal("complex", "( \n \n 1. \n,\n 2.\n)")
    True
    >>> is_valid_fortran_namelist_literal("complex", " (1.,2.)")
    True
    >>> is_valid_fortran_namelist_literal("complex", "(1.,2.) ")
    True

    Character sequences (strings):
    - Must begin and end with the same delimiter character, either a single
    quote (apostrophe), or a double quote (quotation mark).
    - Whichever character is used as a delimiter must not appear in the
    string itself, unless it appears in doubled pairs (e.g. '''' or "'" are the
    two ways of representing a string containing a single apostrophe).
    - Note that newlines cannot be represented in a namelist character literal
    since they are interpreted as an "end of record", but they are allowed as
    long as they don't come between one of the aforementioned double pairs of
    characters.

    >>> is_valid_fortran_namelist_literal("character", "")
    False
    >>> is_valid_fortran_namelist_literal("character", "''")
    True
    >>> is_valid_fortran_namelist_literal("character", " ''")
    True
    >>> is_valid_fortran_namelist_literal("character", "'\n'")
    True
    >>> is_valid_fortran_namelist_literal("character", "''\n''")
    False
    >>> is_valid_fortran_namelist_literal("character", "'''")
    False
    >>> is_valid_fortran_namelist_literal("character", "''''")
    True
    >>> is_valid_fortran_namelist_literal("character", "'''Cookie'''")
    True
    >>> is_valid_fortran_namelist_literal("character", "'''Cookie''")
    False
    >>> is_valid_fortran_namelist_literal("character", "'\"'")
    True
    >>> is_valid_fortran_namelist_literal("character", "'\"\"'")
    True
    >>> is_valid_fortran_namelist_literal("character", '""')
    True
    >>> is_valid_fortran_namelist_literal("character", '"" ')
    True
    >>> is_valid_fortran_namelist_literal("character", '"\n"')
    True
    >>> is_valid_fortran_namelist_literal("character", '""\n""')
    False
    >>> is_valid_fortran_namelist_literal("character", '""' + '"')
    False
    >>> is_valid_fortran_namelist_literal("character", '""' + '""')
    True
    >>> is_valid_fortran_namelist_literal("character", '"' + '""Cookie""' + '"')
    True
    >>> is_valid_fortran_namelist_literal("character", '""Cookie""' + '"')
    False
    >>> is_valid_fortran_namelist_literal("character", '"\'"')
    True
    >>> is_valid_fortran_namelist_literal("character", '"\'\'"')
    True

    Logicals:
    - Must contain a (case-insensitive) "t" or "f".
    - This must be either the first nonblank character, or the second following
    a period.
    - The rest of the string is ignored, but cannot contain a comma, newline,
    equals sign, slash, or space (except that trailing spaces are allowed and
    ignored).

    >>> is_valid_fortran_namelist_literal("logical", "")
    False
    >>> is_valid_fortran_namelist_literal("logical", "t")
    True
    >>> is_valid_fortran_namelist_literal("logical", "F")
    True
    >>> is_valid_fortran_namelist_literal("logical", ".T")
    True
    >>> is_valid_fortran_namelist_literal("logical", ".f")
    True
    >>> is_valid_fortran_namelist_literal("logical", " f")
    True
    >>> is_valid_fortran_namelist_literal("logical", " .t")
    True
    >>> is_valid_fortran_namelist_literal("logical", "at")
    False
    >>> is_valid_fortran_namelist_literal("logical", ".TRUE.")
    True
    >>> is_valid_fortran_namelist_literal("logical", ".false.")
    True
    >>> is_valid_fortran_namelist_literal("logical", ".TEXAS$")
    True
    >>> is_valid_fortran_namelist_literal("logical", ".f=")
    False
    >>> is_valid_fortran_namelist_literal("logical", ".f/1")
    False
    >>> is_valid_fortran_namelist_literal("logical", ".t\nted")
    False
    >>> is_valid_fortran_namelist_literal("logical", ".Fant astic")
    False
    >>> is_valid_fortran_namelist_literal("logical", ".t2 ")
    True
    """
    expect(type_ in FORTRAN_LITERAL_REGEXES,
           "Invalid Fortran type for a namelist: %s" % type_)
    return FORTRAN_LITERAL_REGEXES[type_].search(string) is not None
