"""Poll a URL until it answers HTTP 200. CI helper for readme-examples.yml."""

import sys
import time
import urllib.request


def main() -> int:
    url = sys.argv[1]
    timeout = float(sys.argv[2]) if len(sys.argv) > 2 else 60.0
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    print(f"OK {url}")
                    return 0
        except OSError:
            time.sleep(0.5)
    print(f"no HTTP 200 from {url} within {timeout}s", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
