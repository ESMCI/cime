import logging
import os

from CIME.utils import CIMEError
from CIME.XML.files import Files

logger = logging.getLogger(__name__)

MODS_DIR_VARS = ("TESTS_MODS_DIR", "USER_MODS_DIR")


def find_test_mods(comp_interface, test_mods):
    """Finds paths from names of testmods.

    Testmod format is `${component}-${testmod}`. Each testmod is search for
    it it's component respective `TESTS_MODS_DIR` and `USER_MODS_DIR`.

    Args:
        comp_interface (str): Name of the component interface.
        test_mods (list): List of testmods names.

    Returns:
        List of paths for each testmod.

    Raises:
        CIMEError: If a testmod is not in correct format.
        CIMEError: If testmod could not be found.
    """
    if test_mods is None:
        return []

    files = Files(comp_interface=comp_interface)

    test_mods_paths = []

    logger.debug("Checking for testmods {}".format(test_mods))

    for test_mod in test_mods:
        if test_mod.find("/") != -1:
            component, mod_path = test_mod.split("/", 1)
        else:
            raise CIMEError(
                f"Invalid testmod, format should be `${{component}}-${{testmod}}`, got {test_mod!r}"
            )

        logger.info(
            "Searching for testmod {!r} for component {!r}".format(mod_path, component)
        )

        test_mod_path = None

        for var in MODS_DIR_VARS:
            mods_dir = files.get_value(var, {"component": component})

            try:
                candidate_path = os.path.join(mods_dir, component, mod_path)
            except TypeError:
                # mods_dir is None
                continue

            logger.debug(
                "Checking for testmod {!r} in {!r}".format(test_mod, candidate_path)
            )

            if os.path.exists(candidate_path):
                test_mod_path = candidate_path

                logger.info(
                    "Found testmod {!r} for component {!r} in {!r}".format(
                        mod_path, component, test_mod_path
                    )
                )

                break

        if test_mod_path is None:
            raise CIMEError(f"Could not locate testmod {mod_path!r}")

        test_mods_paths.append(test_mod_path)

    return test_mods_paths
