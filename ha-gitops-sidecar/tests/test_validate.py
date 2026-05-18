from __future__ import annotations

from unittest.mock import mock_open, patch

import pytest

from ha_gitops_sidecar.filesystem import RepoCorruptedError, RepoNotClonedError, validate_repo, validate_yaml_files

_REPO_DIR = "/work/repo"


@pytest.mark.parametrize(
    "exists, isdir, expected_exc",
    [
        (False, False, RepoNotClonedError),
        (True, False, RepoCorruptedError),
        (True, True, None),
    ],
)
def test_validate_repo(exists, isdir, expected_exc):
    with (
        patch("ha_gitops_sidecar.filesystem.os.path.exists", return_value=exists),
        patch("ha_gitops_sidecar.filesystem.os.path.isdir", return_value=isdir),
    ):
        if expected_exc is None:
            validate_repo(_REPO_DIR)  # must not raise
        else:
            with pytest.raises(expected_exc):
                validate_repo(_REPO_DIR)


@pytest.mark.parametrize(
    "yaml_content, raises",
    [
        ("key: value", False),
        ("[", True),
    ],
)
def test_validate_yaml_files(yaml_content, raises):
    filename = "bad.yaml" if raises else "lights.yaml"
    with (
        patch("ha_gitops_sidecar.filesystem.os.walk", return_value=[(_REPO_DIR, [], [filename])]),
        patch("builtins.open", mock_open(read_data=yaml_content)),
    ):
        if raises:
            with pytest.raises(ValueError, match="YAML parse error"):
                validate_yaml_files(_REPO_DIR)
        else:
            validate_yaml_files(_REPO_DIR)  # must not raise


def test_validate_yaml_yml_extension():
    with (
        patch("ha_gitops_sidecar.filesystem.os.walk", return_value=[(_REPO_DIR, [], ["config.yml"])]),
        patch("builtins.open", mock_open(read_data="key: value")) as mock_file,
    ):
        validate_yaml_files(_REPO_DIR)
        mock_file.assert_called_once()


def test_validate_yaml_non_yaml_skipped():
    with (
        patch("ha_gitops_sidecar.filesystem.os.walk", return_value=[(_REPO_DIR, [], ["readme.txt", "notes.md"])]),
        patch("builtins.open", mock_open()) as mock_file,
    ):
        validate_yaml_files(_REPO_DIR)
        mock_file.assert_not_called()
