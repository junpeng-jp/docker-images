from __future__ import annotations

import os
import shutil
from typing import Sequence

import yaml


class RepoNotClonedError(Exception):
    """Raised when the repo directory contains no .git directory."""


class RepoCorruptedError(Exception):
    """Raised when the repo directory exists but contains no .git directory."""


def validate_repo(repo_dir: str) -> None:
    git_dir = os.path.join(repo_dir, ".git")
    if os.path.exists(repo_dir) and not os.path.isdir(git_dir):
        raise RepoCorruptedError(f"Directory exists but contains no .git: {repo_dir}")
    if not os.path.isdir(git_dir):
        raise RepoNotClonedError(f"No git repository found at: {repo_dir}")


def validate_yaml_files(src_dir: str) -> None:
    for dirpath, _, filenames in os.walk(src_dir):
        for filename in filenames:
            if not (filename.endswith(".yaml") or filename.endswith(".yml")):
                continue
            filepath = os.path.join(dirpath, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            try:
                yaml.safe_load(content)
            except yaml.YAMLError as exc:
                raise ValueError(f"YAML parse error in {filepath}: {exc}") from exc


class HomeAssistantFS:
    def __init__(self, root: str) -> None:
        self._root = root

    def validate_dirs(self, directories: Sequence[str], *, src_root: str) -> None:
        for dir in directories:
            src_dir = os.path.join(src_root, dir)
            if not os.path.isdir(src_dir):
                continue
            validate_yaml_files(src_dir)

    def copy_dirs(self, directories: Sequence[str], *, src_root: str) -> None:
        for dir in directories:
            src_dir = os.path.join(src_root, dir)
            if not os.path.isdir(src_dir):
                continue
            dst_dir = os.path.join(self._root, dir)
            shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
