"""Own the isolated server until stdin closes; always clean up on exit/signals.

The native browser tool runs between READY and the caller closing stdin. No
developer database, pre-existing settings module or existing listener is touched.
"""

import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path


def main():
    root = Path.cwd()
    assert root == Path("/home/alex/projects/alex/django-crud-views")
    phase = Path(__file__).parent
    port = int(os.environ.get("CV_NAVBAR_BROWSER_PORT", "9000"))
    settings = root / ".pytest_cache/navbar_browser_settings.py"
    report = {"run": sys.argv[1], "settings": str(settings), "pid": None, "port": port}
    owned_settings = False
    directory = None
    server = None

    def interrupted(signum, frame):
        raise KeyboardInterrupt(f"signal {signum}")

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        with socket.socket() as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            probe.bind(("127.0.0.1", port))
        directory = Path(tempfile.mkdtemp(prefix="cv08-browser-"))
        report["directory"] = str(directory)
        with settings.open("x") as stream:
            owned_settings = True
            stream.write(
                "from project.settings import *\n"
                "DATABASES = {**DATABASES, 'default': {**DATABASES['default'], "
                f"'NAME': {str(directory / 'db.sqlite3')!r}}}}}\n"
            )
        env = {**os.environ, "PYTHONPATH": "../../src:.:../../.pytest_cache", "PYTHONDONTWRITEBYTECODE": "1"}
        command = ["../../.nox/examples-3-12-django-5-2/bin/python", "manage.py"]
        cwd = root / "examples/bootstrap5"
        for args in (
            ["migrate", "--noinput"],
            ["shell", "-c", "from navbar_demo.seed import seed; seed()"],
        ):
            subprocess.run(command + args + ["--settings=navbar_browser_settings"], cwd=cwd, env=env, check=True)
        with (phase / f"08-browser-{sys.argv[1]}.log").open("w") as log:
            server = subprocess.Popen(
                [*command, "runserver", f"127.0.0.1:{port}", "--noreload", "--settings=navbar_browser_settings"],
                cwd=cwd,
                env=env,
                stdout=log,
                stderr=log,
                start_new_session=True,
            )
            report["pid"] = server.pid
            for _ in range(100):
                if server.poll() is not None:
                    raise RuntimeError(f"server exited {server.returncode}")
                try:
                    urllib.request.urlopen(f"http://127.0.0.1:{port}/login/", timeout=1).close()
                    break
                except OSError:
                    time.sleep(0.1)
            else:
                raise RuntimeError("server readiness timed out")
            print("READY " + json.dumps(report), flush=True)
            sys.stdin.readline()
    except BaseException as error:
        report["interruption_or_error"] = repr(error)
        if not isinstance(error, KeyboardInterrupt):
            raise
    finally:
        if server is not None:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=10)
            report["server_exit"] = server.returncode
        if owned_settings:
            settings.unlink()
        if directory is not None:
            shutil.rmtree(directory)
        with socket.socket() as probe:
            report["port_released"] = probe.connect_ex(("127.0.0.1", port)) != 0
        report["settings_removed"] = not settings.exists()
        report["database_removed"] = directory is None or not directory.exists()
        report["bytecode_absent"] = not list((settings.parent / "__pycache__").glob("navbar_browser_settings.*"))
        (phase / f"08-browser-{sys.argv[1]}-cleanup.json").write_text(json.dumps(report, indent=2) + "\n")
        print("CLEANUP " + json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
