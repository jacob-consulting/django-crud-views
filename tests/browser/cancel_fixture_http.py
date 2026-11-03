"""Single-threaded HTTP fixture transport, separate from Django/settings setup."""

from wsgiref.simple_server import WSGIServer


class FixtureServer(WSGIServer):
    """Bound idle speculative sockets while application requests remain serialized."""

    request_timeout = 1

    def get_request(self):
        client, address = super().get_request()
        client.settimeout(self.request_timeout)
        return client, address
