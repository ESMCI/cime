import os
import unittest
import tempfile
from unittest import mock
from pathlib import Path

from CIME.config import Config


def spy(method):
    m = mock.MagicMock()

    def wrapper(self, *args, **kwargs):
        m(*args, **kwargs)
        return method(self, *args, **kwargs)

    wrapper.mock = m
    return wrapper


class TestConfig(unittest.TestCase):
    def test_ignore(self):
        test_paths = (
            ("valid.py", False),
            ("module/valid.py", False),
            ("valid_test.py", False),
            ("test_something.py", True),
            ("tests/test_something.py", True),
            ("conftest.py", True),
            ("tests/conftest.py", True),
            ("tests/generic/test_something.py", True),
            ("tests/generic/conftest.py", True),
        )

        with tempfile.TemporaryDirectory() as _tempdir:
            for src_path_name in ("generic", "test", "tests"):
                customize_path = Path(
                    _tempdir, src_path_name, "cime_config", "customize"
                )

                for test_path_name, _ in test_paths:
                    test_file = customize_path / test_path_name

                    test_file.parent.mkdir(parents=True, exist_ok=True)

                    test_file.touch()

                with mock.patch(
                    "CIME.config.Config._load_file", spy(Config._load_file)
                ) as mock_load_file:
                    _ = Config.load(f"{customize_path}")

                    loaded_files = [
                        f'{Path(x[0][0]).relative_to(f"{customize_path}")}'
                        for x in mock_load_file.mock.call_args_list
                    ]

                    for test_path_name, ignored in test_paths:
                        if ignored:
                            assert test_path_name not in loaded_files
                        else:
                            assert test_path_name in loaded_files

    def test_class_external(self):
        with tempfile.TemporaryDirectory() as tempdir:
            complex_file = os.path.join(tempdir, "01_complex.py")

            with open(complex_file, "w") as fd:
                fd.write(
                    """
class TestComplex:
    def do_something(self):
        print("Something complex")
                    """
                )

            test_file = os.path.join(tempdir, "02_test.py")

            with open(test_file, "w") as fd:
                fd.write(
                    """
from CIME.customize import TestComplex

use_feature1 = True
use_feature2 = False

def prerun_provenance(case, **kwargs):
    print("prerun_provenance")

    external = TestComplex()

    external.do_something()

    return True
                """
                )

            config = Config.load(tempdir)

            assert config.use_feature1
            assert not config.use_feature2
            assert config.prerun_provenance
            assert config.prerun_provenance("test")

            with self.assertRaises(AttributeError):
                config.postrun_provenance("test")

    def test_class(self):
        with tempfile.TemporaryDirectory() as tempdir:
            test_file = os.path.join(tempdir, "test.py")

            with open(test_file, "w") as fd:
                fd.write(
                    """
use_feature1 = True
use_feature2 = False

class TestComplex:
    def do_something(self):
        print("Something complex")

def prerun_provenance(case, **kwargs):
    print("prerun_provenance")

    external = TestComplex()

    external.do_something()

    return True
                """
                )

            config = Config.load(tempdir)

            assert config.use_feature1
            assert not config.use_feature2
            assert config.prerun_provenance
            assert config.prerun_provenance("test")

            with self.assertRaises(AttributeError):
                config.postrun_provenance("test")

    def test_load(self):
        with tempfile.TemporaryDirectory() as tempdir:
            test_file = os.path.join(tempdir, "test.py")

            with open(test_file, "w") as fd:
                fd.write(
                    """
use_feature1 = True
use_feature2 = False

def prerun_provenance(case, **kwargs):
    print("prerun_provenance")

    return True
                """
                )

            config = Config.load(tempdir)

            assert config.use_feature1
            assert not config.use_feature2
            assert config.prerun_provenance
            assert config.prerun_provenance("test")

            with self.assertRaises(AttributeError):
                config.postrun_provenance("test")

    def test_overwrite(self):
        with tempfile.TemporaryDirectory() as tempdir:
            test_file = os.path.join(tempdir, "test.py")

            with open(test_file, "w") as fd:
                fd.write(
                    """
use_feature1 = True
use_feature2 = False

def prerun_provenance(case, **kwargs):
    print("prerun_provenance")

    return True
                """
                )

            Config.use_feature1 = False

            config = Config.load(tempdir)

            assert config.use_feature1
