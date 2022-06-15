import os
import unittest
import tempfile

from CIME.config import Config


class TestConfig(unittest.TestCase):
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
