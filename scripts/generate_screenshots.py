"""Regenerate tutorial screenshots from the live example app.

Usage (from the repo root):

    cd examples/bootstrap5
    env -u VIRTUAL_ENV uv run --with playwright playwright install chromium   # once
    env -u VIRTUAL_ENV uv run --with playwright python ../../scripts/generate_screenshots.py

Boots the seeded dev server on a scratch port, logs in as the demo user
``alice`` and captures the tutorial pages into docs/getting_started/assets/.
Re-run whenever the UI changes; commit the PNGs like normal files.
"""

import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

PORT = 8123
BASE = f"http://127.0.0.1:{PORT}"
EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "examples" / "bootstrap5"
ASSETS_DIR = Path(__file__).resolve().parents[1] / "docs" / "getting_started" / "assets"

#: (output name, path) -- pages reachable by direct URL
STATIC_PAGES = [
    ("tutorial-home", "/"),
    ("tutorial-author-list", "/library/author/"),
    ("tutorial-author-create", "/library/author/create/"),
    ("tutorial-book-list", "/library/book/"),
]


def wait_for_server(timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"{BASE}/login/", timeout=1)
            return
        except OSError:
            time.sleep(0.3)
    raise RuntimeError(f"server on {BASE} did not come up")


def main() -> None:
    subprocess.run(["uv", "run", "manage.py", "migrate"], cwd=EXAMPLES_DIR, check=True)
    subprocess.run(["uv", "run", "manage.py", "seed"], cwd=EXAMPLES_DIR, check=True)
    server = subprocess.Popen(
        ["uv", "run", "manage.py", "runserver", f"127.0.0.1:{PORT}", "--noreload"],
        cwd=EXAMPLES_DIR,
    )
    try:
        wait_for_server()
        ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 800})

            page.goto(f"{BASE}/login/")
            page.fill("input[name=username]", "alice")
            page.fill("input[name=password]", "alice")
            page.click("input[type=submit], button[type=submit]")
            page.wait_for_load_state("networkidle")

            for name, path in STATIC_PAGES:
                page.goto(f"{BASE}{path}")
                page.wait_for_load_state("networkidle")
                page.screenshot(path=ASSETS_DIR / f"{name}.png")
                print(f"captured {name}.png  ({path})")

            # object pages: derive the first author's detail URL from the list table
            page.goto(f"{BASE}/library/author/")
            detail_href = page.locator("table tbody a").first.get_attribute("href")
            if not detail_href:
                raise RuntimeError("no detail link found on the author list page")
            for name, path in [
                ("tutorial-author-detail", detail_href),
                ("tutorial-author-update", detail_href.replace("/detail/", "/update/")),
                ("tutorial-author-delete", detail_href.replace("/detail/", "/delete/")),
            ]:
                page.goto(f"{BASE}{path}")
                page.wait_for_load_state("networkidle")
                page.screenshot(path=ASSETS_DIR / f"{name}.png")
                print(f"captured {name}.png  ({path})")

            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=10)


if __name__ == "__main__":
    sys.exit(main())
