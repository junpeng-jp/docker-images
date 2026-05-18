from __future__ import annotations

import http.client
import json
import threading
from http.server import HTTPServer
from unittest.mock import MagicMock

import pytest

from ha_gitops_sidecar.main import GitOpsHandler
from ha_gitops_sidecar.server import HttpException


@pytest.fixture
def mock_impl():
    return MagicMock()


@pytest.fixture
def live_server(mock_impl):
    GitOpsHandler.impl = mock_impl
    srv = HTTPServer(("127.0.0.1", 0), GitOpsHandler)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    yield srv
    srv.shutdown()


def _get(live_server, path):
    host, port = live_server.server_address
    conn = http.client.HTTPConnection(host, port)
    conn.request("GET", path)
    resp = conn.getresponse()
    return resp.status, resp.getheader("Content-Type"), json.loads(resp.read())


def _post(live_server, path):
    host, port = live_server.server_address
    conn = http.client.HTTPConnection(host, port)
    conn.request("POST", path)
    resp = conn.getresponse()
    return resp.status, resp.getheader("Content-Type"), json.loads(resp.read())


def test_health(live_server, mock_impl):
    mock_impl.health.return_value = {"status": "ok"}
    status, ct, body = _get(live_server, "/health")
    assert status == 200
    assert ct == "application/json"
    assert body == {"status": "ok"}


def test_status_after_sync(live_server, mock_impl):
    mock_impl.status.return_value = {
        "repo": "git@github.com:org/repo.git",
        "commit_hash": "abc123",
        "last_updated": "2024-01-01T00:00:00+00:00",
    }
    status, ct, body = _get(live_server, "/status")
    assert status == 200
    assert ct == "application/json"
    assert body == {
        "repo": "git@github.com:org/repo.git",
        "commit_hash": "abc123",
        "last_updated": "2024-01-01T00:00:00+00:00",
    }


def test_status_not_yet_run(live_server, mock_impl):
    mock_impl.status.return_value = {"repo": "git@github.com:org/repo.git", "commit_hash": None, "last_updated": None}
    status, ct, body = _get(live_server, "/status")
    assert status == 200
    assert ct == "application/json"
    assert body == {"repo": "git@github.com:org/repo.git", "commit_hash": None, "last_updated": None}


def test_sync_success(live_server, mock_impl):
    sync_result = {"success": True, "timestamp": "2024-01-01T00:00:00+00:00", "sha": "abc123", "error": None}
    mock_impl.sync.return_value = sync_result
    status, ct, body = _post(live_server, "/webhook/sync")
    assert status == 200
    assert ct == "application/json"
    assert body == sync_result


def test_sync_failure(live_server, mock_impl):
    error_body = {"success": False, "timestamp": "2024-01-01T00:00:00+00:00", "sha": None, "error": "git failed"}
    mock_impl.sync.side_effect = HttpException(500, error_body)
    status, ct, body = _post(live_server, "/webhook/sync")
    assert status == 500
    assert body == error_body


def test_get_unknown_path(live_server):
    status, ct, body = _get(live_server, "/unknown")
    assert status == 404
    assert body == {"error": "not found"}


def test_post_unknown_path(live_server):
    status, ct, body = _post(live_server, "/unknown")
    assert status == 404
    assert body == {"error": "not found"}
