from __future__ import annotations

import subprocess

import pytest

from ha_gitops_sidecar.filesystem import RepoCorruptedError, RepoNotClonedError
from ha_gitops_sidecar.server import HttpException

_REPO_DIR = "/work/repo"


def test_health(make_impl):
    assert make_impl().health() == {"status": "ok"}


@pytest.mark.parametrize(
    "exc_cls, expect_rmtree",
    [
        (RepoNotClonedError, False),
        (RepoCorruptedError, True),
    ],
)
def test_sync_repo_init(make_impl, mock_git_run, frozen_dt, mocker, exc_cls, expect_rmtree):
    mocker.patch("ha_gitops_sidecar.server.validate_repo", side_effect=exc_cls)
    mock_rmtree = mocker.patch("ha_gitops_sidecar.server.shutil.rmtree")

    result = make_impl().sync()

    assert result["success"] is True
    if expect_rmtree:
        mock_rmtree.assert_called_once_with(_REPO_DIR)
    else:
        mock_rmtree.assert_not_called()
    mock_git_run.assert_any_call(
        ["git", "clone", "--branch", "main", "--depth", "1", "git@github.com:example/repo.git", _REPO_DIR],
        check=True,
    )


def test_sync_repo_existing(make_impl, mock_git_run, frozen_dt, mocker):
    mocker.patch("ha_gitops_sidecar.server.validate_repo")

    result = make_impl().sync()

    assert result["success"] is True
    mock_git_run.assert_any_call(
        ["git", "-C", _REPO_DIR, "fetch", "origin", "main"],
        check=True,
    )
    mock_git_run.assert_any_call(
        ["git", "-C", _REPO_DIR, "reset", "--hard", "origin/main"],
        check=True,
    )


def test_sync_success(make_impl, mock_git_run, frozen_dt, mocker):
    impl = make_impl(managed_dirs=("automations",))
    mock_validate = mocker.patch.object(impl._ha_fs, "validate_dirs")
    mock_copy = mocker.patch.object(impl._ha_fs, "copy_dirs")

    result = impl.sync()

    assert result == {
        "success": True,
        "timestamp": "2024-01-01T00:00:00+00:00",
        "sha": "abc123",
        "error": None,
    }
    assert result is impl._last_result
    mock_validate.assert_called_once_with(("automations",), src_root=_REPO_DIR)
    mock_copy.assert_called_once_with(("automations",), src_root=_REPO_DIR)


def test_sync_subprocess_raises(make_impl, frozen_dt, mocker):
    mocker.patch("ha_gitops_sidecar.git.subprocess.run", side_effect=subprocess.CalledProcessError(1, "git clone"))

    with pytest.raises(HttpException) as exc_info:
        make_impl().sync()

    assert exc_info.value.status_code == 422
    assert exc_info.value.body["success"] is False
    assert exc_info.value.body["sha"] is None
    assert exc_info.value.body["error"] is not None


def test_sync_validation_failure_aborts_copy(make_impl, mock_git_run, frozen_dt, mocker):
    impl = make_impl(managed_dirs=("automations",))
    mocker.patch.object(impl._ha_fs, "validate_dirs", side_effect=ValueError("YAML parse error in bad.yaml"))
    mock_copy = mocker.patch.object(impl._ha_fs, "copy_dirs")

    with pytest.raises(HttpException) as exc_info:
        impl.sync()

    assert exc_info.value.status_code == 422
    assert exc_info.value.body["success"] is False
    assert "YAML parse error" in exc_info.value.body["error"]
    mock_copy.assert_not_called()


def test_status_no_run(make_impl):
    with pytest.raises(HttpException) as exc_info:
        make_impl().status()

    assert exc_info.value.status_code == 503
    assert exc_info.value.body == {"has_run": False, "last": None}


def test_status_after_success(make_impl, mock_git_run, frozen_dt):
    impl = make_impl()
    impl.sync()
    result = impl.status()

    assert result["has_run"] is True
    assert result["last"]["success"] is True


def test_status_after_failure(make_impl, frozen_dt, mocker):
    mocker.patch("ha_gitops_sidecar.git.subprocess.run", side_effect=subprocess.CalledProcessError(1, "git clone"))

    impl = make_impl()
    with pytest.raises(HttpException):
        impl.sync()

    with pytest.raises(HttpException) as exc_info:
        impl.status()

    assert exc_info.value.status_code == 503
    assert exc_info.value.body["has_run"] is True
    assert exc_info.value.body["last"]["success"] is False
