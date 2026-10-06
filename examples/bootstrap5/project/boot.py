"""Process boot id for the public demo. Installed by ``settings_demo`` only.

A restart replaces the instance without downtime, so the reset workflow cannot tell the old instance from the new
one by status codes. It compares this header before and after the restart instead.
"""

import uuid

BOOT_ID = uuid.uuid4().hex


class BootIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["X-Demo-Boot"] = BOOT_ID
        return response
