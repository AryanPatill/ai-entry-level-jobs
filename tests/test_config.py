from pathlib import Path

import pytest

from src.utils.config import REPO_ROOT, get_secret, load_settings


def test_repo_root_is_correct():
    assert (REPO_ROOT / "docs" / "preregistration.md").exists()


def test_paths_are_absolute_and_inside_repo():
    for name, path in load_settings()["paths"].items():
        assert isinstance(path, Path) and path.is_absolute(), name
        assert REPO_ROOT in path.parents, name


def test_missing_secret_raises():
    with pytest.raises(RuntimeError):
        get_secret("THIS_KEY_DOES_NOT_EXIST_123")