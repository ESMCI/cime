"""Unit tests for the ERIO system test."""

from unittest.mock import MagicMock, patch

import pytest

from CIME.SystemTests.erio import ERIO


@pytest.mark.parametrize(
    "pio_netcdf_formats, expected_pio_types",
    [
        (["64bit_data"], ["netcdf", "pnetcdf", "default", "nothing"]),
        (
            ["classic", "64bit_offset"],
            ["netcdf", "pnetcdf", "netcdf4p", "netcdf4c", "default", "nothing"],
        ),
        ([], ["netcdf", "pnetcdf", "netcdf4p", "netcdf4c", "default", "nothing"]),
    ],
)
def test_init_filters_incompatible_pio_types(pio_netcdf_formats, expected_pio_types):
    """ERIO should not try PIO types invalid for the configured file formats."""
    # Context
    case = MagicMock()
    run_env = case.get_env.return_value
    run_env.get_valid_values.return_value = [
        "netcdf",
        "pnetcdf",
        "netcdf4p",
        "netcdf4c",
        "default",
        "nothing",
    ]
    run_env.get_values.return_value = pio_netcdf_formats
    case.get_value.return_value = 5

    # Mocks
    with patch(
        "CIME.SystemTests.erio.SystemTestsCommon.__init__",
        side_effect=lambda instance, case, **kwargs: setattr(instance, "_case", case),
    ):
        # Act
        erio = ERIO(case)

    # Assert
    assert erio._pio_types == expected_pio_types
    run_env.get_values.assert_called_once_with("PIO_NETCDF_FORMAT")
