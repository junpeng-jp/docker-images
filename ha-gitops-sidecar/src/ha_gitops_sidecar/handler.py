from __future__ import annotations

import json
import logging

from typing import Any
from collections.abc import Mapping
from http.server import BaseHTTPRequestHandler

from ha_gitops_sidecar.server import GitOpsServerImpl, HttpException


logger = logging.getLogger(__name__)


class GitOpsHandler(BaseHTTPRequestHandler):
    impl: GitOpsServerImpl

    def do_GET(self) -> None:
        try:
            if self.path == "/health":
                self._respond(self.impl.health())
            elif self.path == "/status":
                self._respond(self.impl.status())
            else:
                self._send_json(404, {"error": "not found"})
        except HttpException as exc:
            self._send_json(exc.status_code, exc.body)

    def do_POST(self) -> None:
        try:
            if self.path == "/webhook/sync":
                self._respond(self.impl.sync())
            else:
                self._send_json(404, {"error": "not found"})
        except HttpException as exc:
            self._send_json(exc.status_code, exc.body)

    def _respond(self, result: Any) -> None:
        if result is None:
            self.send_response(204)
            self.end_headers()
        else:
            self._send_json(200, result)

    def _send_json(self, code: int, body: Mapping[str, Any]) -> None:
        payload = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:
        logger.info("http request: %s", format % args)
