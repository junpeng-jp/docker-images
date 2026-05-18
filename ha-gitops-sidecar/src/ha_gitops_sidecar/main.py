from __future__ import annotations

import json
import logging
import os
import signal
import sys
import threading

from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from collections.abc import Mapping

from ha_gitops_sidecar.config import ConfigError, ServerConfig, load_config
from ha_gitops_sidecar.server import GitOpsServerImpl, HttpException

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


class GitOpsHandler(BaseHTTPRequestHandler):
    impl: GitOpsServerImpl

    def do_GET(self) -> None:
        try:
            if self.path == "/health":
                self._send_json(200, {"status": "ok"})
            elif self.path == "/status":
                self._send_json(200, self.impl.status())
            else:
                self._send_json(404, {"error": "not found"})
        except HttpException as exc:
            self._send_json(exc.status_code, exc.body)

    def do_POST(self) -> None:
        try:
            if self.path == "/webhook/sync":
                self._send_json(200, self.impl.sync())
            else:
                self._send_json(404, {"error": "not found"})
        except HttpException as exc:
            self._send_json(exc.status_code, exc.body)

    def _send_json(self, code: int, body: Mapping[str, Any]) -> None:
        payload = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:
        logger.info("http request: %s", format % args)


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
