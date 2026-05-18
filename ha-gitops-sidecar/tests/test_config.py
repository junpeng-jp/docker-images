from __future__ import annotations

import pytest

from ha_gitops_sidecar.config import ConfigError, load_config

_VALID_YAML = (
    "repo_url: git@github.com:owner/repo.git\n"
    "repo_branch: main\n"
    "work_dir: /work\n"
    "port: 8080\n"
    "ssh_key_filename: id_rsa\n"
    "config_root: /config\n"
)


def test_load_config_valid(tmp_path):
    config_file = tmp_path / "gitops.yaml"
    config_file.write_text(_VALID_YAML)
    config = load_config(str(config_file))

    assert config["app"]["repo_url"] == "git@github.com:owner/repo.git"
    assert config["app"]["repo_branch"] == "main"
    assert config["app"]["log_level"] == "INFO"
    assert config["deployment"]["work_dir"] == "/work"
    assert config["deployment"]["port"] == 8080
    assert config["deployment"]["ssh_key_path"] == "/run/secrets/ssh/id_rsa"
    assert config["deployment"]["known_hosts_path"] == "/run/known-hosts/known_hosts"
    assert config["deployment"]["managed_dirs"] == ("automations", "scripts", "scenes", "blueprints")
    assert config["deployment"]["config_root"] == "/config"


def test_load_config_log_level_custom(tmp_path):
    config_file = tmp_path / "gitops.yaml"
    config_file.write_text(_VALID_YAML + "log_level: DEBUG\n")
    assert load_config(str(config_file))["app"]["log_level"] == "DEBUG"


def test_load_config_missing_file(tmp_path):
    missing = str(tmp_path / "nonexistent.yaml")
    with pytest.raises(ConfigError, match=missing):
        load_config(missing)


@pytest.mark.parametrize(
    "content, match",
    [
        ("repo_url: [\nbad yaml", "Invalid YAML"),
        (
            "repo_url: git@github.com:owner/repo.git\nrepo_branch: main\n"
            "work_dir: /work\nport: 8080\nconfig_root: /config\n",
            "ssh_key_filename",
        ),
        (_VALID_YAML.replace("port: 8080", "port: abc"), "port"),
    ],
)
def test_load_config_error(tmp_path, content, match):
    config_file = tmp_path / "gitops.yaml"
    config_file.write_text(content)
    with pytest.raises(ConfigError, match=match):
        load_config(str(config_file))
