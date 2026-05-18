from __future__ import annotations

import subprocess
import threading

import pytest

from ha_gitops_sidecar.filesystem import HomeAssistantFS
from ha_gitops_sidecar.git import GitController
from ha_gitops_sidecar.server import GitOpsServerImpl

_URL = "git@github.com:example/repo.git"
_CONFIG_ROOT = "/config"


@pytest.fixture
def mock_git_run(mocker):
    def _side_effect(cmd, **kwargs):
        stdout = "abc123\n" if "rev-parse" in cmd else ""
        return subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr="")

    return mocker.patch("ha_gitops_sidecar.git.subprocess.run", side_effect=_side_effect)


@pytest.fixture
def frozen_dt(mocker):
    mock = mocker.patch("ha_gitops_sidecar.server.datetime")
    mock.now.return_value.isoformat.return_value = "2024-01-01T00:00:00+00:00"
    return mock


@pytest.fixture
def git_controller():
    return GitController(_URL)


@pytest.fixture
def ha_fs():
    return HomeAssistantFS(_CONFIG_ROOT)


@pytest.fixture
def make_impl():
    def _factory(managed_dirs=None):
        from ha_gitops_sidecar.config import ServerConfig

        config: ServerConfig = {
            "app": {
                "repo_url": _URL,
                "repo_branch": "main",
                "log_level": "INFO",
            },
            "deployment": {
                "work_dir": "/work",
                "managed_dirs": managed_dirs or (),
                "config_root": _CONFIG_ROOT,
                "port": 8080,
                "bind_host": "127.0.0.1",
                "ssh_key_path": "/run/secrets/ssh/id_rsa",
                "known_hosts_path": "/run/known-hosts/known_hosts",
                "git_ssh_command": "ssh -i /run/secrets/ssh/id_rsa",
                "git_remote": "origin",
                "repo_subdir": "repo",
            },
        }
        return GitOpsServerImpl(config=config, lock=threading.Lock())

    return _factory
