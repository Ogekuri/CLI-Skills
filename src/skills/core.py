"""CLI management commands, resource installation dispatch, and release notification orchestration."""

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
from .installer import install_enabled
from .settings import load_config, save_config
from .show import build_show
from .targets import TARGETS, resolve_target

ENDPOINT = "https://api.github.com/repos/Ogekuri/SKILLs/releases/latest"
UPGRADE = ["uv", "tool", "install", "skills", "--force", "--from", "git+https://github.com/Ogekuri/SKILLs.git"]
UNINSTALL = ["uv", "tool", "uninstall", "skills"]
SKILLS_INSTALL = ["skills", "install"]
"""
@brief Child `skills install` command executed after a successful upgrade.
@details Spawned by `_post_upgrade_install` so the freshly upgraded package
         installs its bundled skills and prompts into every enabled CLI.
@satisfies REQ-043
"""
HELP = f"""Usage: skills [command] [options] ({__version__})

Management Commands:
  --upgrade   - Reinstall skills on Linux; print manual command elsewhere.
  --uninstall - Uninstall skills on Linux; print manual command elsewhere.
  --ver       - Print the skills version.
  --version   - Print the skills version.
  --help      - Print the full help screen or the help text of a specific command.

Installation Commands:
  enable <cli name>  - Enable skill and prompt installation for a supported CLI.
  disable <cli name> - Disable skill and prompt installation for a supported CLI.
  install            - Install skills and prompts for every enabled CLI.

Reporting Commands:
  show               - Show packaged resources, CLI configuration, and installation status.

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


def _post_upgrade_install(home: Path | None = None) -> int:
    """
    @brief Install bundled resources through `skills install` after a
           successful upgrade.
    @details Loads the user configuration and, when at least one CLI is
             enabled, spawns `skills install` as a child process so the
             freshly upgraded package synchronizes its bundled skills and
             prompts into every enabled CLI. Skips the child process when
             the enabled configuration is empty. The child reads the
             upgraded package resources, not the running process ones.
    @param home {Path | None} Optional home-directory override used only for
            the configuration read; the child process inherits the real
            environment.
    @return {int} 0 when no CLI is enabled; otherwise the `skills install`
            exit code (1 on spawn or installation failure).
    @throws {OSError} When reading the configuration file fails.
    @satisfies REQ-043 REQ-044 REQ-046
    """
    if not load_config(home)["enabled"]:
        return 0
    return _manage(SKILLS_INSTALL)


def _unsupported(name: str) -> str:
    """
    @brief Build an unsupported-CLI diagnostic message.
    @details Lists the canonical CLI names accepted by the adapter registry.
    @param name {str} Unsupported CLI name from the command line.
    @return {str} Human-readable diagnostic message.
    @satisfies REQ-026
    """
    return f"Unsupported CLI: {name}. Supported: {', '.join(TARGETS)}."


def _enable(name: str, home: Path | None = None) -> int:
    """
    @brief Enable resource installation for one supported CLI.
    @details Resolves the CLI adapter, loads the user configuration, appends
             the canonical CLI name when absent, and persists the configuration.
             Re-enabling an enabled CLI leaves configuration unchanged.
    @param name {str} CLI name from the command line.
    @param home {Path | None} Optional home-directory override.
    @return {int} Exit code: 0 on success; 2 for an unsupported CLI.
    @throws {OSError} When saving the configuration file fails.
    @satisfies REQ-024 REQ-026 REQ-027 REQ-028
    """
    target = resolve_target(name)
    if target is None:
        print(_unsupported(name), file=sys.stderr)
        return 2
    config = load_config(home)
    if target.name in config["enabled"]:
        print(f"{target.name} is already enabled.")
        return 0
    config["enabled"].append(target.name)
    save_config(config, home)
    print(f"Enabled {target.name}.")
    return 0


def _disable(name: str, home: Path | None = None) -> int:
    """
    @brief Disable resource installation for one supported CLI.
    @details Resolves the CLI adapter, loads the user configuration, removes
             the canonical CLI name when present, and persists the
             configuration. Disabling an already disabled CLI is a successful
             no-op.
    @param name {str} CLI name from the command line.
    @param home {Path | None} Optional home-directory override.
    @return {int} Exit code: 0 on success; 2 for an unsupported CLI.
    @throws {OSError} When saving the configuration file fails.
    @satisfies REQ-025 REQ-026 REQ-027 REQ-028
    """
    target = resolve_target(name)
    if target is None:
        print(_unsupported(name), file=sys.stderr)
        return 2
    config = load_config(home)
    if target.name not in config["enabled"]:
        print(f"{target.name} is already disabled.")
        return 0
    config["enabled"] = [item for item in config["enabled"] if item != target.name]
    save_config(config, home)
    print(f"Disabled {target.name}.")
    return 0


def _install(home: Path | None = None) -> int:
    """
    @brief Install bundled resources for all enabled CLIs.
    @details Delegates installation to `install_enabled`, prints per-CLI skill
             and prompt counts, prints an informational message when no CLI is
             enabled, and reports collected failures.
    @param home {Path | None} Optional home-directory override.
    @return {int} Exit code: 0 when no failure occurs; 1 when any failure
            occurs.
    @satisfies REQ-029 REQ-030 REQ-031 REQ-032
    """
    summaries, errors = install_enabled(home)
    if not summaries and not errors:
        print("No CLI enabled. Use 'skills enable <cli name>' first.")
        return 0
    for summary in summaries:
        print(
            f"Installed {summary.skills} skills and "
            f"{summary.prompts} prompts for {summary.cli}."
        )
    for error in errors:
        print(f"Error: {error}", file=sys.stderr)
    return 1 if errors else 0


def _show(home: Path | None = None) -> int:
    """
    @brief Print packaged resources, CLI configuration, and installation status.
    @details Delegates report rendering to `build_show` and prints the result.
    @param home {Path | None} Optional home-directory override.
    @return {int} Exit code 0 after printing the report.
    @throws {OSError} When bundled resources or the configuration cannot be read.
    @satisfies REQ-037 REQ-038 REQ-039 REQ-042
    """
    print(build_show(home))
    return 0


def main(argv: list[str] | None = None) -> int:
    """
    @brief Run the automatic release check and dispatch one CLI command.
    @details Executes `check_version` before argument parsing (forced by
             `--ver` or `--version`), then routes to help, version,
             management, enable/disable, install, or show handlers. The
             `--upgrade` branch chains `skills install` after a successful
             Linux upgrade when the enabled configuration is non-empty and
             returns the chained exit code.
    @param argv {list[str] | None} Command-line arguments; defaults to
            `sys.argv[1:]`.
    @return {int} Process exit code: 0 on success; 1 on upgrade or install
            failure; 2 on usage errors.
    @satisfies REQ-006 REQ-007 REQ-008 REQ-009 REQ-010 REQ-011 REQ-012
               REQ-013 REQ-014 REQ-015 REQ-024 REQ-025 REQ-026 REQ-029
               REQ-030 REQ-031 REQ-032 REQ-037 REQ-042 REQ-043 REQ-044
               REQ-045 REQ-046
    """
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
            "enable": "Enable skill and prompt installation for a supported CLI.",
            "disable": "Disable skill and prompt installation for a supported CLI.",
            "install": "Install skills and prompts for every enabled CLI.",
            "show": "Show packaged resources, CLI configuration, and installation status.",
        }
        if command in descriptions:
            print(f"{command} - {descriptions[command]}")
            return 0
    if args in (["--ver"], ["--version"]):
        print(__version__)
        return 0
    if args == ["--upgrade"]:
        upgraded = _manage(UPGRADE)
        if upgraded == 0 and sys.platform.startswith("linux"):
            return _post_upgrade_install()
        return upgraded
    if args == ["--uninstall"]:
        return _manage(UNINSTALL)
    if len(args) == 1 and args[0] in ("enable", "disable"):
        print(f"Usage: skills {args[0]} <cli name>", file=sys.stderr)
        return 2
    if len(args) == 2 and args[0] == "enable":
        return _enable(args[1])
    if len(args) == 2 and args[0] == "disable":
        return _disable(args[1])
    if args == ["install"]:
        return _install()
    if args == ["show"]:
        return _show()
    print(f"Unknown command or options: {' '.join(args)}", file=sys.stderr)
    return 2
