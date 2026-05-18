from __future__ import annotations

import logging
import subprocess

logger = logging.getLogger(__name__)


class GitController:
    def __init__(self, url: str) -> None:
        self._url = url

    def clone(self, dest: str, *, branch: str, depth: int = 1) -> None:
        subprocess.run(
            ["git", "clone", "--branch", branch, "--depth", str(depth), self._url, dest],
            check=True,
        )

    def fetch(self, remote: str, branch: str, *, cwd: str) -> None:
        subprocess.run(["git", "-C", cwd, "fetch", remote, branch], check=True)

    def reset(self, target: str, *, cwd: str, hard: bool = False) -> None:
        args = ["git", "-C", cwd, "reset"]
        if hard:
            args.append("--hard")
        args.append(target)
        subprocess.run(args, check=True)

    def rev_parse(self, ref: str, *, cwd: str) -> str:
        result = subprocess.run(
            ["git", "-C", cwd, "rev-parse", ref],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
