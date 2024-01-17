#!/usr/bin/env python3

"""
This module tests *some* functionality of CIME.XML.grids
"""

# Ignore privacy concerns for unit tests, so that unit tests can access
# protected members of the system under test
#
# pylint:disable=protected-access

# Also ignore too-long lines, since these are common in unit tests
#
# pylint:disable=line-too-long

import unittest
import os
import shutil
import string
import tempfile
from CIME.XML.grids import Grids, _ComponentGrids, _add_grid_info, _strip_grid_from_name
from CIME.utils import CIMEError


class TestGrids(unittest.TestCase):
    """Tests some functionality of CIME.XML.grids

    Note that much of the functionality of CIME.XML.grids is NOT covered here
    """

    _CONFIG_GRIDS_TEMPLATE = string.Template(
        """<?xml version="1.0"?>

<grid_data version="2.1" xmlns:xi="http://www.w3.org/2001/XInclude">
  <help>
  </help>

  <grids>
    <model_grid_defaults>
      <grid name="atm"       compset="." >atm_default_grid</grid>
      <grid name="lnd"       compset="." >lnd_default_grid</grid>
      <grid name="ocnice"    compset="." >ocnice_default_grid</grid>
      <grid name="rof"       compset="." >rof_default_grid</grid>
      <grid name="glc"	     compset="." >glc_default_grid</grid>
      <grid name="wav"       compset="." >wav_default_grid</grid>
      <grid name="iac"       compset="." >null</grid>
    </model_grid_defaults>

$MODEL_GRID_ENTRIES
  </grids>

  <domains>
    <domain name="null">
      <!-- null grid -->
      <nx>0</nx> <ny>0</ny>
      <file>unset</file>
      <desc>null is no grid: </desc>
    </domain>

$DOMAIN_ENTRIES
  </domains>

  <required_gridmaps>
    <required_gridmap grid1="atm_grid" grid2="ocn_grid">ATM2OCN_FMAPNAME</required_gridmap>
    <required_gridmap grid1="atm_grid" grid2="ocn_grid">OCN2ATM_FMAPNAME</required_gridmap>
$EXTRA_REQUIRED_GRIDMAPS
  </required_gridmaps>

  <gridmaps>
$GRIDMAP_ENTRIES
  </gridmaps>
</grid_data>
"""
    )

    _MODEL_GRID_F09_G17 = """
    <model_grid alias="f09_g17">
      <grid name="atm">0.9x1.25</grid>
      <grid name="lnd">0.9x1.25</grid>
      <grid name="ocnice">gx1v7</grid>
      <mask>gx1v7</mask>
    </model_grid>
"""

    # For testing multiple GLC grids
    _MODEL_GRID_F09_G17_3GLC = """
    <model_grid alias="f09_g17_3glc">
      <grid name="atm">0.9x1.25</grid>
      <grid name="lnd">0.9x1.25</grid>
      <grid name="ocnice">gx1v7</grid>
      <grid name="glc">ais8:gris4:lis12</grid>
      <mask>gx1v7</mask>
    </model_grid>
"""

    _DOMAIN_F09 = """
    <domain name="0.9x1.25">
      <nx>288</nx>  <ny>192</ny>
      <mesh>fv0.9x1.25_ESMFmesh.nc</mesh>
      <desc>0.9x1.25 is FV 1-deg grid:</desc>
    </domain>
"""

    _DOMAIN_G17 = """
    <domain name="gx1v7">
      <nx>320</nx>  <ny>384</ny>
      <mesh>gx1v7_ESMFmesh.nc</mesh>
      <desc>gx1v7 is displaced Greenland pole 1-deg grid with Caspian as a land feature:</desc>
    </domain>
"""

    _DOMAIN_GRIS4 = """
    <domain name="gris4">
      <nx>416</nx> <ny>704</ny>
      <mesh>greenland_4km_ESMFmesh.nc</mesh>
      <desc>4-km Greenland grid</desc>
    </domain>
"""

    _DOMAIN_AIS8 = """
    <domain name="ais8">
      <nx>704</nx> <ny>576</ny>
      <mesh>antarctica_8km_ESMFmesh.nc</mesh>
      <desc>8-km Antarctica grid</desc>
    </domain>
"""

    _DOMAIN_LIS12 = """
    <domain name="lis12">
      <nx>123</nx> <ny>456</ny>
      <mesh>laurentide_12km_ESMFmesh.nc</mesh>
      <desc>12-km Laurentide grid</desc>
    </domain>
"""

    _GRIDMAP_F09_G17 = """
    <!-- The following entries are here to make sure that the code skips gridmap entries with the wrong grids.
         These use the wrong atm grid but the correct ocn grid. -->
    <gridmap atm_grid="foo" ocn_grid="gx1v7">
      <map name="ATM2OCN_FMAPNAME">map_foo_TO_gx1v7_aave.nc</map>
      <map name="OCN2ATM_FMAPNAME">map_gx1v7_TO_foo_aave.nc</map>
      <map name="OCN2ATM_SHOULDBEABSENT">map_gx1v7_TO_foo_xxx.nc</map>
    </gridmap>

    <!-- Here are the gridmaps that should actually be used. -->
    <gridmap atm_grid="0.9x1.25" ocn_grid="gx1v7">
      <map name="ATM2OCN_FMAPNAME">map_fv0.9x1.25_TO_gx1v7_aave.nc</map>
      <map name="OCN2ATM_FMAPNAME">map_gx1v7_TO_fv0.9x1.25_aave.nc</map>
    </gridmap>

    <!-- The following entries are here to make sure that the code skips gridmap entries with the wrong grids.
         These use the wrong ocn grid but the correct atm grid. -->
    <gridmap atm_grid="0.9x1.25" ocn_grid="foo">
      <map name="ATM2OCN_FMAPNAME">map_fv0.9x1.25_TO_foo_aave.nc</map>
      <map name="OCN2ATM_FMAPNAME">map_foo_TO_fv0.9x1.25_aave.nc</map>
      <map name="OCN2ATM_SHOULDBEABSENT">map_foo_TO_fv0.9x1.25_xxx.nc</map>
    </gridmap>
"""

    _GRIDMAP_GRIS4_G17 = """
    <gridmap ocn_grid="gx1v7" glc_grid="gris4" >
      <map name="GLC2OCN_LIQ_RMAPNAME">map_gris4_to_gx1v7_liq.nc</map>
      <map name="GLC2OCN_ICE_RMAPNAME">map_gris4_to_gx1v7_ice.nc</map>
    </gridmap>
"""

    _GRIDMAP_AIS8_G17 = """
    <gridmap ocn_grid="gx1v7" glc_grid="ais8" >
      <map name="GLC2OCN_LIQ_RMAPNAME">map_ais8_to_gx1v7_liq.nc</map>
      <map name="GLC2OCN_ICE_RMAPNAME">map_ais8_to_gx1v7_ice.nc</map>
    </gridmap>
"""

    _GRIDMAP_LIS12_G17 = """
    <gridmap ocn_grid="gx1v7" glc_grid="lis12" >
      <map name="GLC2OCN_LIQ_RMAPNAME">map_lis12_to_gx1v7_liq.nc</map>
      <map name="GLC2OCN_ICE_RMAPNAME">map_lis12_to_gx1v7_ice.nc</map>
    </gridmap>
"""

    def setUp(self):
        self._workdir = tempfile.mkdtemp()
        self._xml_filepath = os.path.join(self._workdir, "config_grids.xml")

    def tearDown(self):
        shutil.rmtree(self._workdir)

    def _create_grids_xml(
        self,
        model_grid_entries,
        domain_entries,
        gridmap_entries,
        extra_required_gridmaps="",
    ):
        grids_xml = self._CONFIG_GRIDS_TEMPLATE.substitute(
            {
                "MODEL_GRID_ENTRIES": model_grid_entries,
                "DOMAIN_ENTRIES": domain_entries,
                "EXTRA_REQUIRED_GRIDMAPS": extra_required_gridmaps,
                "GRIDMAP_ENTRIES": gridmap_entries,
            }
        )
        with open(self._xml_filepath, "w", encoding="UTF-8") as xml_file:
            xml_file.write(grids_xml)

    def assert_grid_info_f09_g17(self, grid_info):
        """Asserts that expected grid info is present and correct when using _MODEL_GRID_F09_G17"""
        self.assertEqual(grid_info["ATM_NX"], 288)
        self.assertEqual(grid_info["ATM_NY"], 192)
        self.assertEqual(grid_info["ATM_GRID"], "0.9x1.25")
        self.assertEqual(grid_info["ATM_DOMAIN_MESH"], "fv0.9x1.25_ESMFmesh.nc")

        self.assertEqual(grid_info["LND_NX"], 288)
        self.assertEqual(grid_info["LND_NY"], 192)
        self.assertEqual(grid_info["LND_GRID"], "0.9x1.25")
        self.assertEqual(grid_info["LND_DOMAIN_MESH"], "fv0.9x1.25_ESMFmesh.nc")

        self.assertEqual(grid_info["OCN_NX"], 320)
        self.assertEqual(grid_info["OCN_NY"], 384)
        self.assertEqual(grid_info["OCN_GRID"], "gx1v7")
        self.assertEqual(grid_info["OCN_DOMAIN_MESH"], "gx1v7_ESMFmesh.nc")

        self.assertEqual(grid_info["ICE_NX"], 320)
        self.assertEqual(grid_info["ICE_NY"], 384)
        self.assertEqual(grid_info["ICE_GRID"], "gx1v7")
        self.assertEqual(grid_info["ICE_DOMAIN_MESH"], "gx1v7_ESMFmesh.nc")

        self.assertEqual(
            grid_info["ATM2OCN_FMAPNAME"], "map_fv0.9x1.25_TO_gx1v7_aave.nc"
        )
        self.assertEqual(
            grid_info["OCN2ATM_FMAPNAME"], "map_gx1v7_TO_fv0.9x1.25_aave.nc"
        )
        self.assertFalse("OCN2ATM_SHOULDBEABSENT" in grid_info)

    def assert_grid_info_f09_g17_3glc(self, grid_info):
        """Asserts that all domain info is present & correct for _MODEL_GRID_F09_G17_3GLC"""
        self.assert_grid_info_f09_g17(grid_info)

        # Note that we don't assert GLC_NX and GLC_NY here: these are unused for this
        # multi-grid case, so we don't care what arbitrary values they have.
        self.assertEqual(grid_info["GLC_GRID"], "ais8:gris4:lis12")
        self.assertEqual(
            grid_info["GLC_DOMAIN_MESH"],
            "antarctica_8km_ESMFmesh.nc:greenland_4km_ESMFmesh.nc:laurentide_12km_ESMFmesh.nc",
        )
        self.assertEqual(
            grid_info["GLC2OCN_LIQ_RMAPNAME"],
            "map_ais8_to_gx1v7_liq.nc:map_gris4_to_gx1v7_liq.nc:map_lis12_to_gx1v7_liq.nc",
        )
        self.assertEqual(
            grid_info["GLC2OCN_ICE_RMAPNAME"],
            "map_ais8_to_gx1v7_ice.nc:map_gris4_to_gx1v7_ice.nc:map_lis12_to_gx1v7_ice.nc",
        )

    def test_get_grid_info_basic(self):
        """Basic test of get_grid_info"""
        model_grid_entries = self._MODEL_GRID_F09_G17
        domain_entries = self._DOMAIN_F09 + self._DOMAIN_G17
        gridmap_entries = self._GRIDMAP_F09_G17
        self._create_grids_xml(
            model_grid_entries=model_grid_entries,
            domain_entries=domain_entries,
            gridmap_entries=gridmap_entries,
        )

        grids = Grids(self._xml_filepath)
        grid_info = grids.get_grid_info(
            name="f09_g17",
            compset="NOT_IMPORTANT",
            driver="nuopc",
        )

        self.assert_grid_info_f09_g17(grid_info)

    def test_get_grid_info_extra_required_gridmaps(self):
        """Test of get_grid_info with some extra required gridmaps"""
        model_grid_entries = self._MODEL_GRID_F09_G17
        domain_entries = self._DOMAIN_F09 + self._DOMAIN_G17
        gridmap_entries = self._GRIDMAP_F09_G17
        # These are some extra required gridmaps that aren't explicitly specified
        extra_required_gridmaps = """
    <required_gridmap grid1="atm_grid" grid2="ocn_grid">ATM2OCN_EXTRA</required_gridmap>
    <required_gridmap grid1="ocn_grid" grid2="atm_grid">OCN2ATM_EXTRA</required_gridmap>
"""
        self._create_grids_xml(
            model_grid_entries=model_grid_entries,
            domain_entries=domain_entries,
            gridmap_entries=gridmap_entries,
            extra_required_gridmaps=extra_required_gridmaps,
        )

        grids = Grids(self._xml_filepath)
        grid_info = grids.get_grid_info(
            name="f09_g17",
            compset="NOT_IMPORTANT",
            driver="nuopc",
        )

        self.assert_grid_info_f09_g17(grid_info)
        self.assertEqual(grid_info["ATM2OCN_EXTRA"], "unset")
        self.assertEqual(grid_info["OCN2ATM_EXTRA"], "unset")

    def test_get_grid_info_extra_gridmaps(self):
        """Test of get_grid_info with some extra gridmaps"""
        model_grid_entries = self._MODEL_GRID_F09_G17
        domain_entries = self._DOMAIN_F09 + self._DOMAIN_G17
        gridmap_entries = self._GRIDMAP_F09_G17
        # These are some extra gridmaps that aren't in the required list
        gridmap_entries += """
    <gridmap atm_grid="0.9x1.25" ocn_grid="gx1v7">
      <map name="ATM2OCN_EXTRA">map_fv0.9x1.25_TO_gx1v7_extra.nc</map>
      <map name="OCN2ATM_EXTRA">map_gx1v7_TO_fv0.9x1.25_extra.nc</map>
    </gridmap>
"""
        self._create_grids_xml(
            model_grid_entries=model_grid_entries,
            domain_entries=domain_entries,
            gridmap_entries=gridmap_entries,
        )

        grids = Grids(self._xml_filepath)
        grid_info = grids.get_grid_info(
            name="f09_g17",
            compset="NOT_IMPORTANT",
            driver="nuopc",
        )

        self.assert_grid_info_f09_g17(grid_info)
        self.assertEqual(grid_info["ATM2OCN_EXTRA"], "map_fv0.9x1.25_TO_gx1v7_extra.nc")
        self.assertEqual(grid_info["OCN2ATM_EXTRA"], "map_gx1v7_TO_fv0.9x1.25_extra.nc")

    def test_get_grid_info_3glc(self):
        """Test of get_grid_info with 3 glc grids"""
        model_grid_entries = self._MODEL_GRID_F09_G17_3GLC
        domain_entries = (
            self._DOMAIN_F09
            + self._DOMAIN_G17
            + self._DOMAIN_GRIS4
            + self._DOMAIN_AIS8
            + self._DOMAIN_LIS12
        )
        gridmap_entries = (
            self._GRIDMAP_F09_G17
            + self._GRIDMAP_GRIS4_G17
            + self._GRIDMAP_AIS8_G17
            + self._GRIDMAP_LIS12_G17
        )
        # Claim that a glc2atm gridmap is required in order to test the logic that handles
        # an unset required gridmap for a component with multiple grids.
        extra_required_gridmaps = """
    <required_gridmap grid1="glc_grid" grid2="atm_grid">GLC2ATM_EXTRA</required_gridmap>
"""
        self._create_grids_xml(
            model_grid_entries=model_grid_entries,
            domain_entries=domain_entries,
            gridmap_entries=gridmap_entries,
            extra_required_gridmaps=extra_required_gridmaps,
        )

        grids = Grids(self._xml_filepath)
        grid_info = grids.get_grid_info(
            name="f09_g17_3glc",
            compset="NOT_IMPORTANT",
            driver="nuopc",
        )

        self.assert_grid_info_f09_g17_3glc(grid_info)
        self.assertEqual(grid_info["GLC2ATM_EXTRA"], "unset")


class TestComponentGrids(unittest.TestCase):
    """Tests the _ComponentGrids helper class defined in CIME.XML.grids"""

    # A valid grid long name used in a lot of these tests; there are two rof grids and
    # three glc grids, and one grid for each other component
    _GRID_LONGNAME = "a%0.9x1.25_l%0.9x1.25_oi%gx1v7_r%r05:r01_g%ais8:gris4:lis12_w%ww3a_z%null_m%gx1v7"

    # ------------------------------------------------------------------------
    # Tests of check_num_elements
    #
    # These tests cover a lot of the code in _ComponentGrids
    #
    # We don't cover all of the branches in check_num_elements because many of the
    # branches that lead to a successful pass are already covered by unit tests in the
    # TestGrids class.
    # ------------------------------------------------------------------------

    def test_check_num_elements_right_ndomains(self):
        """With the right number of domains for a component, check_num_elements should pass"""
        component_grids = _ComponentGrids(self._GRID_LONGNAME)
        gridinfo = {"GLC_DOMAIN_MESH": "foo:bar:baz"}

        # The test passes as long as the following call doesn't generate any errors
        component_grids.check_num_elements(gridinfo)

    def test_check_num_elements_wrong_ndomains(self):
        """With the wrong number of domains for a component, check_num_elements should fail"""
        component_grids = _ComponentGrids(self._GRID_LONGNAME)
        # In the following, there should be 3 elements, but we only specify 2
        gridinfo = {"GLC_DOMAIN_MESH": "foo:bar"}

        self.assertRaisesRegex(
            CIMEError,
            "Unexpected number of colon-delimited elements",
            component_grids.check_num_elements,
            gridinfo,
        )

    def test_check_num_elements_right_nmaps(self):
        """With the right number of maps between two components, check_num_elements should pass"""
        component_grids = _ComponentGrids(self._GRID_LONGNAME)
        gridinfo = {"GLC2ROF_RMAPNAME": "map1:map2:map3:map4:map5:map6"}

        # The test passes as long as the following call doesn't generate any errors
        component_grids.check_num_elements(gridinfo)

    def test_check_num_elements_wrong_nmaps(self):
        """With the wrong number of maps between two components, check_num_elements should fail"""
        component_grids = _ComponentGrids(self._GRID_LONGNAME)
        # In the following, there should be 6 elements, but we only specify 5
        gridinfo = {"GLC2ROF_RMAPNAME": "map1:map2:map3:map4:map5"}

        self.assertRaisesRegex(
            CIMEError,
            "Unexpected number of colon-delimited elements",
            component_grids.check_num_elements,
            gridinfo,
        )


class TestGridsFunctions(unittest.TestCase):
    """Tests helper functions defined in CIME.XML.grids

    These tests are in a separate class to avoid the unnecessary setUp and tearDown
    function of the main test class.

    """

    # ------------------------------------------------------------------------
    # Tests of _add_grid_info
    # ------------------------------------------------------------------------

    def test_add_grid_info_initial(self):
        """Test of _add_grid_info for the initial add of a given key"""
        grid_info = {"foo": "a"}
        _add_grid_info(grid_info, "bar", "b")
        self.assertEqual(grid_info, {"foo": "a", "bar": "b"})

    def test_add_grid_info_existing(self):
        """Test of _add_grid_info when the given key already exists"""
        grid_info = {"foo": "bar"}
        _add_grid_info(grid_info, "foo", "baz")
        self.assertEqual(grid_info, {"foo": "bar:baz"})

    def test_add_grid_info_existing_with_value_for_multiple(self):
        """Test of _add_grid_info when the given key already exists and value_for_multiple is provided"""
        grid_info = {"foo": 1}
        _add_grid_info(grid_info, "foo", 2, value_for_multiple=0)
        self.assertEqual(grid_info, {"foo": 0})

    # ------------------------------------------------------------------------
    # Tests of strip_grid_from_name
    # ------------------------------------------------------------------------

    def test_strip_grid_from_name_basic(self):
        """Basic test of _strip_grid_from_name"""
        result = _strip_grid_from_name("atm_grid")
        self.assertEqual(result, "atm")

    def test_strip_grid_from_name_badname(self):
        """_strip_grid_from_name should raise an exception for a name not ending with _grid"""
        self.assertRaisesRegex(
            CIMEError, "does not end with _grid", _strip_grid_from_name, name="atm"
        )

    # ------------------------------------------------------------------------
    # Tests of _check_grid_info_component_counts
    # ------------------------------------------------------------------------


if __name__ == "__main__":
    unittest.main()
