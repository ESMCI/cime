"""Unit tests for CIME.core.config.bootstrap."""

import os
import sys

import pytest

from CIME.core.config.bootstrap import (
    _prepend_sys_path,
    _is_cimeroot,
    bootstrap_cime,
    check_minimum_python_version,
    find_cimeroot,
    get_tools_path,
)


class TestFindCimeroot:
    def test_explicit_dir(self, tmp_path):
        """find_cimeroot accepts an explicit directory with a CIME/ subdir."""
        (tmp_path / "CIME").mkdir()
        root = find_cimeroot(str(tmp_path))
        assert root == str(tmp_path.resolve())

    def test_explicit_dir_invalid(self, tmp_path):
        with pytest.raises(RuntimeError, match="not a valid CIMEROOT"):
            find_cimeroot(str(tmp_path))

    def test_env_var(self, tmp_path, monkeypatch):
        (tmp_path / "CIME").mkdir()
        monkeypatch.setenv("CIMEROOT", str(tmp_path))
        root = find_cimeroot()
        assert root == str(tmp_path.resolve())

    def test_walks_up_from_file(self):
        """The default detection should find the real CIMEROOT from this repo."""
        root = find_cimeroot()
        assert os.path.isdir(os.path.join(root, "CIME"))


class TestIsCimeroot:
    def test_valid(self, tmp_path):
        (tmp_path / "CIME").mkdir()
        assert _is_cimeroot(str(tmp_path)) is True

    def test_invalid(self, tmp_path):
        assert _is_cimeroot(str(tmp_path)) is False


class TestBootstrapCime:
    def setup_method(self):
        self._orig_path = sys.path[:]
        self._orig_env = os.environ.get("CIMEROOT")

    def teardown_method(self):
        sys.path[:] = self._orig_path
        if self._orig_env is not None:
            os.environ["CIMEROOT"] = self._orig_env
        else:
            os.environ.pop("CIMEROOT", None)

    def test_bootstrap_sets_sys_path(self, tmp_path):
        (tmp_path / "CIME" / "Tools").mkdir(parents=True)
        root = bootstrap_cime(cimeroot=str(tmp_path))
        assert root == str(tmp_path.resolve())
        assert str(tmp_path.resolve()) in sys.path
        tools = os.path.join(str(tmp_path.resolve()), "CIME", "Tools")
        assert tools in sys.path

    def test_bootstrap_sets_env(self, tmp_path):
        (tmp_path / "CIME" / "Tools").mkdir(parents=True)
        bootstrap_cime(cimeroot=str(tmp_path))
        assert os.environ["CIMEROOT"] == str(tmp_path.resolve())

    def test_bootstrap_no_env(self, tmp_path):
        (tmp_path / "CIME" / "Tools").mkdir(parents=True)
        os.environ.pop("CIMEROOT", None)
        bootstrap_cime(cimeroot=str(tmp_path), set_env=False)
        assert "CIMEROOT" not in os.environ

    def test_extra_paths(self, tmp_path):
        (tmp_path / "CIME" / "Tools").mkdir(parents=True)
        extra = tmp_path / "extras"
        extra.mkdir()
        bootstrap_cime(cimeroot=str(tmp_path), extra_paths=[str(extra)])
        assert str(extra.resolve()) in sys.path

    def test_no_duplicate_paths(self, tmp_path):
        (tmp_path / "CIME" / "Tools").mkdir(parents=True)
        bootstrap_cime(cimeroot=str(tmp_path))
        bootstrap_cime(cimeroot=str(tmp_path))
        root_str = str(tmp_path.resolve())
        assert sys.path.count(root_str) == 1


class TestPrependSysPath:
    def setup_method(self):
        self._orig_path = sys.path[:]

    def teardown_method(self):
        sys.path[:] = self._orig_path

    def test_inserts_in_order(self, tmp_path):
        a = str(tmp_path / "a")
        b = str(tmp_path / "b")

        # Context
        existing = [p for p in sys.path if p not in (a, b)]

        # Act
        _prepend_sys_path([a, b])

        # Assert
        assert sys.path[0] == a
        assert sys.path[1] == b
        for p in existing:
            assert p in sys.path

    def test_moves_existing_entry(self, tmp_path):
        p = str(tmp_path / "x")

        # Context
        sys.path.append(p)
        existing = [x for x in sys.path if x != p]

        # Act
        _prepend_sys_path([p])

        # Assert
        assert sys.path[0] == p
        assert sys.path.count(p) == 1
        for x in existing:
            assert x in sys.path

    def test_duplicate_in_input_uses_first_occurrence_position(self, tmp_path):
        # sys.path = [A, B, C]; paths = [C, D, C]
        # C appears twice in paths; first-occurrence wins so the effective
        # list is [C, D].  C must land at index 0, D at index 1.
        A = str(tmp_path / "A")
        B = str(tmp_path / "B")
        C = str(tmp_path / "C")
        D = str(tmp_path / "D")

        # Context
        sys.path[:] = [A, B, C]

        # Act
        _prepend_sys_path([C, D, C])

        # Assert
        assert sys.path[0] == C
        assert sys.path[1] == D
        assert sys.path.count(C) == 1
        assert sys.path.count(D) == 1
        assert A in sys.path
        assert B in sys.path

    def test_duplicate_in_input_warns(self, tmp_path):
        # Duplicate paths in the input list should raise a UserWarning so
        # callers are alerted that import precedence may be affected.
        C = str(tmp_path / "C")
        D = str(tmp_path / "D")

        # Context
        sys.path[:] = []

        # Act / Assert
        with pytest.warns(UserWarning, match="Duplicate paths"):
            _prepend_sys_path([C, D, C])


class TestGetToolsPath:
    def test_returns_tools_dir(self, tmp_path):
        (tmp_path / "CIME" / "Tools").mkdir(parents=True)
        tools = get_tools_path(cimeroot=str(tmp_path))
        assert tools == os.path.join(str(tmp_path), "CIME", "Tools")


class TestCheckMinimumPythonVersion:
    def test_passes_current_version(self):
        # Current Python is >= 3.9 (required by CIME)
        check_minimum_python_version(3, 9)

    def test_fails_future_version(self):
        with pytest.raises(RuntimeError, match="required"):
            check_minimum_python_version(99, 0)

    def test_warn_only(self, capsys):
        check_minimum_python_version(99, 0, warn_only=True)
        captured = capsys.readouterr()
        assert "recommended" in captured.err
