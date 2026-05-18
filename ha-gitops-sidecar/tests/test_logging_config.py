from __future__ import annotations

import logging

import pytest

from ha_gitops_sidecar.main import configure_logging


@pytest.mark.parametrize(
    "level_str, expected",
    [
        ("INFO", logging.INFO),
        ("DEBUG", logging.DEBUG),
    ],
)
def test_configure_logging(level_str, expected):
    configure_logging(level_str)
    assert logging.root.level == expected
