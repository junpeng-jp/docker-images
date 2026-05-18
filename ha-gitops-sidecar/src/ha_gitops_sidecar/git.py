from __future__ import annotations

import subprocess


class GitError(Exception):
    def __init__(self, message: str, stderr: str) -> None:
        super().__init__(message)
        self.stderr = stderr


class GitCloneError(GitError): ...


class GitFetchError(GitError): ...


class GitResetError(GitError): ...


class GitRevParseError(GitError): ...


class GitController:
    def __init__(self, url: str) -> None:
        self._url = url

    def clone(self, dest: str, *, branch: str, depth: int = 1) -> None:
        try:
            subprocess.run(
                ["git", "clone", "--branch", branch, "--depth", str(depth), self._url, dest],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            raise GitCloneError(str(e), e.stderr or "") from e

    def fetch(self, remote: str, branch: str, *, cwd: str) -> None:
        try:
            subprocess.run(
                ["git", "-C", cwd, "fetch", remote, branch],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            raise GitFetchError(str(e), e.stderr or "") from e

    def reset(self, target: str, *, cwd: str, hard: bool = False) -> None:
        args = ["git", "-C", cwd, "reset"]
        if hard:
            args.append("--hard")
        args.append(target)
        try:
            subprocess.run(args, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise GitResetError(str(e), e.stderr or "") from e

    def rev_parse(self, ref: str, *, cwd: str) -> str:
        try:
            result = subprocess.run(
                ["git", "-C", cwd, "rev-parse", ref],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            raise GitRevParseError(str(e), e.stderr or "") from e

        return result.stdout.strip()
