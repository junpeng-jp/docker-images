from __future__ import annotations

import logging
import os
import shutil
import threading
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Sequence, cast

if TYPE_CHECKING:
    from ha_gitops_sidecar.config import ServerConfig, StatusResult, SyncResult

from ha_gitops_sidecar.filesystem import HomeAssistantFS, RepoCorruptedError, RepoNotClonedError, validate_repo
from ha_gitops_sidecar.git import GitController, GitError

logger = logging.getLogger(__name__)


class HttpException(Exception):
    def __init__(self, status_code: int, body: dict[str, Any]) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(str(body))


class GitOpsServerImpl:
    def __init__(
        self,
        config: ServerConfig,
        lock: threading.Lock,
    ) -> None:
        self._config = config
        self._lock = lock
        self._last_result: SyncResult | None = None
        self._git = GitController(config["app"]["repo_url"])
        self._ha_fs = HomeAssistantFS(config["deployment"]["config_root"])

    @property
    def branch(self) -> str:
        return self._config["app"]["repo_branch"]

    @property
    def managed_dirs(self) -> Sequence[str]:
        return self._config["deployment"]["managed_dirs"]

    @property
    def work_dir(self) -> str:
        return self._config["deployment"]["work_dir"]

    @property
    def git_remote(self) -> str:
        return self._config["deployment"]["git_remote"]

    @property
    def repo_subdir(self) -> str:
        return self._config["deployment"]["repo_subdir"]

    def health(self) -> dict:
        return {"status": "ok"}

    def sync(self) -> SyncResult:
        current_time = datetime.now(timezone.utc)
        with self._lock:
            try:
                repo_dir = os.path.join(self.work_dir, self.repo_subdir)
                try:
                    validate_repo(repo_dir)
                except RepoCorruptedError:
                    shutil.rmtree(repo_dir)
                    self._git.clone(repo_dir, branch=self.branch)
                except RepoNotClonedError:
                    self._git.clone(repo_dir, branch=self.branch)
                else:
                    self._git.fetch(self.git_remote, self.branch, cwd=repo_dir)
                    self._git.reset(f"{self.git_remote}/{self.branch}", cwd=repo_dir, hard=True)

                self._ha_fs.validate_dirs(self.managed_dirs, src_root=repo_dir)
                self._ha_fs.copy_dirs(self.managed_dirs, src_root=repo_dir)
                sha = self._git.rev_parse("HEAD", cwd=repo_dir)

                result: SyncResult = {
                    "success": True,
                    "timestamp": current_time.isoformat(),
                    "sha": sha,
                    "error": None,
                }
            except Exception as exc:
                if isinstance(exc, GitError) and exc.stderr:
                    logger.error("sync failed: %s | stderr: %s", exc, exc.stderr)
                else:
                    logger.error("sync failed: %s", exc)

                result = {
                    "success": False,
                    "timestamp": current_time.isoformat(),
                    "sha": None,
                    "error": str(exc),
                }

            self._last_result = result
            if not result["success"]:
                raise HttpException(500, cast(dict, result))

            return result

    def status(self) -> StatusResult:
        last = self._last_result
        return {
            "repo": self._config["app"]["repo_url"],
            "commit_hash": last["sha"] if last is not None else None,
            "last_updated": last["timestamp"] if last is not None else None,
        }
