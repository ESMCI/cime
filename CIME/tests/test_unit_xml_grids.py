import os
import io
import unittest
import tempfile
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

from CIME.utils import CIMEError
from CIME.XML.grids import Grids


TEST_CONFIG = """<grid_data version="2.0">
    <grids>
        <model_grid_defaults>
            <grid name="atm"    compset="SATM">null</grid>
            <grid name="lnd"    compset="SLND">null</grid>
            <grid name="ocnice" compset="SOCN">null</grid>
            <grid name="rof"    compset="SROF">null</grid>
            <grid name="rof"    compset="DWAV">rx1</grid>
            <grid name="rof"    compset="RTM">r05</grid>
            <grid name="rof"    compset="MOSART">r05</grid>
            <grid name="rof"    compset="DROF">rx1</grid>
            <grid name="rof"    compset="DROF%CPLHIST">r05</grid>
            <grid name="rof"    compset="XROF">r05</grid>
            <grid name="glc"    compset="SGLC">null</grid>
            <grid name="wav"    compset="SWAV">null</grid>
            <grid name="wav"    compset="DWAV">null</grid>
            <grid name="wav"    compset="XWAV">null</grid>
            <grid name="iac"    compset="SIAC">null</grid>
        </model_grid_defaults>

        <model_grid alias="T62_g37" compset="(DATM|XATM|SATM)">
            <grid name="atm">T62</grid>
            <grid name="lnd">T62</grid>
            <grid name="ocnice">gx3v7</grid>
            <grid name="rof">rx1</grid>
            <grid name="glc">null</grid>
            <grid name="wav">null</grid>
            <mask>gx3v7</mask>
        </model_grid>
        <model_grid alias="f05_g16" not_compset="(DATM|XATM|SATM)">
            <grid name="atm">0.47x0.63</grid>
            <grid name="lnd">0.47x0.63</grid>
            <grid name="ocnice">gx1v6</grid>
            <grid name="rof">r05</grid>
            <grid name="glc">null</grid>
            <grid name="wav">null</grid>
            <mask>gx1v6</mask>
        </model_grid>
        <model_grid alias="f02_g16">
            <grid name="atm">0.23x0.31</grid>
            <grid name="lnd">0.23x0.31</grid>
            <grid name="ocnice">gx1v6</grid>
            <grid name="rof">r05</grid>
            <grid name="glc">null</grid>
            <grid name="wav">null</grid>
            <mask>gx1v6</mask>
        </model_grid>
        <model_grid alias="T31_g37_rx1" compset="_DROF">
            <grid name="atm">T31</grid>
            <grid name="lnd">T31</grid>
            <grid name="ocnice">gx3v7</grid>
            <grid name="rof">rx1</grid>
            <grid name="glc">null</grid>
            <grid name="wav">null</grid>
            <mask>gx3v7</mask>
        </model_grid>
        <model_grid alias="f09_g16" compset="DATM.TEST" not_compset="DATM2TEST">
            <grid name="atm">0.9x1.25</grid>
            <grid name="lnd">0.9x1.25</grid>
            <grid name="ocnice">gx1v6</grid>
            <grid name="rof">r05</grid>
            <grid name="glc">null</grid>
            <grid name="wav">null</grid>
            <mask>gx1v6</mask>
        </model_grid>
        <model_grid alias="f19_g16">
            <grid name="atm">1.9x2.5</grid>
            <grid name="lnd">1.9x2.5</grid>
            <grid name="ocnice">gx1v6</grid>
            <grid name="rof">r05</grid>
            <grid name="glc">null</grid>
            <grid name="wav">null</grid>
        </model_grid>
    </grids>
</grid_data>"""


def write_config_grids(tempdir, config):
    config_grids_path = os.path.join(tempdir, "config_grids.xml")

    with open(config_grids_path, "w") as fd:
        fd.write(TEST_CONFIG)

    return config_grids_path


class TestXMLGrids(unittest.TestCase):
    def test_read_config_grids(self):
        with tempfile.TemporaryDirectory() as tempdir:
            config_grids_path = write_config_grids(tempdir, TEST_CONFIG)

            grids = Grids(config_grids_path)

            lname = grids._read_config_grids("T62_g37", "DATM")

            assert lname == "a%T62_l%T62_oi%gx3v7_r%rx1_g%null_w%null_z%null_m%gx3v7"

            with self.assertRaisesRegex(
                CIMEError, "ERROR: grid alias T62_g37 not valid for compset SCREAM"
            ):
                grids._read_config_grids("T62_g37", "SCREAM")

            lname = grids._read_config_grids("f02_g16", "DATM")

            assert (
                lname
                == "a%0.23x0.31_l%0.23x0.31_oi%gx1v6_r%r05_g%null_w%null_z%null_m%gx1v6"
            )

            lname = grids._read_config_grids("f05_g16", "SCREAM")

            assert (
                lname
                == "a%0.47x0.63_l%0.47x0.63_oi%gx1v6_r%r05_g%null_w%null_z%null_m%gx1v6"
            )

            with self.assertRaisesRegex(
                CIMEError, "ERROR: grid alias f05_g16 not valid for compset DATM"
            ):
                grids._read_config_grids("f05_g16", "DATM")

            lname = grids._read_config_grids("T31_g37_rx1", "_DROF")

            assert lname == "a%T31_l%T31_oi%gx3v7_r%rx1_g%null_w%null_z%null_m%gx3v7"

            lname = grids._read_config_grids("f09_g16", "DATM3TEST")

            assert (
                lname
                == "a%0.9x1.25_l%0.9x1.25_oi%gx1v6_r%r05_g%null_w%null_z%null_m%gx1v6"
            )

            with self.assertRaisesRegex(
                CIMEError, "ERROR: grid alias f09_g16 not valid for compset DATM2TEST"
            ):
                grids._read_config_grids("f09_g16", "DATM2TEST")

            lname = grids._read_config_grids("f19_g16", "DATM")

            assert (
                lname
                == "a%1.9x2.5_l%1.9x2.5_oi%gx1v6_r%r05_g%null_w%null_z%null_m%gx1v6"
            )

            lname = grids._read_config_grids(
                "f19_g16", "DATM", atmnlev="2", lndnlev="4"
            )

            assert (
                lname
                == "a%1.9x2.5z2_l%1.9x2.5z4_oi%gx1v6_r%r05_g%null_w%null_z%null_m%gx1v6"
            )
