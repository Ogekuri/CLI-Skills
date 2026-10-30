"""CLI management commands and release notification orchestration."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from . import __version__

ENDPOINT = "https://api.github.com/repos/Ogekuri/SKILLs/releases/latest"
UPGRADE = ["uv", "tool", "install", "skills", "--force", "--from", "git+https://github.com/Ogekuri/SKILLs.git"]
UNINSTALL = ["uv", "tool", "uninstall", "skills"]
HELP = f"""Usage: skills [command] [options] ({__version__})

Management Commands:
  --upgrade   - Reinstall skills on Linux; print manual command elsewhere.
  --uninstall - Uninstall skills on Linux; print manual command elsewhere.
  --ver       - Print the skills version.
  --version   - Print the skills version.
  --help      - Print the full help screen or the help text of a specific command.

Commands:
  ..."""


def cache_path() -> Path:
    return Path.home() / ".cache" / "skills" / "check_version_idle-time.json"


def _human(timestamp: float | None) -> str | None:
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat() if timestamp is not None else None


def _version(value: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", value)
    if not match:
        raise ValueError(f"Invalid release version: {value}")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def check_version(force: bool = False) -> None:
    path = cache_path()
    cache = {}
    try:
        with path.open(encoding="utf-8") as file:
            cache = json.load(file)
        if not isinstance(cache, dict):
            cache = {}
    except (OSError, ValueError):
        pass
    now = time.time()
    idle = cache.get("idle_time_epoch")
    if not force and isinstance(idle, (int, float)) and idle > now:
        return

    last_success = cache.get("last_success_epoch")
    if not isinstance(last_success, (int, float)):
        last_success = None
    delay = 86400
    try:
        request = Request(ENDPOINT, headers={"Accept": "application/vnd.github+json", "User-Agent": "skills"})
        with urlopen(request, timeout=2) as response:
            release = json.load(response)
        available = release["tag_name"]
        newer = _version(available) > _version(__version__)
        now = time.time()
        last_success = now
        if newer:
            delay = 3600
            print(f"\033[92mAvailable Version: {available} | Installed Version: {__version__}\033[0m", file=sys.stderr)
        else:
            print("\033[91mVersion check: no newer version available.\033[0m", file=sys.stderr)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        now = time.time()
        print(f"\033[91mVersion check error: {exc}\033[0m", file=sys.stderr)
    data = {
        "last_success_epoch": last_success,
        "last_success_human": _human(last_success),
        "idle_time_epoch": now + delay,
        "idle_time_human": _human(now + delay),
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"\033[91mVersion cache error: {exc}\033[0m", file=sys.stderr)


def _manage(command: list[str]) -> int:
    if not sys.platform.startswith("linux"):
        print(f"Warning: run this command manually: {' '.join(command)}")
        return 0
    try:
        return subprocess.run(command, check=False).returncode
    except OSError as exc:
        print(f"Error executing {command[0]}: {exc}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    check_version(force="--ver" in args or "--version" in args)
    if not args or args == ["--help"]:
        print(HELP)
        return 0
    if len(args) == 2 and "--help" in args:
        command = args[0] if args[1] == "--help" else args[1]
        descriptions = {
            "--upgrade": "Reinstall skills on Linux; print manual command elsewhere.",
            "--uninstall": "Uninstall skills on Linux; print manual command elsewhere.",
            "--ver": "Print the skills version.",
            "--version": "Print the skills version.",
        }
        if command in descriptions:
            print(f"{command} - {descriptions[command]}")
            return 0
    if args in (["--ver"], ["--version"]):
        print(__version__)
        return 0
    if args == ["--upgrade"]:
        return _manage(UPGRADE)
    if args == ["--uninstall"]:
        return _manage(UNINSTALL)
    print(f"Unknown command or options: {' '.join(args)}", file=sys.stderr)
    return 2
