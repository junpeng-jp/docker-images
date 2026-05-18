from __future__ import annotations

import json
import logging
import os
import signal
import sys
import threading

from http.server import HTTPServer

from ha_gitops_sidecar.config import ConfigError, ServerConfig, load_config
from ha_gitops_sidecar.server import GitOpsServerImpl
from ha_gitops_sidecar.handler import GitOpsHandler


logger = logging.getLogger(__name__)


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(
            {
                "level": record.levelname,
                "logger": record.name,
                "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
                "message": record.getMessage(),
            }
        )


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(_JsonFormatter())
    logging.root.handlers = [handler]
    logging.root.setLevel(level)


def main() -> None:
    configure_logging("INFO")

    try:
        config: ServerConfig = load_config()
    except ConfigError as exc:
        logger.error("configuration error: %s", exc)
        sys.exit(1)

    logging.root.setLevel(config["app"]["log_level"])

    os.environ["GIT_SSH_COMMAND"] = config["deployment"]["git_ssh_command"]

    lock = threading.Lock()
    impl = GitOpsServerImpl(config=config, lock=lock)
    GitOpsHandler.impl = impl

    server = HTTPServer((config["deployment"]["bind_host"], config["deployment"]["port"]), GitOpsHandler)

    def _shutdown(*_) -> None:
        thread = threading.Thread(target=server.shutdown, daemon=True)
        thread.start()

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    logger.info("GitOps sidecar listening on %s:%s", config["deployment"]["bind_host"], config["deployment"]["port"])
    server.serve_forever()


if __name__ == "__main__":
    main()
