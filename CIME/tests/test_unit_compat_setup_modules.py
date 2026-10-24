"""Compatibility tests for the legacy ``standard_*_setup`` modules.

External code (E3SM, CESM, NorESM ``cime_config`` and component scripts) still
does ``from standard_script_setup import *`` and
``from CIME.XML.standard_module_setup import *``. These tests pin down the names
and side effects those imports provide so the shims cannot drift silently.

Each star import runs in a fresh interpreter because the modules mutate
``sys.path`` and ``os.environ`` at import time.
"""

import json
import os
import subprocess
import sys
import textwrap

CIMEROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TOOLS_DIR = os.path.join(CIMEROOT, "CIME", "Tools")

SCRIPT_SETUP_EXPORTS = {
    "CIME",
    "argparse",
    "check_minimum_python_version",
    "cimeroot",
    "logging",
    "main",
    "os",
    "real_file_dir",
    "sys",
}

MODULE_SETUP_EXPORTS = {
    "LIB_DIR",
    "expect",
    "get_cime_root",
    "logging",
    "os",
    "re",
    "run_cmd",
    "run_cmd_no_fail",
    "sys",
}

_RUNNER = textwrap.dedent(
    """
    import json, os, sys

    sys.path = [p for p in sys.path if p not in {drop!r}]
    {prelude}

    namespace = {{}}
    exec({statement!r}, namespace)

    namespace.pop("__builtins__", None)
    print(json.dumps({{
        "names": sorted(namespace),
        "cimeroot_env": os.environ.get("CIMEROOT"),
        "unbuffered_env": os.environ.get("PYTHONUNBUFFERED"),
        "sys_path": sys.path,
        "values": {{k: str(v) for k, v in namespace.items() if isinstance(v, str)}},
        "same_expect": namespace.get("expect") is not None
        and namespace["expect"].__module__ == "CIME.utils",
    }}))
    """
)


def run_star_import(
    statement, prelude="", env_overrides=None, python=sys.executable, cwd=None
):
    """Run ``statement`` in a clean interpreter and return its observations.

    Args:
        statement: Source executed in an empty namespace, e.g. a star import.
        prelude: Source run before ``statement``, used to set up ``sys.path``.
        env_overrides: Extra environment variables for the subprocess.
        python: Interpreter used for the subprocess.
        cwd: Working directory for the subprocess.

    Returns:
        Parsed JSON with the exported names and process side effects.
    """
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env.pop("CIMEROOT", None)
    env.update(env_overrides or {})

    code = _RUNNER.format(
        drop=[CIMEROOT, TOOLS_DIR], prelude=prelude, statement=statement
    )

    proc = subprocess.run(
        [python, "-c", code],
        env=env,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr

    return json.loads(proc.stdout.strip().splitlines()[-1])


def run_snippet(code, prelude="", env_overrides=None, cwd=None):
    """Run ``code`` in a clean interpreter and return the completed process."""
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env.pop("CIMEROOT", None)
    env.update(env_overrides or {})

    source = (
        f"import sys\nsys.path = [p for p in sys.path if p not in "
        f"{[CIMEROOT, TOOLS_DIR]!r}]\n{prelude}\n{code}"
    )

    return subprocess.run(
        [sys.executable, "-c", source],
        env=env,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def tools_only_prelude():
    """Mimic external callers that add only ``CIME/Tools`` to ``sys.path``."""
    return f"sys.path.insert(0, {TOOLS_DIR!r})"


class TestStandardScriptSetup:
    """Bare ``from standard_script_setup import *`` used by external tools."""

    def test_star_import_exports_legacy_names(self, tmp_path):
        # Act
        result = run_star_import(
            "from standard_script_setup import *",
            prelude=tools_only_prelude(),
            cwd=tmp_path,
        )

        # Assert
        assert set(result["names"]) == SCRIPT_SETUP_EXPORTS

    def test_star_import_sets_cimeroot_and_prepends_path(self, tmp_path):
        # Act
        result = run_star_import(
            "from standard_script_setup import *",
            prelude=tools_only_prelude(),
            cwd=tmp_path,
        )

        # Assert
        assert result["cimeroot_env"] == CIMEROOT
        assert result["values"]["cimeroot"] == CIMEROOT
        assert result["sys_path"][0] == CIMEROOT

    def test_star_import_stops_output_buffering(self, tmp_path):
        # Act
        result = run_star_import(
            "from standard_script_setup import *",
            prelude=tools_only_prelude(),
            cwd=tmp_path,
        )

        # Assert
        assert result["unbuffered_env"] == "1"

    def test_star_import_overrides_existing_cimeroot(self, tmp_path):
        # Context
        stale = str(tmp_path / "stale_cimeroot")

        # Act
        result = run_star_import(
            "from standard_script_setup import *",
            prelude=tools_only_prelude(),
            env_overrides={"CIMEROOT": stale},
            cwd=tmp_path,
        )

        # Assert
        assert result["cimeroot_env"] == CIMEROOT

    def test_star_import_from_package_path_matches_bare_import(self, tmp_path):
        # Context
        prelude = f"sys.path.insert(0, {CIMEROOT!r})"

        # Act
        result = run_star_import(
            "from CIME.Tools.standard_script_setup import *",
            prelude=prelude,
            cwd=tmp_path,
        )

        # Assert
        assert set(result["names"]) == SCRIPT_SETUP_EXPORTS

    def test_star_import_fails_without_tools_on_path(self, tmp_path):
        # Act
        proc = run_snippet("from standard_script_setup import *", cwd=tmp_path)

        # Assert
        assert proc.returncode != 0
        assert "standard_script_setup" in proc.stderr

    def test_check_minimum_python_version_passes_current(self, tmp_path):
        # Act
        proc = run_snippet(
            "from standard_script_setup import check_minimum_python_version\n"
            "check_minimum_python_version(3, 0)",
            prelude=tools_only_prelude(),
            cwd=tmp_path,
        )

        # Assert
        assert proc.returncode == 0, proc.stderr

    def test_check_minimum_python_version_raises_for_future_version(self, tmp_path):
        # Act
        proc = run_snippet(
            "from standard_script_setup import check_minimum_python_version\n"
            "check_minimum_python_version(99, 0)",
            prelude=tools_only_prelude(),
            cwd=tmp_path,
        )

        # Assert
        assert proc.returncode != 0
        assert "is required to run CIME" in proc.stderr

    def test_check_minimum_python_version_warn_only(self, tmp_path):
        # Act
        proc = run_snippet(
            "from standard_script_setup import check_minimum_python_version\n"
            "check_minimum_python_version(99, 0, warn_only=True)",
            prelude=tools_only_prelude(),
            cwd=tmp_path,
        )

        # Assert
        assert proc.returncode == 0, proc.stderr
        assert "recommended" in proc.stderr


class TestStandardModuleSetup:
    """``from CIME.XML.standard_module_setup import *`` used by downstream code."""

    def test_star_import_exports_legacy_names(self, tmp_path):
        # Act
        result = run_star_import(
            "from CIME.XML.standard_module_setup import *",
            prelude=f"sys.path.insert(0, {CIMEROOT!r})",
            cwd=tmp_path,
        )

        # Assert
        assert set(result["names"]) == MODULE_SETUP_EXPORTS

    def test_star_import_exports_cime_utils_helpers(self, tmp_path):
        # Act
        result = run_star_import(
            "from CIME.XML.standard_module_setup import *",
            prelude=f"sys.path.insert(0, {CIMEROOT!r})",
            cwd=tmp_path,
        )

        # Assert
        assert result["same_expect"] is True

    def test_star_import_exports_lib_dir_as_cimeroot(self, tmp_path):
        # Act
        result = run_star_import(
            "from CIME.XML.standard_module_setup import *",
            prelude=f"sys.path.insert(0, {CIMEROOT!r})",
            cwd=tmp_path,
        )

        # Assert
        assert result["values"]["LIB_DIR"] == CIMEROOT

    def test_star_import_keeps_cimeroot_on_path(self, tmp_path):
        # Act
        result = run_star_import(
            "from CIME.XML.standard_module_setup import *",
            prelude=f"sys.path.insert(0, {CIMEROOT!r})",
            cwd=tmp_path,
        )

        # Assert
        assert CIMEROOT in result["sys_path"]

    def test_star_import_does_not_touch_script_environment(self, tmp_path):
        # Act
        result = run_star_import(
            "from CIME.XML.standard_module_setup import *",
            prelude=f"sys.path.insert(0, {CIMEROOT!r})",
            cwd=tmp_path,
        )

        # Assert
        assert result["cimeroot_env"] is None
        assert result["unbuffered_env"] is None

    def test_star_import_fails_without_cime_on_path(self, tmp_path):
        # Act
        proc = run_snippet("from CIME.XML.standard_module_setup import *", cwd=tmp_path)

        # Assert
        assert proc.returncode != 0
        assert "No module named 'CIME'" in proc.stderr
