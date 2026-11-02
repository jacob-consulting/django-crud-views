"""Disposable authenticated loopback fixture for presentation acceptance."""

# ruff: noqa: E402 -- validate port before Django configuration and imports.
import os
import re

port_text = os.environ.get("CV_PRESENTATION_PORT", "8145")
if not re.fullmatch(r"[0-9]+", port_text) or not 1024 <= int(port_text) <= 65535:
    raise SystemExit("CV_PRESENTATION_PORT must be decimal 1024..65535; reserved ports: 8143, 8144")
PORT = int(port_text)

from tests.test1.conftest import pytest_configure

pytest_configure()
