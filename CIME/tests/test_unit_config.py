import os
import unittest
import tempfile

from CIME.config import Config


class TestConfig(unittest.TestCase):
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
