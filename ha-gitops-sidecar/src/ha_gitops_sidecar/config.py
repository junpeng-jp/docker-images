from __future__ import annotations

from typing import TypedDict

import yaml


_MANAGED_DIRS = ("automations", "scripts", "scenes", "blueprints")
_KNOWN_HOSTS_PATH = "/run/known-hosts/known_hosts"
_SSH_KEY_DIR = "/run/secrets/ssh"
_APP_CONFIG_PATH = "/etc/gitops-sidecar/gitops.yaml"
_BIND_HOST = "127.0.0.1"
_GIT_REMOTE = "origin"
_REPO_SUBDIR = "repo"

_REQUIRED_KEYS = ("repo_url", "repo_branch", "work_dir", "port", "ssh_key_filename", "config_root")


class AppConfig(TypedDict):
    repo_url: str
    repo_branch: str
    log_level: str


class DeploymentConfig(TypedDict):
    work_dir: str
    port: int
    bind_host: str
    ssh_key_path: str
    known_hosts_path: str
    git_ssh_command: str
    git_remote: str
    repo_subdir: str
    managed_dirs: tuple[str, ...]
    config_root: str


class ServerConfig(TypedDict):
    app: AppConfig
    deployment: DeploymentConfig


class SyncResult(TypedDict):
    success: bool
    timestamp: str
    sha: str | None
    error: str | None


class StatusResult(TypedDict):
    has_run: bool
    last: SyncResult | None


class ConfigError(ValueError):
    pass


def load_config(config_path: str = _APP_CONFIG_PATH) -> ServerConfig:
    try:
        with open(config_path) as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        raise ConfigError(f"Config file not found: {config_path}")
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in config file {config_path!r}: {exc}")

    if not isinstance(data, dict):
        raise ConfigError(f"Config file must be a YAML mapping, got: {type(data).__name__}")

    missing = [k for k in _REQUIRED_KEYS if not data.get(k)]
    if missing:
        raise ConfigError(f"Missing required keys in config file: {', '.join(missing)}")

    try:
        port = int(data["port"])
    except (ValueError, TypeError):
        raise ConfigError(f"'port' must be an integer, got: {data['port']!r}")

    ssh_key_path = f"{_SSH_KEY_DIR}/{data['ssh_key_filename']}"
    git_ssh_command = (
        f"ssh -i {ssh_key_path} -o UserKnownHostsFile={_KNOWN_HOSTS_PATH} -o StrictHostKeyChecking=yes -o BatchMode=yes"
    )

    return {
        "app": {
            "repo_url": data["repo_url"],
            "repo_branch": data["repo_branch"],
            "log_level": data.get("log_level", "INFO"),
        },
        "deployment": {
            "work_dir": data["work_dir"],
            "port": port,
            "bind_host": data.get("bind_host", _BIND_HOST),
            "ssh_key_path": ssh_key_path,
            "known_hosts_path": _KNOWN_HOSTS_PATH,
            "git_ssh_command": git_ssh_command,
            "git_remote": _GIT_REMOTE,
            "repo_subdir": _REPO_SUBDIR,
            "managed_dirs": _MANAGED_DIRS,
            "config_root": data["config_root"],
        },
    }
