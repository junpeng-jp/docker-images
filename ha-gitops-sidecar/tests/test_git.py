from __future__ import annotations

import subprocess

import pytest

from ha_gitops_sidecar.git import GitCloneError, GitFetchError, GitResetError, GitRevParseError

_URL = "git@github.com:example/repo.git"
_REPO_DIR = "/work/repo"


def _completed(cmd, stdout=""):
    return subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr="")


@pytest.mark.parametrize(
    "depth, depth_str",
    [
        (1, "1"),
        (5, "5"),
    ],
)
def test_clone(git_controller, mocker, depth, depth_str):
    mock_run = mocker.patch("ha_gitops_sidecar.git.subprocess.run", return_value=_completed(["git", "clone"]))
    git_controller.clone(_REPO_DIR, branch="main", depth=depth)
    mock_run.assert_called_once_with(
        ["git", "clone", "--branch", "main", "--depth", depth_str, _URL, _REPO_DIR],
        check=True,
        capture_output=True,
        text=True,
    )


def test_fetch(git_controller, mocker):
    mock_run = mocker.patch("ha_gitops_sidecar.git.subprocess.run", return_value=_completed(["git", "fetch"]))
    git_controller.fetch("origin", "main", cwd=_REPO_DIR)
    mock_run.assert_called_once_with(
        ["git", "-C", _REPO_DIR, "fetch", "origin", "main"],
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize(
    "hard, expected_args",
    [
        (False, ["git", "-C", _REPO_DIR, "reset", "origin/main"]),
        (True, ["git", "-C", _REPO_DIR, "reset", "--hard", "origin/main"]),
    ],
)
def test_reset(git_controller, mocker, hard, expected_args):
    mock_run = mocker.patch("ha_gitops_sidecar.git.subprocess.run", return_value=_completed(["git", "reset"]))
    git_controller.reset("origin/main", cwd=_REPO_DIR, hard=hard)
    mock_run.assert_called_once_with(expected_args, check=True, capture_output=True, text=True)


def test_rev_parse(git_controller, mocker):
    mock_run = mocker.patch(
        "ha_gitops_sidecar.git.subprocess.run",
        return_value=_completed(["git", "rev-parse"], stdout="abc123\n"),
    )
    sha = git_controller.rev_parse("HEAD", cwd=_REPO_DIR)
    assert sha == "abc123"
    mock_run.assert_called_once_with(
        ["git", "-C", _REPO_DIR, "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )


def test_clone_error(git_controller, mocker):
    mocker.patch(
        "ha_gitops_sidecar.git.subprocess.run",
        side_effect=subprocess.CalledProcessError(128, "git clone", stderr="fatal: repo not found\n"),
    )
    with pytest.raises(GitCloneError) as exc_info:
        git_controller.clone(_REPO_DIR, branch="main")
    assert exc_info.value.stderr == "fatal: repo not found\n"


def test_fetch_error(git_controller, mocker):
    mocker.patch(
        "ha_gitops_sidecar.git.subprocess.run",
        side_effect=subprocess.CalledProcessError(1, "git fetch", stderr="error: could not fetch origin\n"),
    )
    with pytest.raises(GitFetchError) as exc_info:
        git_controller.fetch("origin", "main", cwd=_REPO_DIR)
    assert exc_info.value.stderr == "error: could not fetch origin\n"


def test_reset_error(git_controller, mocker):
    mocker.patch(
        "ha_gitops_sidecar.git.subprocess.run",
        side_effect=subprocess.CalledProcessError(1, "git reset", stderr="fatal: bad object origin/main\n"),
    )
    with pytest.raises(GitResetError) as exc_info:
        git_controller.reset("origin/main", cwd=_REPO_DIR, hard=True)
    assert exc_info.value.stderr == "fatal: bad object origin/main\n"


def test_rev_parse_error(git_controller, mocker):
    mocker.patch(
        "ha_gitops_sidecar.git.subprocess.run",
        side_effect=subprocess.CalledProcessError(128, "git rev-parse", stderr="fatal: not a git repository\n"),
    )
    with pytest.raises(GitRevParseError) as exc_info:
        git_controller.rev_parse("HEAD", cwd=_REPO_DIR)
    assert exc_info.value.stderr == "fatal: not a git repository\n"
