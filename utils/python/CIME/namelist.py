"""Module containing tools for dealing with Fortran namelists.

The public interface consists of the following functions:
- `is_valid_fortran_name`
- `is_valid_fortran_namelist_literal`
- `parse`
- `write`

For the moment, only a subset of namelist syntax is supported; specifically, we
assume that only variables of intrinsic type are used, and indexing/co-indexing
of arrays to set a portion of a variable is not supported. (However, null values
and repeated values may be used to set or fill a variable as indexing would.)

We also always assume that a period (".") is the decimal separator, not a comma
(","). We also assume that the file encoding is UTF-8 or some compatible format
(e.g. ASCII).

Otherwise, most Fortran syntax rules implemented here are compatible with
Fortran 2008 (which is largely the same as previous standards, and will be
similar to Fortran 2015). The only exceptions should be cases where (a) we
deliberately prohibit "troublesome" behavior that would be allowed by the
standard, or (b) we rely on conventions shared by all major compilers.

One important convention is that newline characters can be used to denote the
end of a record. This makes them equivalent to spaces at most locations in a
Fortran namelist, except that newlines also end comments, and they are ignored
entirely within strings.

While the treatment of comments in this module is standard, it may be somewhat
surprising. Namelist comments are only allowed in two situations:

(1) As the only thing on a line (aside from optional indentation with spaces).
(2) Immediately after a "value separator" (the space, newline, comma, or slash
after a value).

This implies that all lines except for the last are syntax errors, in this
example:

```
&group_name! This is not a valid comment because it's after the group name.
foo ! Neither is this, because it's between a name and an equals sign.
= 2 ! Nor this, because it comes between the value and the following comma.
, bar = ! Nor this, because it's between an equals sign and a value.
2! Nor this, because it should be separated from the value by a comma or space.
bazz = 3 ! Nor this, because it comes between the value and the following slash.
/! This is fine, but technically it is outside the namelist, not a comment.
```

However, the above would actually be valid if all the "comments" were removed.
The Fortran standard is not clear about whether whitespace is allowed after
inline comments and before subsequent non-whitespace text (!), but this module
allows such whitespace, to preserve the sanity of both implementors and users.

The Fortran standard only applies to the interior of namelist groups, and not to
text between one namelist group and the next. This module assumes that namelist
groups are separated by (optional) whitespace and comments, and nothing else.
"""

# Disable these because of doctest, and because we don't typically follow the
# (rather specific) pylint naming conventions.
# pylint: disable=line-too-long,too-many-lines,invalid-name

import re

# Disable these because this is our standard setup
# pylint: disable=wildcard-import,unused-wildcard-import

from CIME.XML.standard_module_setup import *
from CIME.utils import expect

logger = logging.getLogger(__name__)

# Fortran syntax regular expressions.
# Variable names.
FORTRAN_NAME_REGEX = re.compile(r"^[a-z][a-z0-9_]{0,62}$", re.IGNORECASE)
FORTRAN_LITERAL_REGEXES = {}
# Integer literals.
_int_re_string = r"(\+|-)?[0-9]+"
FORTRAN_LITERAL_REGEXES['integer'] = re.compile("^" + _int_re_string + "$")
# Real/complex literals.
_ieee_exceptional_re_string = r"inf(inity)?|nan(\([^)]+\))?"
_float_re_string = r"((\+|-)?([0-9]+(\.[0-9]*)?|\.[0-9]+)([ed]?%s)?|%s)" % \
                   (_int_re_string, _ieee_exceptional_re_string)
FORTRAN_LITERAL_REGEXES['real'] = re.compile("^" + _float_re_string + "$",
                                             re.IGNORECASE)
FORTRAN_LITERAL_REGEXES['complex'] = re.compile(r"^\([ \n]*" +
                                                _float_re_string +
                                                r"[ \n]*,[ \n]*" +
                                                _float_re_string +
                                                r"[ \n]*\)$", re.IGNORECASE)
# Character literals.
_char_single_re_string = r"'[^']*(''[^']*)*'"
_char_double_re_string = r'"[^"]*(""[^"]*)*"'
FORTRAN_LITERAL_REGEXES['character'] = re.compile("^(" +
                                                  _char_single_re_string + "|" +
                                                  _char_double_re_string +
                                                  ")$")
# Logical literals.
FORTRAN_LITERAL_REGEXES['logical'] = re.compile(r"^\.?[tf][^=/ \n]*$",
                                                re.IGNORECASE)
# Repeated value prefix.
FORTRAN_REPEAT_PREFIX_REGEX = re.compile(r"^[0-9]*[1-9]+[0-9]*\*")


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
    this check a bit. Internal whitespace is allowed for complex and character
    literals only. BOZ literals and compiler extensions (e.g. backslash escapes)
    are not allowed.

    Null values, however, are allowed for all types. This means that passing in
    a string containing nothing but spaces and newlines will always cause
    `True` to be returned. Repetition (e.g. `5*'a'`) is also allowed, including
    repetition of null values.

    Detailed rules and examples follow.

    Integers: Must be a sequence of one or more digits, with an optional sign.

    >>> is_valid_fortran_namelist_literal("integer", "")
    True
    >>> is_valid_fortran_namelist_literal("integer", " ")
    True
    >>> is_valid_fortran_namelist_literal("integer", "\n")
    True
    >>> is_valid_fortran_namelist_literal("integer", "5*")
    True
    >>> is_valid_fortran_namelist_literal("integer", "1")
    True
    >>> is_valid_fortran_namelist_literal("integer", "5*1")
    True
    >>> is_valid_fortran_namelist_literal("integer", " 5*1")
    True
    >>> is_valid_fortran_namelist_literal("integer", "5* 1")
    False
    >>> is_valid_fortran_namelist_literal("integer", "5 *1")
    False
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
    True
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
    >>> is_valid_fortran_namelist_literal("real", "nan())")
    False

    Complex numbers:
    - A pair of real numbers enclosed by parentheses, and separated by a comma.
    - Any number of spaces or newlines may be placed before or after each real.

    >>> is_valid_fortran_namelist_literal("complex", "")
    True
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
    True
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
    True
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
    # Strip leading/trailing whitespace.
    string = string.strip(" \n")
    # Strip off repeated value prefix.
    if FORTRAN_REPEAT_PREFIX_REGEX.search(string) is not None:
        string = string[string.find('*') + 1:]
    # Null values are always allowed.
    if string == '':
        return True
    return FORTRAN_LITERAL_REGEXES[type_].search(string) is not None


def parse(namelist, convert_tab_to_space=True):
    """Parse a Fortran namelist.

    The `namelist` argument must be either a `str` or `unicode` object
    containing a file name, or a text I/O object with a `read` method that
    returns the text of the namelist.

    The `convert_tab_to_space` option can be used to force all tabs in the file
    to be converted to spaces, and is on by default. Note that this will usually
    allow files that use tabs as whitespace to be parsed. However, the
    implementation of this option is crude; it converts *all* tabs in the file,
    including those in character literals. (Note that there are many characters
    that cannot be passed in via namelist in any standard way, including '\n',
    so it is already a bad idea to assume that the namelist will preserve
    whitespace in strings, aside from simple spaces.)

    The return value is a dictionary associating group names to settings, where
    the setting for each namelist group is itself a dictionary associating
    variable names to lists of values.

    All names and values returned are ultimately unicode strings. E.g. a value
    of "6*2" is returned as that string; it is not converted to 6 copies of the
    Python integer `2`. Null values are returned as the empty string ("").
    """
    if isinstance(namelist, str) or isinstance(namelist, unicode):
        with open(namelist) as namelist_obj:
            text = namelist_obj.read()
    else:
        text = namelist.read()
    if convert_tab_to_space:
        text = text.replace('\t', ' ')
    try:
        namelist_dict = _NamelistParser(text, groupless).parse_namelist()
    except (_NamelistEOF, _NamelistParseError) as error:
        # Deal with unexpected EOF or other parsing errors.
        expect(False, str(error))
    return namelist_dict


def write(settings, out_file):
    """Write a Fortran namelist to a file.

    The `settings` method must be a dictionary associating group names to
    dictionaries of variable name-value pairs, i.e. the same type of data
    structure returned by `parse`.

    As with `parse`, the `out_file` argument can be either a file name, or a
    file object with a `write` method that accepts unicode.
    """
    if isinstance(out_file, str) or isinstance(out_file, unicode):
        with open(out_file, 'w') as file_obj:
            _write(settings, file_obj)
    else:
         _write(settings, out_file)


def _write(settings, out_file):
    """Unwrapped version of `write` that assumes that a file object is input."""
    for group_name in sorted(settings.keys()):
        out_file.write("&%s\n" % group_name)
        group = settings[group_name]
        for name in sorted(group.keys()):
            values = group[name]
            # To prettify things for long lists of values, build strings line-
            # by-line.
            lines = ["  %s = %s" % (name, values[0])]
            for value in values[1:]:
                if len(lines[-1]) + len(value) <= 77:
                    lines[-1] += ", " + value
                else:
                    lines[-1] += ",\n"
                    lines.append("      " + value)
            lines[-1] += "\n"
            for line in lines:
                out_file.write(line)
        out_file.write("/\n")


class _NamelistEOF(Exception):

    """Exception thrown for an unexpected end-of-file in a namelist.

    This is an internal helper class, and should never be raised in a context
    where it would be visible to a user. (Typically it should be caught and
    converted to some other error, or ignored.)
    """

    def __init__(self, message=None):
        """Create a `_NamelistEOF`, optionally using an error message."""
        super(_NamelistEOF, self).__init__()
        self._message = message

    def __str__(self):
        """Get an error message suitable for display."""
        string = "Unexpected end of file encountered in namelist."
        if self._message is not None:
            string += " (%s)" % self._message
        return string


class _NamelistParseError(Exception):

    """Exception thrown when namelist input has a syntax error.

    This is an internal helper class, and should never be raised in a context
    where it would be visible to a user. (Typically it should be caught and
    converted to some other error, or ignored.)
    """

    def __init__(self, message=None):
        """Create a `_NamelistParseError`, optionally using an error message."""
        super(_NamelistParseError, self).__init__()
        self._message = message

    def __str__(self):
        """Get an error message suitable for display."""
        string = "Error in parsing namelist"
        if self._message is not None:
            string += ": %s" % self._message
        return string


class _NamelistParser(object):

    """Class to validate and read from Fortran namelist input.

    This is intended to be an internal helper class and should not be used
    directly. Use the `parse` function in this module instead.
    """

    def __init__(self, text):
        """Create a `_NamelistParser` given text to parse in a string."""
        # Current location within the file.
        self._pos = 0
        self._line = 1
        self._col = 0
        # Text and its size.
        self._text = unicode(text)
        self._len = len(self._text)
        # Dictionary with group names as keys, and dictionaries of variable
        # name-value pairs as values.
        self._settings = dict()

    def _line_col_string(self):
        r"""Return a string specifying the current line and column number.

        >>> x = _NamelistParser('abc\nd\nef')
        >>> x._advance(5)
        >>> x._line_col_string()
        'line 2, column 1'
        """
        return "line %s, column %s" % (self._line, self._col)

    def _curr(self):
        """Return the character at the current position."""
        return self._text[self._pos]

    def _next(self):
        """Return the character at the next position.

        >>> _NamelistParser(' ')._next()
        Traceback (most recent call last):
            ...
        _NamelistEOF: Unexpected end of file encountered in namelist. (At line 1, column 1)
        """
        # If at the end of the file, we should raise _NamelistEOF. The easiest
        # way to do this is to just advance.
        if self._pos == self._len - 1:
            self._advance()
        return self._text[self._pos+1]

    def _advance(self, nchars=1):
        r"""Advance the parser's current position by `nchars` characters.

        >>> _NamelistParser('abcd')._advance(-1)
        Traceback (most recent call last):
            ...
        AssertionError: _NamelistParser attempted to 'advance' backwards
        >>> x = _NamelistParser('abc\nd\nef')
        >>> (x._pos, x._line, x._col)
        (0, 1, 0)
        >>> x._advance(0)
        >>> (x._pos, x._line, x._col)
        (0, 1, 0)
        >>> x._advance(2)
        >>> (x._pos, x._line, x._col)
        (2, 1, 2)
        >>> x._advance(1)
        >>> (x._pos, x._line, x._col)
        (3, 1, 3)
        >>> x._advance(1)
        >>> (x._pos, x._line, x._col)
        (4, 2, 0)
        >>> x._advance(3)
        >>> (x._pos, x._line, x._col)
        (7, 3, 1)
        >>> x._advance(1)
        Traceback (most recent call last):
            ...
        _NamelistEOF: Unexpected end of file encountered in namelist. (At line 3, column 2)
        >>> _NamelistParser('abc\n')._advance(4)
        Traceback (most recent call last):
            ...
        _NamelistEOF: Unexpected end of file encountered in namelist. (At line 2, column 0)
        """
        assert nchars >= 0, \
            "_NamelistParser attempted to 'advance' backwards"
        new_pos = min(self._pos + nchars, self._len)
        consumed_text = self._text[self._pos:new_pos]
        self._pos = new_pos
        lines = consumed_text.count('\n')
        self._line += lines
        # If we started a new line, set self._col to be relative to the start of
        # the current line.
        if lines > 0:
            self._col = -(consumed_text.rfind('\n') + 1)
        self._col += len(consumed_text)
        if new_pos == self._len:
            raise _NamelistEOF(message="At "+self._line_col_string())

    def _eat_whitespace(self, allow_initial_comment=False):
        r"""Advance until the next non-whitespace character.

        Returns a boolean representing whether anything was eaten. Note that
        this function also skips past new lines containing comments. Comments in
        the current line will be skipped if `allow_initial_comment=True` is
        passed in.

        >>> x = _NamelistParser(' \n a ')
        >>> x._eat_whitespace()
        True
        >>> x._curr()
        u'a'
        >>> x._eat_whitespace()
        False
        >>> x._advance()
        >>> x._eat_whitespace()
        Traceback (most recent call last):
            ...
        _NamelistEOF: Unexpected end of file encountered in namelist. (At line 2, column 3)
        >>> x = _NamelistParser(' \n! blah\n ! blah\n a')
        >>> x._eat_whitespace()
        True
        >>> x._curr()
        u'a'
        >>> x = _NamelistParser('! blah\n a')
        >>> x._eat_whitespace()
        False
        >>> x._curr()
        u'!'
        >>> x = _NamelistParser(' ! blah\n a')
        >>> x._eat_whitespace()
        True
        >>> x._curr()
        u'!'
        >>> x = _NamelistParser(' ! blah\n a')
        >>> x._eat_whitespace(allow_initial_comment=True)
        True
        >>> x._curr()
        u'a'
        """
        eaten = False
        comment_allowed = allow_initial_comment
        while True:
            while self._curr() in (' ', '\n'):
                comment_allowed |= self._curr() == '\n'
                eaten = True
                self._advance()
            # Note the reliance on short-circuit `and` here.
            if not (comment_allowed and self._eat_comment()):
                break
        return eaten

    def _eat_comment(self):
        r"""If currently positioned at a '!', advance past the comment's end.

        Only works properly if not currently inside a comment or string. Returns
        a boolean representing whether anything was eaten.

        >>> x = _NamelistParser('! foo\n ! bar\na ! bazz')
        >>> x._eat_comment()
        True
        >>> x._curr()
        u' '
        >>> x._eat_comment()
        False
        >>> x._eat_whitespace()
        True
        >>> x._eat_comment()
        True
        >>> x._curr()
        u'a'
        >>> x._advance(2)
        >>> x._eat_comment()
        Traceback (most recent call last):
            ...
        _NamelistEOF: Unexpected end of file encountered in namelist. (At line 3, column 8)
        >>> x = _NamelistParser('! foo\n')
        >>> x._eat_comment()
        Traceback (most recent call last):
            ...
        _NamelistEOF: Unexpected end of file encountered in namelist. (At line 2, column 0)
        """
        if self._curr() != '!':
            return False
        newline_pos = self._text[self._pos:].find('\n')
        if newline_pos == -1:
            # This is the last line.
            self._advance(self._len - self._pos)
        else:
            # Advance to the next line.
            self._advance(newline_pos)
            # Advance to the first character of the next line.
            self._advance()
        return True

    def _expect_char(self, chars):
        """Raise an error if the wrong character is present, else advance.

        Does not return anything, but raises a `_NamelistParseError` if `chars`
        does not contain the character at the current position.

        >>> x = _NamelistParser('abc')
        >>> x._expect_char('a')
        >>> x._expect_char('a')
        Traceback (most recent call last):
            ...
        _NamelistParseError: Error in parsing namelist: expected 'a' but found 'b' at line 1, column 1
        >>> x._expect_char('ab')
        >>> x._expect_char('c')
        Traceback (most recent call last):
            ...
        _NamelistEOF: Unexpected end of file encountered in namelist. (At line 1, column 3)
        """
        if self._curr() not in chars:
            raise _NamelistParseError("expected %r but found %r at %s" %
                                      (str(chars), str(self._curr()),
                                       self._line_col_string()))
        self._advance()

    def _parse_namelist_group_name(self):
        r"""Parses and returns a namelist group name at the current position.

        >>> _NamelistParser('abc')._parse_namelist_group_name()
        Traceback (most recent call last):
            ...
        _NamelistParseError: Error in parsing namelist: expected '&' but found 'a' at line 1, column 0
        >>> _NamelistParser('&abc')._parse_namelist_group_name()
        Traceback (most recent call last):
            ...
        _NamelistEOF: Unexpected end of file encountered in namelist. (At line 1, column 4)
        >>> _NamelistParser('&abc ')._parse_namelist_group_name()
        u'abc'
        >>> _NamelistParser('&abc\n')._parse_namelist_group_name()
        u'abc'
        >>> _NamelistParser('&abc/ ')._parse_namelist_group_name()
        Traceback (most recent call last):
            ...
        _NamelistParseError: Error in parsing namelist: 'abc/' is not a valid variable name at line 1, column 5
        >>> _NamelistParser('&abc= ')._parse_namelist_group_name()
        Traceback (most recent call last):
            ...
        _NamelistParseError: Error in parsing namelist: 'abc=' is not a valid variable name at line 1, column 5
        >>> _NamelistParser('& ')._parse_namelist_group_name()
        Traceback (most recent call last):
            ...
        _NamelistParseError: Error in parsing namelist: '' is not a valid variable name at line 1, column 1
        """
        self._expect_char("&")
        return self._parse_variable_name(allow_equals=False)

    def _parse_variable_name(self, allow_equals=True):
        r"""Parses and returns a variable name at the current position.

        The `allow_equals` flag controls whether '=' can denote the end of the
        variable name; if it is `False`, only white space can be used for this
        purpose.

        >>> _NamelistParser('abc')._parse_variable_name()
        Traceback (most recent call last):
            ...
        _NamelistEOF: Unexpected end of file encountered in namelist. (At line 1, column 3)
        >>> _NamelistParser('abc ')._parse_variable_name()
        u'abc'
        >>> _NamelistParser('ABC ')._parse_variable_name()
        u'abc'
        >>> _NamelistParser('abc\n')._parse_variable_name()
        u'abc'
        >>> _NamelistParser('abc=')._parse_variable_name()
        u'abc'
        >>> _NamelistParser('abc, ')._parse_variable_name()
        Traceback (most recent call last):
            ...
        _NamelistParseError: Error in parsing namelist: 'abc,' is not a valid variable name at line 1, column 4
        >>> _NamelistParser(' ')._parse_variable_name()
        Traceback (most recent call last):
            ...
        _NamelistParseError: Error in parsing namelist: '' is not a valid variable name at line 1, column 0
        """
        old_pos = self._pos
        separators = (' ', '\n', '=') if allow_equals else (' ', '\n')
        while self._curr() not in separators:
            self._advance()
        text = self._text[old_pos:self._pos]
        if not is_valid_fortran_name(text):
            raise _NamelistParseError("%r is not a valid variable name at %s" %
                                      (str(text), self._line_col_string()))
        return text.lower()

    def _parse_character_literal(self):
        """Parse and return a character literal (a string).

        >>> _NamelistParser('"abc"')._parse_character_literal()
        Traceback (most recent call last):
            ...
        _NamelistEOF: Unexpected end of file encountered in namelist. (At line 1, column 5)
        >>> _NamelistParser('"abc" ')._parse_character_literal()
        u'"abc"'
        >>> _NamelistParser("'abc' ")._parse_character_literal()
        u"'abc'"
        >>> _NamelistParser("*abc* ")._parse_character_literal()
        Traceback (most recent call last):
            ...
        _NamelistParseError: Error in parsing namelist: *abc* is not a valid character literal at line 1, column 5
        >>> _NamelistParser("'abc''def' ")._parse_character_literal()
        u"'abc''def'"
        >>> _NamelistParser("'abc''' ")._parse_character_literal()
        u"'abc'''"
        >>> _NamelistParser("'''abc' ")._parse_character_literal()
        u"'''abc'"
        """
        delimiter = self._curr()
        old_pos = self._pos
        self._advance()
        while True:
            while self._curr() != delimiter:
                self._advance()
            # Doubled delimiters are escaped.
            if self._next() == delimiter:
                self._advance(2)
            else:
                break
        self._advance()
        text = self._text[old_pos:self._pos]
        if not is_valid_fortran_namelist_literal("character", text):
            raise _NamelistParseError("%s is not a valid character literal at %s" %
                                      (text, self._line_col_string()))
        return text

    def _parse_complex_literal(self):
        """Parse and return a complex literal.

        >>> _NamelistParser('(1.,2.)')._parse_complex_literal()
        Traceback (most recent call last):
            ...
        _NamelistEOF: Unexpected end of file encountered in namelist. (At line 1, column 7)
        >>> _NamelistParser('(1.,2.) ')._parse_complex_literal()
        u'(1.,2.)'
        >>> _NamelistParser("(A,B) ")._parse_complex_literal()
        Traceback (most recent call last):
            ...
        _NamelistParseError: Error in parsing namelist: '(A,B)' is not a valid complex literal at line 1, column 5
        """
        old_pos = self._pos
        while self._curr() != ')':
            self._advance()
        self._advance()
        text = self._text[old_pos:self._pos]
        if not is_valid_fortran_namelist_literal("complex", text):
            raise _NamelistParseError("%r is not a valid complex literal at %s"
                                      % (str(text), self._line_col_string()))
        return text

    def _parse_literal(self, allow_name=False):
        r"""Parse and return a variable value at the current position.

        The basic strategy is this:
        - If a value starts with an apostrophe/quotation mark, parse it as a
        character value (string).
        - If a value starts with a left parenthesis, parse it as a complex
        number.
        - Otherwise, read until the next value separator (comma, space, newline,
        or slash).

        If the argument `allow_name=True` is passed in, we allow the possibility
        that the current position is at the start of the variable name in a new
        name-value pair. In this case, `None` is returned, and the current
        position remains unchanged.

        >>> _NamelistParser('"abc" ')._parse_literal()
        u'"abc"'
        >>> _NamelistParser("'abc' ")._parse_literal()
        u"'abc'"
        >>> _NamelistParser('(1.,2.) ')._parse_literal()
        u'(1.,2.)'
        >>> _NamelistParser('5 ')._parse_literal()
        u'5'
        >>> _NamelistParser('6.9 ')._parse_literal()
        u'6.9'
        >>> _NamelistParser('inf ')._parse_literal()
        u'inf'
        >>> _NamelistParser('nan(booga) ')._parse_literal()
        u'nan(booga)'
        >>> _NamelistParser('.FLORIDA$ ')._parse_literal()
        u'.FLORIDA$'
        >>> _NamelistParser('hamburger ')._parse_literal()
        Traceback (most recent call last):
            ...
        _NamelistParseError: Error in parsing namelist: expected literal value, but got 'hamburger' at line 1, column 9
        >>> _NamelistParser('5,')._parse_literal()
        u'5'
        >>> _NamelistParser('5\n')._parse_literal()
        u'5'
        >>> _NamelistParser('5/')._parse_literal()
        u'5'
        >>> _NamelistParser(',')._parse_literal()
        u''
        >>> _NamelistParser('6*5 ')._parse_literal()
        u'6*5'
        >>> _NamelistParser('6*(1., 2.) ')._parse_literal()
        u'6*(1., 2.)'
        >>> _NamelistParser('6*"a" ')._parse_literal()
        u'6*"a"'
        >>> _NamelistParser('6*')._parse_literal()
        Traceback (most recent call last):
            ...
        _NamelistEOF: Unexpected end of file encountered in namelist. (At line 1, column 2)
        >>> _NamelistParser('foo= ')._parse_literal()
        Traceback (most recent call last):
            ...
        _NamelistParseError: Error in parsing namelist: expected literal value, but got 'foo=' at line 1, column 4
        >>> _NamelistParser('5,')._parse_literal(allow_name=True)
        u'5'
        >>> x = _NamelistParser('foo= ')
        >>> x._parse_literal(allow_name=True)
        >>> x._curr()
        u'f'
        >>> _NamelistParser('6*foo= ')._parse_literal(allow_name=True)
        Traceback (most recent call last):
            ...
        _NamelistParseError: Error in parsing namelist: expected literal value, but got '6*foo=' at line 1, column 6
        >>> x = _NamelistParser('foo = ')
        >>> x._parse_literal(allow_name=True)
        >>> x._curr()
        u'f'
        >>> x = _NamelistParser('foo\n= ')
        >>> x._parse_literal(allow_name=True)
        >>> x._curr()
        u'f'
        >>> x = _NamelistParser('foo\n')
        >>> x._parse_literal(allow_name=True)
        Traceback (most recent call last):
            ...
        _NamelistEOF: Unexpected end of file encountered in namelist. (At line 2, column 0)
        """
        # Deal with a repeated value prefix.
        old_pos = self._pos
        if FORTRAN_REPEAT_PREFIX_REGEX.search(self._text[self._pos:]):
            allow_name = False
            while self._curr() != '*':
                self._advance()
            self._advance()
        prefix = self._text[old_pos:self._pos]
        # Deal with delimited literals.
        if self._curr() in ('"', "'"):
            return prefix + self._parse_character_literal()
        if self._curr() == '(':
            return prefix + self._parse_complex_literal()
        # Deal with non-delimited literals.
        new_pos = self._pos
        while self._text[new_pos] not in (' ', '\n', ',', '/'):
            if allow_name and self._text[new_pos] == '=':
                # In this case it turns out that we have a name rather than a
                # value, so:
                return
            new_pos += 1
            if new_pos == self._len:
                # At the end of the file, give up by throwing an EOF exception.
                self._advance(self._len)
        # If `allow_name` is set, and we ended up on whitespace, we need to
        # check and see if the next non-blank character is '='.
        if allow_name and self._text[new_pos] in (' ', '\n'):
            test_pos = new_pos
            while self._text[test_pos] in (' ', '\n'):
                test_pos += 1
                if test_pos == self._len:
                    self._advance(self._len)
            if self._text[test_pos] == '=':
                return
        self._advance(new_pos - self._pos)
        text = self._text[old_pos:self._pos]
        if not any(is_valid_fortran_namelist_literal(type_, text)
                   for type_ in ("integer", "logical", "real")):
            raise _NamelistParseError("expected literal value, but got %r at %s"
                                      % (str(text), self._line_col_string()))
        return text

    def _expect_separator(self):
        r"""Advance past the current value separator.

        This function raises an error if we are not positioned at a valid value
        separator. It returns `False` if the end-of-namelist ('/') was
        encountered, in which case this function will leave the current position
        at the '/'. This function returns `True` otherwise, and skips to the
        location of the next non-whitespace character.

        >>> x = _NamelistParser("\na")
        >>> x._expect_separator()
        True
        >>> x._curr()
        u'a'
        >>> x = _NamelistParser(" a")
        >>> x._expect_separator()
        True
        >>> x._curr()
        u'a'
        >>> x = _NamelistParser(",a")
        >>> x._expect_separator()
        True
        >>> x._curr()
        u'a'
        >>> x = _NamelistParser("/a")
        >>> x._expect_separator()
        False
        >>> x._curr()
        u'/'
        >>> x = _NamelistParser("a")
        >>> x._expect_separator()
        Traceback (most recent call last):
            ...
        _NamelistParseError: Error in parsing namelist: expected value separator but found 'a' at line 1, column 0
        >>> x = _NamelistParser(" , a")
        >>> x._expect_separator()
        True
        >>> x._curr()
        u'a'
        >>> x = _NamelistParser(" / a")
        >>> x._expect_separator()
        False
        >>> x._curr()
        u'/'
        >>> x = _NamelistParser(" , ! Some stuff\n a")
        >>> x._expect_separator()
        True
        >>> x._curr()
        u'a'
        >>> x = _NamelistParser(" , ! Some stuff\n ! Other stuff\n a")
        >>> x._expect_separator()
        True
        >>> x._curr()
        u'a'
        """
        # Must actually be at a value separator.
        if self._curr() not in (' ', ',', '\n', '/'):
            raise _NamelistParseError("expected value separator but found %r at %s"
                                      % (str(self._curr()), self._line_col_string()))
        self._eat_whitespace()
        if self._curr() == '/':
            return False
        if self._curr() == ',':
            self._advance()
            self._eat_whitespace(allow_initial_comment=True)
        return True

    def _parse_name_and_values(self):
        r"""Parse and return a variable name and values assigned to that name.

        The return value of this function is a tuple containing (a) the name of
        the variable in a string, and (b) a list of the variable's values. Null
        values are represented by the empty string.

        >>> _NamelistParser("foo='bar' /")._parse_name_and_values()
        (u'foo', [u"'bar'"])
        >>> _NamelistParser("foo ='bar' /")._parse_name_and_values()
        (u'foo', [u"'bar'"])
        >>> _NamelistParser("foo=\n'bar' /")._parse_name_and_values()
        (u'foo', [u"'bar'"])
        >>> _NamelistParser("foo 'bar' /")._parse_name_and_values()
        Traceback (most recent call last):
            ...
        _NamelistParseError: Error in parsing namelist: expected '=' but found "'" at line 1, column 4
        >>> _NamelistParser("foo='bar','bazz' /")._parse_name_and_values()
        (u'foo', [u"'bar'", u"'bazz'"])
        >>> _NamelistParser("foo=,,'bazz',6*/")._parse_name_and_values()
        (u'foo', [u'', u'', u"'bazz'", u'6*'])
        >>> _NamelistParser("foo='bar' 'bazz' foo2='ban'")._parse_name_and_values()
        (u'foo', [u"'bar'", u"'bazz'"])
        >>> _NamelistParser("foo= foo2='ban' ")._parse_name_and_values()
        Traceback (most recent call last):
            ...
        _NamelistParseError: Error in parsing namelist: expected literal value, but got "foo2='ban'" at line 1, column 15
        """
        name = self._parse_variable_name()
        self._eat_whitespace()
        self._expect_char("=")
        self._eat_whitespace()
        # Expect at least one literal, even if it's a null value.
        values = [self._parse_literal()]
        # While we haven't reached the end of the namelist group...
        while self._expect_separator():
            # see if we can parse a literal (we might get a variable name)...
            literal = self._parse_literal(allow_name=True)
            if literal is not None:
                # and if it really is a literal, add it.
                values.append(literal)
            else:
                # Otherwise we're done here.
                break
        return name, values

    def _parse_namelist_group(self):
        r"""Parse an entire namelist group, adding info to `self._settings`.

        This function assumes that we start at the beginning of the group name
        (e.g. '&'), and will return at the end of the namelist group ('/').

        >>> x = _NamelistParser("&group /")
        >>> x._parse_namelist_group()
        >>> x._settings
        {u'group': {}}
        >>> x._curr()
        u'/'
        >>> x = _NamelistParser("&group\n foo='bar','bazz'\n,, foo2=2*5\n /")
        >>> x._parse_namelist_group()
        >>> x._settings
        {u'group': {u'foo': [u"'bar'", u"'bazz'", u''], u'foo2': [u'2*5']}}
        >>> x._curr()
        u'/'
        """
        group_name = self._parse_namelist_group_name()
        self._settings[group_name] = {}
        self._eat_whitespace()
        while self._curr() != '/':
            name, values = self._parse_name_and_values()
            self._settings[group_name][name] = values

    def parse_namelist(self):
        r"""Parse the contents of an entire namelist file.

        Returned information is a dictionary of dictionaries, mapping variables
        first by namelist group name, then by variable name.

        >>> _NamelistParser("").parse_namelist()
        {}
        >>> _NamelistParser(" \n!Comment").parse_namelist()
        {}
        >>> _NamelistParser(" &group /").parse_namelist()
        {u'group': {}}
        >>> _NamelistParser("! Comment \n &group /! Comment\n ").parse_namelist()
        {u'group': {}}
        >>> _NamelistParser("! Comment \n &group /! Comment ").parse_namelist()
        {u'group': {}}
        >>> _NamelistParser("&group1\n foo='bar','bazz'\n,, foo2=2*5\n / &group2 /").parse_namelist()
        {u'group1': {u'foo': [u"'bar'", u"'bazz'", u''], u'foo2': [u'2*5']}, u'group2': {}}
        """
        # Return empty dictionary for empty files.
        if self._len == 0:
            return self._settings
        # Remove initial whitespace and comments, and return empty dictionary if
        # that's all we have.
        try:
            self._eat_whitespace(allow_initial_comment=True)
        except _NamelistEOF:
            return self._settings
        # Loop over namelist groups in the file.
        while True:
            self._parse_namelist_group()
            # After each group, try to move forward to the next one. If we run
            # out of text, return what we've found.
            try:
                self._advance()
                self._eat_whitespace(allow_initial_comment=True)
            except _NamelistEOF:
                return self._settings
