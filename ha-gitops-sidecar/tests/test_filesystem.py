from __future__ import annotations

from unittest.mock import mock_open, patch

import pytest

_REPO_DIR = "/work/repo"
_CONFIG_ROOT = "/config"


@pytest.mark.parametrize(
    "method, absent_mock",
    [
        ("validate_dirs", "ha_gitops_sidecar.filesystem.os.walk"),
        ("copy_dirs", "ha_gitops_sidecar.filesystem.shutil.copytree"),
    ],
)
def test_dirs_absent(ha_fs, method, absent_mock):
    """When the src dir does not exist, the downstream operation is not called."""
    with patch("ha_gitops_sidecar.filesystem.os.path.isdir", return_value=False), patch(absent_mock) as mock_op:
        getattr(ha_fs, method)(["automations"], src_root=_REPO_DIR)
        mock_op.assert_not_called()


def test_validate_dirs_valid_yaml(ha_fs):
    src_dir = f"{_REPO_DIR}/automations"
    with (
        patch("ha_gitops_sidecar.filesystem.os.path.isdir", side_effect=lambda p: p == src_dir),
        patch("ha_gitops_sidecar.filesystem.os.walk", return_value=[(src_dir, [], ["lights.yaml"])]),
        patch("builtins.open", mock_open(read_data="key: value")),
    ):
        ha_fs.validate_dirs(["automations"], src_root=_REPO_DIR)  # must not raise


def test_validate_dirs_invalid_yaml(ha_fs):
    src_dir = f"{_REPO_DIR}/automations"
    with (
        patch("ha_gitops_sidecar.filesystem.os.path.isdir", side_effect=lambda p: p == src_dir),
        patch("ha_gitops_sidecar.filesystem.os.walk", return_value=[(src_dir, [], ["bad.yaml"])]),
        patch("builtins.open", mock_open(read_data="[")),
    ):
        with pytest.raises(ValueError, match="YAML parse error"):
            ha_fs.validate_dirs(["automations"], src_root=_REPO_DIR)


def test_copy_dirs_present(ha_fs):
    src_dir = f"{_REPO_DIR}/automations"
    dst_dir = f"{_CONFIG_ROOT}/automations"
    with (
        patch("ha_gitops_sidecar.filesystem.os.path.isdir", side_effect=lambda p: p == src_dir),
        patch("ha_gitops_sidecar.filesystem.shutil.copytree") as mock_copytree,
    ):
        ha_fs.copy_dirs(["automations"], src_root=_REPO_DIR)
        mock_copytree.assert_called_once_with(src_dir, dst_dir, dirs_exist_ok=True)
