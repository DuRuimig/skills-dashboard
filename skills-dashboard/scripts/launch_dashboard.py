#!/usr/bin/env python3
"""Launch the bundled Skills Dashboard local web app."""

import argparse
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
DASHBOARD_APP = SKILL_DIR / "assets" / "dashboard" / "app.py"


def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def healthcheck(port):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=1) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError):
        return False


def wait_until_ready(port, timeout=10):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if healthcheck(port):
            return True
        time.sleep(0.2)
    return False


def open_browser(url, browser):
    if browser == "none":
        return
    if sys.platform == "darwin":
        if browser == "chrome":
            subprocess.run(["open", "-a", "Google Chrome", url], check=False)
        else:
            subprocess.run(["open", url], check=False)
        return
    if sys.platform.startswith("win"):
        os.startfile(url)  # type: ignore[attr-defined]
        return
    subprocess.run(["xdg-open", url], check=False)


def main():
    parser = argparse.ArgumentParser(description="Start the Skills Dashboard local server.")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8787")))
    parser.add_argument("--browser", choices=["default", "chrome", "none"], default="default")
    parser.add_argument("--extra-root", action="append", default=[], help="Additional skill root to scan. Can be repeated.")
    args = parser.parse_args()

    if not DASHBOARD_APP.exists():
        raise SystemExit(f"Dashboard app not found: {DASHBOARD_APP}")

    env = os.environ.copy()
    env["PORT"] = str(args.port)
    env.setdefault("SKILLS_DASHBOARD_WORKSPACE", os.getcwd())
    if args.extra_root:
        existing = env.get("SKILLS_DASHBOARD_EXTRA_ROOTS", "")
        roots = [root for root in existing.split(os.pathsep) if root] + args.extra_root
        env["SKILLS_DASHBOARD_EXTRA_ROOTS"] = os.pathsep.join(roots)

    if is_port_open(args.port):
        if not healthcheck(args.port):
            raise SystemExit(f"Port {args.port} is already in use by another process.")
    else:
        subprocess.Popen(
            [sys.executable, str(DASHBOARD_APP)],
            cwd=str(DASHBOARD_APP.parent),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        if not wait_until_ready(args.port):
            raise SystemExit(f"Skills Dashboard did not become ready on port {args.port}.")

    url = f"http://127.0.0.1:{args.port}/"
    open_browser(url, args.browser)
    print(url)


if __name__ == "__main__":
    main()
