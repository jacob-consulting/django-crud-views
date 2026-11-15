"""Cross-subtree optional access observations, imported after Django configuration."""

import os

import pytest


@pytest.fixture(autouse=True)
def record_access_requests():
    if os.environ.get("CV_ACCESS_RECORD_REQUESTS") != "1":
        yield None
        return
    # Root conftest loads before each test project's pytest_configure.
    from crud_views.lib.access_trace import AccessRecorder, recording

    recorder = AccessRecorder()
    with recording(recorder):
        try:
            yield recorder
        finally:
            recorder.clear()
