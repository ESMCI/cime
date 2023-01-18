#!/usr/bin/env python3

import os
import stat
import shutil
import sys
import tempfile

import unittest
from unittest import mock
from CIME.utils import (
    indent_string,
    run_and_log_case_status,
    import_from_file,
    _line_defines_python_function,
    file_contains_python_function,
    copy_globs,
    import_and_run_sub_or_cmd,
)


class TestIndentStr(unittest.TestCase):
    """Test the indent_string function."""

    def test_indent_string_singleline(self):
        """Test the indent_string function with a single-line string"""
        mystr = "foo"
        result = indent_string(mystr, 4)
        expected = "    foo"
        self.assertEqual(expected, result)

    def test_indent_string_multiline(self):
        """Test the indent_string function with a multi-line string"""
        mystr = """hello
hi
goodbye
"""
        result = indent_string(mystr, 2)
        expected = """  hello
  hi
  goodbye
"""
        self.assertEqual(expected, result)


class TestLineDefinesPythonFunction(unittest.TestCase):
    """Tests of _line_defines_python_function"""

    # ------------------------------------------------------------------------
    # Tests of _line_defines_python_function that should return True
    # ------------------------------------------------------------------------

    def test_def_foo(self):
        """Test of a def of the function of interest"""
        line = "def foo():"
        self.assertTrue(_line_defines_python_function(line, "foo"))

    def test_def_foo_space(self):
        """Test of a def of the function of interest, with an extra space before the parentheses"""
        line = "def foo ():"
        self.assertTrue(_line_defines_python_function(line, "foo"))

    def test_import_foo(self):
        """Test of an import of the function of interest"""
        line = "from bar.baz import foo"
        self.assertTrue(_line_defines_python_function(line, "foo"))

    def test_import_foo_space(self):
        """Test of an import of the function of interest, with trailing spaces"""
        line = "from bar.baz import foo  "
        self.assertTrue(_line_defines_python_function(line, "foo"))

    def test_import_foo_then_others(self):
        """Test of an import of the function of interest, along with others"""
        line = "from bar.baz import foo, bar"
        self.assertTrue(_line_defines_python_function(line, "foo"))

    def test_import_others_then_foo(self):
        """Test of an import of the function of interest, after others"""
        line = "from bar.baz import bar, foo"
        self.assertTrue(_line_defines_python_function(line, "foo"))

    # ------------------------------------------------------------------------
    # Tests of _line_defines_python_function that should return False
    # ------------------------------------------------------------------------

    def test_def_barfoo(self):
        """Test of a def of a different function"""
        line = "def barfoo():"
        self.assertFalse(_line_defines_python_function(line, "foo"))

    def test_def_foobar(self):
        """Test of a def of a different function"""
        line = "def foobar():"
        self.assertFalse(_line_defines_python_function(line, "foo"))

    def test_def_foo_indented(self):
        """Test of a def of the function of interest, but indented"""
        line = "    def foo():"
        self.assertFalse(_line_defines_python_function(line, "foo"))

    def test_def_foo_no_parens(self):
        """Test of a def of the function of interest, but without parentheses"""
        line = "def foo:"
        self.assertFalse(_line_defines_python_function(line, "foo"))

    def test_import_foo_indented(self):
        """Test of an import of the function of interest, but indented"""
        line = "    from bar.baz import foo"
        self.assertFalse(_line_defines_python_function(line, "foo"))

    def test_import_barfoo(self):
        """Test of an import of a different function"""
        line = "from bar.baz import barfoo"
        self.assertFalse(_line_defines_python_function(line, "foo"))

    def test_import_foobar(self):
        """Test of an import of a different function"""
        line = "from bar.baz import foobar"
        self.assertFalse(_line_defines_python_function(line, "foo"))


class TestFileContainsPythonFunction(unittest.TestCase):
    """Tests of file_contains_python_function"""

    def setUp(self):
        self._workdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._workdir, ignore_errors=True)

    def create_test_file(self, contents):
        """Creates a test file with the given contents, and returns the path to that file"""

        filepath = os.path.join(self._workdir, "testfile")
        with open(filepath, "w") as fd:
            fd.write(contents)

        return filepath

    def test_contains_correct_def_and_others(self):
        """Test file_contains_python_function with a correct def mixed with other defs"""
        contents = """
def bar():
def foo():
def baz():
"""
        filepath = self.create_test_file(contents)
        self.assertTrue(file_contains_python_function(filepath, "foo"))

    def test_does_not_contain_correct_def(self):
        """Test file_contains_python_function without the correct def"""
        contents = """
def bar():
def notfoo():
def baz():
"""
        filepath = self.create_test_file(contents)
        self.assertFalse(file_contains_python_function(filepath, "foo"))


class MockTime(object):
    def __init__(self):
        self._old = None

    def __enter__(self):
        self._old = getattr(sys.modules["time"], "strftime")
        setattr(sys.modules["time"], "strftime", lambda *args: "00:00:00 ")

    def __exit__(self, *args, **kwargs):
        setattr(sys.modules["time"], "strftime", self._old)


def match_all_lines(data, lines):
    for line in data:
        for i, x in enumerate(lines):
            if x == line:
                lines.pop(i)

                continue

        if len(lines) == 0:
            return True, []

    return False, lines


class TestUtils(unittest.TestCase):
    def setUp(self):
        self.base_func = lambda *args: None

        # pylint: disable=unused-argument
        def _error_func(*args):
            raise Exception("Something went wrong")

        self.error_func = _error_func

    def test_import_and_run_sub_or_cmd(self):
        with self.assertRaisesRegex(
            Exception, "ERROR: Could not find buildnml file for component test"
        ):
            import_and_run_sub_or_cmd(
                "/tmp/buildnml",
                "arg1 arg2 -vvv",
                "buildnml",
                (self, "arg1"),
                "/tmp",
                "test",
            )

    @mock.patch("importlib.import_module")
    def test_import_and_run_sub_or_cmd_cime_py(self, importmodule):
        importmodule.side_effect = Exception("Module has a problem")

        with self.assertRaisesRegex(Exception, "Module has a problem") as e:
            import_and_run_sub_or_cmd(
                "/tmp/buildnml",
                "arg1, arg2 -vvv",
                "buildnml",
                (self, "arg1"),
                "/tmp",
                "test",
            )

        # check that we avoid exception chaining
        self.assertTrue(e.exception.__context__ is None)

    @mock.patch("importlib.import_module")
    def test_import_and_run_sub_or_cmd_import(self, importmodule):
        importmodule.side_effect = Exception("I am being imported")

        with self.assertRaisesRegex(Exception, "I am being imported") as e:
            import_and_run_sub_or_cmd(
                "/tmp/buildnml",
                "arg1 arg2 -vvv",
                "buildnml",
                (self, "arg1"),
                "/tmp",
                "test",
            )

        # check that we avoid exception chaining
        self.assertTrue(e.exception.__context__ is None)

    @mock.patch("os.path.isfile")
    @mock.patch("CIME.utils.run_sub_or_cmd")
    def test_import_and_run_sub_or_cmd_run(self, func, isfile):
        isfile.return_value = True

        func.side_effect = Exception(
            "ERROR: /tmp/buildnml arg1 arg2 -vvv FAILED, see above"
        )

        with self.assertRaisesRegex(
            Exception, "ERROR: /tmp/buildnml arg1 arg2 -vvv FAILED, see above"
        ):
            import_and_run_sub_or_cmd(
                "/tmp/buildnml",
                "arg1 arg2 -vvv",
                "buildnml",
                (self, "arg1"),
                "/tmp",
                "test",
            )

    @mock.patch("glob.glob")
    @mock.patch("CIME.utils.safe_copy")
    def test_copy_globs(self, safe_copy, glob):
        glob.side_effect = [
            [],
            ["/src/run/test.sh", "/src/run/.hidden.sh"],
            [
                "/src/bld/test.nc",
            ],
        ]

        copy_globs(["CaseDocs/*", "run/*.sh", "bld/*.nc"], "/storage/output", "uid")

        safe_copy.assert_any_call(
            "/src/run/test.sh", "/storage/output/test.sh.uid", preserve_meta=False
        )
        safe_copy.assert_any_call(
            "/src/run/.hidden.sh", "/storage/output/hidden.sh.uid", preserve_meta=False
        )
        safe_copy.assert_any_call(
            "/src/bld/test.nc", "/storage/output/test.nc.uid", preserve_meta=False
        )

    def assertMatchAllLines(self, tempdir, test_lines):
        with open(os.path.join(tempdir, "CaseStatus")) as fd:
            data = fd.readlines()

        result, missing = match_all_lines(data, test_lines)

        error = []

        if len(missing) != 0:
            error.extend(["Missing Lines", ""])
            error.extend([x.rstrip("\n") for x in missing])
            error.extend(["", "Tempfile contents", ""])
            error.extend([x.rstrip("\n") for x in data])

        self.assertTrue(result, msg="\n".join(error))

    def test_import_from_file(self):
        with tempfile.NamedTemporaryFile() as fd:
            fd.writelines(
                [
                    b"def test():\n",
                    b"  return 'value'",
                ]
            )

            fd.flush()

            module = import_from_file("test.py", fd.name)

            assert module.test() == "value"

    def test_run_and_log_case_status(self):
        test_lines = [
            "00:00:00 default starting \n",
            "00:00:00 default success \n",
        ]

        with tempfile.TemporaryDirectory() as tempdir, MockTime():
            run_and_log_case_status(self.base_func, "default", caseroot=tempdir)

            self.assertMatchAllLines(tempdir, test_lines)

    def test_run_and_log_case_status_case_submit_on_batch(self):
        test_lines = [
            "00:00:00 case.submit starting \n",
            "00:00:00 case.submit success \n",
        ]

        with tempfile.TemporaryDirectory() as tempdir, MockTime():
            run_and_log_case_status(
                self.base_func, "case.submit", caseroot=tempdir, is_batch=True
            )

            self.assertMatchAllLines(tempdir, test_lines)

    def test_run_and_log_case_status_case_submit_no_batch(self):
        test_lines = [
            "00:00:00 case.submit starting \n",
            "00:00:00 case.submit success \n",
        ]

        with tempfile.TemporaryDirectory() as tempdir, MockTime():
            run_and_log_case_status(
                self.base_func, "case.submit", caseroot=tempdir, is_batch=False
            )

            self.assertMatchAllLines(tempdir, test_lines)

    def test_run_and_log_case_status_case_submit_error_on_batch(self):
        test_lines = [
            "00:00:00 case.submit starting \n",
            "00:00:00 case.submit error \n",
            "Something went wrong\n",
        ]

        with tempfile.TemporaryDirectory() as tempdir, MockTime():
            with self.assertRaises(Exception):
                run_and_log_case_status(
                    self.error_func, "case.submit", caseroot=tempdir, is_batch=True
                )

            self.assertMatchAllLines(tempdir, test_lines)

    def test_run_and_log_case_status_custom_msg(self):
        test_lines = [
            "00:00:00 default starting starting extra\n",
            "00:00:00 default success success extra\n",
        ]

        starting_func = mock.MagicMock(return_value="starting extra")
        success_func = mock.MagicMock(return_value="success extra")

        def normal_func():
            return "data"

        with tempfile.TemporaryDirectory() as tempdir, MockTime():
            run_and_log_case_status(
                normal_func,
                "default",
                custom_starting_msg_functor=starting_func,
                custom_success_msg_functor=success_func,
                caseroot=tempdir,
            )

            self.assertMatchAllLines(tempdir, test_lines)

        starting_func.assert_called_with()
        success_func.assert_called_with("data")

    def test_run_and_log_case_status_custom_msg_error_on_batch(self):
        test_lines = [
            "00:00:00 default starting starting extra\n",
            "00:00:00 default success success extra\n",
        ]

        starting_func = mock.MagicMock(return_value="starting extra")
        success_func = mock.MagicMock(return_value="success extra")

        def error_func():
            raise Exception("Error")

        with tempfile.TemporaryDirectory() as tempdir, MockTime(), self.assertRaises(
            Exception
        ):
            run_and_log_case_status(
                error_func,
                "default",
                custom_starting_msg_functor=starting_func,
                custom_success_msg_functor=success_func,
                caseroot=tempdir,
            )

            self.assertMatchAllLines(tempdir, test_lines)

        starting_func.assert_called_with()
        success_func.assert_not_called()

    def test_run_and_log_case_status_error(self):
        test_lines = [
            "00:00:00 default starting \n",
            "00:00:00 default error \n",
            "Something went wrong\n",
        ]

        with tempfile.TemporaryDirectory() as tempdir, MockTime():
            with self.assertRaises(Exception):
                run_and_log_case_status(self.error_func, "default", caseroot=tempdir)

            self.assertMatchAllLines(tempdir, test_lines)


if __name__ == "__main__":
    unittest.main()
