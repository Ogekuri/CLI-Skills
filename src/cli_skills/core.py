"""CLI management commands, resource installation and uninstallation dispatch, and release notification orchestration."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from . import __version__
from . import configops, configview, schema
from .installer import install_enabled, uninstall_enabled
from .settings import load_config, save_config
from .show import build_show
from .targets import TARGETS, resolve_target

## @brief PyPI JSON API endpoint for the newest published version.
## @satisfies DES-042
PYPI_ENDPOINT = "https://pypi.org/pypi/cli-skills/json"
ENDPOINT = "https://api.github.com/repos/Ogekuri/CLI-Skills/releases/latest"
## @brief Standard upgrade argv installing from PyPI without any force option.
## @details Executed for `--upgrade`; runs the standard install/update process.
## @satisfies DES-040 REQ-010
UPGRADE = ["uv", "tool", "install", "cli-skills"]
## @brief Forced-upgrade argv forcing download and complete reinstallation from PyPI.
## @details Executed for `--upgrade --force`; appends the uv tool install
##          reinstallation options `--force --reinstall --refresh`.
## @satisfies DES-103 REQ-067
UPGRADE_FORCE = ["uv", "tool", "install", "cli-skills", "--force", "--reinstall", "--refresh"]
## @brief Upgrade command argv installing the latest tagged GitHub release via git.
## @details Executed for `--upgrade --dev` and `--upgrade --develop`; bypasses PyPI.
## @satisfies DES-081 REQ-063
UPGRADE_DEVELOP = ["uv", "tool", "install", "cli-skills", "--from", "git+https://github.com/Ogekuri/CLI-Skills.git"]
## @brief Forced-upgrade argv forcing download and complete reinstallation from GitHub.
## @details Executed for `--upgrade` combined with `--dev` or `--develop` and
##          `--force`; appends the reinstallation options before `--from`.
## @satisfies DES-103 REQ-068
UPGRADE_DEVELOP_FORCE = ["uv", "tool", "install", "cli-skills", "--force", "--reinstall", "--refresh", "--from", "git+https://github.com/Ogekuri/CLI-Skills.git"]
UNINSTALL = ["uv", "tool", "uninstall", "cli-skills"]
SKILLS_INSTALL = ["cli-skills", "install"]
"""
@brief Child `cli-skills install` command executed after a successful upgrade.
@details Spawned by `_post_upgrade_install` so the freshly upgraded package
         installs its bundled skills into every enabled CLI.
@satisfies REQ-043
"""
_REPORT_LABEL_WIDTH = 18
"""
@brief Common left-justified width of the `--ver` and `--version` report labels.
@details Width of the longest label `Current Installed` (17 characters) plus
         one separator space, so the `:` delimiters and version values align
         vertically across the three report lines.
@satisfies REQ-070
"""
HELP = f"""Usage: cli-skills [command] [options] ({__version__})

Management Commands:
  --upgrade   - Upgrade cli-skills on Linux; print manual command elsewhere.
  --uninstall - Uninstall cli-skills on Linux; print manual command elsewhere.
  --ver       - Print the cli-skills version.
  --version   - Print the cli-skills version.
  --dev       - With --upgrade, install the latest GitHub release instead of PyPI.
  --force     - With --upgrade, force download and complete reinstallation.
  --help      - Print the full help screen or the help text of a specific command.

Installation Commands:
  enable <cli name>  - Enable skill installation for a supported CLI.
  disable <cli name> - Disable skill installation for a supported CLI.
  install            - Install skills for every enabled CLI.
  uninstall          - Remove installed skills for every enabled CLI.

Reporting Commands:
  show               - Show packaged resources, CLI configuration, and installation status.

Configuration Commands:
  --print [<path>]     - Print the configuration tree or a configuration subtree.
  --info [<path>]      - Print the configuration schema reference or a schema subtree.
  --print-raw          - Print the raw configuration JSON file bytes.
  --get <path>         - Print the JSON value stored at a canonical configuration path.
  --set <path> <value> - Set a canonical configuration path to a value.
  --unset <path>       - Reset or remove a canonical configuration path.

Commands:
  ..."""

## @brief Configuration commands dispatched through the shared schema.
## @details Order defines the dispatch set only; the help template owns the
##          documented order.
## @satisfies DES-105 DES-106 DES-130
CONFIG_COMMANDS = ("--print", "--info", "--print-raw", "--get", "--set", "--unset")


def cache_path() -> Path:
    return Path.home() / ".cache" / "cli-skills" / "check_version_idle-time.json"


def _human(timestamp: float | None) -> str | None:
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat() if timestamp is not None else None


def _version(value: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", value)
    if not match:
        raise ValueError(f"Invalid release version: {value}")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def _http_json(url: str, accept: str) -> dict:
    """
    @brief Perform one HTTP GET and parse the JSON response body.
    @details Sends a `cli-skills` User-Agent with the caller-supplied Accept
             header and enforces the hardcoded 2-second timeout. Network and
             protocol errors propagate to the caller.
    @param url {str} Absolute HTTP/HTTPS endpoint URL.
    @param accept {str} HTTP Accept header value.
    @return {Dict} Decoded top-level JSON object.
    @throws {OSError} On transport or HTTP errors, including 429 and 503.
    @throws {ValueError} When the response body is not valid JSON.
    @satisfies CTN-006 DES-042 DES-083
    """
    request = Request(url, headers={"Accept": accept, "User-Agent": "cli-skills"})
    with urlopen(request, timeout=2) as response:
        return json.load(response)


def fetch_pypi_latest() -> str:
    """
    @brief Fetch the newest published version from the PyPI JSON API.
    @details Requests `PYPI_ENDPOINT`, reads `info.version`, and returns it
             trimmed. Any transport, HTTP, or payload-shape failure raises.
    @return {str} Newest PyPI version string.
    @throws {OSError} On transport or HTTP errors, including 429 and 503.
    @throws {ValueError} When the payload is not valid JSON or omits a
            non-empty string `info.version`.
    @throws {KeyError} When the payload omits `info.version`.
    @satisfies DES-042 REQ-002 REQ-003 REQ-059
    """
    version = _http_json(PYPI_ENDPOINT, "application/json")["info"]["version"]
    if not isinstance(version, str) or not version.strip():
        raise ValueError("missing PyPI latest version")
    return version.strip()


def fetch_github_latest() -> str:
    """
    @brief Fetch the newest GitHub release version in `x.y.z` form.
    @details Requests `ENDPOINT`, reads `tag_name`, and strips an optional `v`
             prefix. The returned release is the newest tagged GitHub release
             regardless of its source branch, matching the `--upgrade --dev`
             download source.
    @return {str} Newest GitHub release version as `x.y.z`.
    @throws {OSError} On transport or HTTP errors, including 429 and 503.
    @throws {ValueError} When the payload omits or holds an invalid
            `tag_name`.
    @throws {KeyError} When the payload omits `tag_name`.
    @satisfies DES-083 REQ-061 REQ-062 REQ-063
    """
    tag = _http_json(ENDPOINT, "application/vnd.github+json")["tag_name"]
    if not isinstance(tag, str):
        raise ValueError("missing GitHub latest release tag")
    match = re.fullmatch(r"v?(\d+\.\d+\.\d+)", tag.strip())
    if not match:
        raise ValueError(f"invalid GitHub release tag: {tag}")
    return match.group(1)


def _failure_reason(exc: Exception) -> str:
    """
    @brief Normalize one release-fetch failure to a concise reason string.
    @details For `HTTPError`, decodes the error body as JSON and surfaces the
             API `message` field prefixed with `HTTP <code>`; this exposes
             GitHub rate-limit causes such as `API rate limit exceeded`
             that arrive with HTTP 404. Body decode failures fall back to
             `HTTP <code>`; non-HTTP errors return `str(exc)`. Complexity
             O(B) where B is the error-body byte length.
    @param exc {Exception} Failure raised by `_http_json` or its callers.
    @return {str} Human-readable reason identifying the actual error cause.
    @satisfies REQ-066
    """
    if not isinstance(exc, HTTPError):
        return str(exc)
    try:
        message = json.loads(exc.read().decode("utf-8", "replace")).get("message")
    except (OSError, ValueError, AttributeError):
        return f"HTTP {exc.code}"
    if isinstance(message, str) and message.strip():
        return f"HTTP {exc.code}: {message.strip()}"
    return f"HTTP {exc.code}"


def _report_line(label: str, value: str) -> str:
    """
    @brief Format one aligned `--ver`/`--version` report line.
    @details Left-justifies `label` to `_REPORT_LABEL_WIDTH` characters and
             appends `: ` plus the value, so the `:` delimiters and version
             values align vertically across the three report lines.
    @param label {str} Report label: `Current Installed`, `Latest @ PyPI`,
            or `Latest @ GitHub`.
    @param value {str} Rendered version or failure value.
    @return {str} Aligned report line without trailing newline.
    @satisfies REQ-006 REQ-060 REQ-061 REQ-070
    """
    return f"{label:<{_REPORT_LABEL_WIDTH}}: {value}"


def check_version(force: bool = False) -> None:
    """
    @brief Run the cached automatic release check against PyPI.
    @details Skips while the cached idle-time is valid unless `force` is set;
             otherwise fetches the newest PyPI version via `fetch_pypi_latest`,
             compares it with `__version__`, prints a bright-green
             available-versus-installed message when a newer version exists or
             a bright-red message for a failed or negative check, records
             last-success timestamps on success only, and writes the cache
             with a 3600-second (positive) or 86400-second (negative or
             failed) expiration.
    @param force {bool} Bypass the cached idle-time and perform the request.
    @return {None}
    @note Cache read/write and network failures are reported to stderr and do
          not raise.
    @satisfies REQ-001 REQ-002 REQ-003 REQ-004 REQ-005 REQ-016 REQ-017 REQ-018
               REQ-019 REQ-020 REQ-021 REQ-022 REQ-023 REQ-059 CTN-006 CTN-007
               CTN-008 DES-042 DES-043 DES-044 DES-045 DES-046
    """
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
        available = fetch_pypi_latest()
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
    @brief Install bundled resources through `cli-skills install` after a
           successful upgrade.
    @details Loads the user configuration and, when at least one CLI is
             enabled, spawns `cli-skills install` as a child process so the
             freshly upgraded package synchronizes its bundled skills into
             every enabled CLI. Skips the child process when
             the enabled configuration is empty. The child reads the
             upgraded package resources, not the running process ones. The
             child inherits stdout, so its per-CLI count and installed-name
             report surfaces as visible `--upgrade` output.
    @param home {Path | None} Optional home-directory override used only for
            the configuration read; the child process inherits the real
            environment.
    @return {int} 0 when no CLI is enabled; otherwise the `cli-skills install`
            exit code (1 on spawn or installation failure).
    @throws {OSError} When reading the configuration file fails.
    @satisfies REQ-043 REQ-044 REQ-046 REQ-058
    """
    if not load_config(home)["enabled"]:
        return 0
    return _manage(SKILLS_INSTALL)


def _run_upgrade(command: list[str]) -> int:
    """
    @brief Execute one upgrade command and chain the post-upgrade install.
    @details Delegates to `_manage` and, on a zero exit code under Linux,
             chains `_post_upgrade_install` so the freshly upgraded package
             installs bundled resources into every enabled CLI. Used by the
             PyPI `--upgrade` form (with or without `--force`) and the GitHub
             `--upgrade --dev` form (with or without `--force`).
    @param command {list[str]} Upgrade command argv executed on Linux and
            printed as the manual command on other operating systems.
    @return {int} Upgrade exit code, or the chained `cli-skills install` exit
            code when the chained install executes.
    @satisfies REQ-010 REQ-011 REQ-012 REQ-043 REQ-044 REQ-045 REQ-046
               REQ-063 REQ-067 REQ-068 REQ-069
    """
    upgraded = _manage(command)
    if upgraded == 0 and sys.platform.startswith("linux"):
        return _post_upgrade_install()
    return upgraded


def _unsupported(name: str) -> str:
    """
    @brief Build an unsupported-CLI diagnostic message.
    @details Lists the canonical CLI names accepted by the adapter registry in
             alphabetical order.
    @param name {str} Unsupported CLI name from the command line.
    @return {str} Human-readable diagnostic message.
    @satisfies REQ-026 DES-092
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
    @details Delegates installation to `install_enabled`, prints per-CLI
             installed skill counts plus the installed skill names, prints an
             informational message when no CLI is enabled, and reports
             collected failures.
    @param home {Path | None} Optional home-directory override.
    @return {int} Exit code: 0 when no failure occurs; 1 when any failure
            occurs.
    @satisfies REQ-029 REQ-030 REQ-031 REQ-032 REQ-057
    """
    summaries, errors = install_enabled(home)
    if not summaries and not errors:
        print("No CLI enabled. Use 'cli-skills enable <cli name>' first.")
        return 0
    for summary in summaries:
        print(f"Installed {summary.skills} skills for {summary.cli}.")
        print(f"  Skills: {', '.join(summary.skill_names) or 'none'}")
    for error in errors:
        print(f"Error: {error}", file=sys.stderr)
    return 1 if errors else 0


def _uninstall(home: Path | None = None) -> int:
    """
    @brief Remove installed bundled resources for all enabled CLIs.
    @details Delegates uninstallation to `uninstall_enabled`, prints per-CLI
             removed skill counts, prints an informational message
             when no CLI is enabled, and reports collected failures.
    @param home {Path | None} Optional home-directory override.
    @return {int} Exit code: 0 when no failure occurs; 1 when any failure
            occurs.
    @satisfies REQ-047 REQ-054 REQ-055 REQ-056
    """
    summaries, errors = uninstall_enabled(home)
    if not summaries and not errors:
        print("No CLI enabled. Use 'cli-skills enable <cli name>' first.")
        return 0
    for summary in summaries:
        print(f"Removed {summary.skills} skills for {summary.cli}.")
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


def _upgrade_command(options: list[str]) -> list[str] | None:
    """
    @brief Resolve the upgrade argv for the options following `--upgrade`.
    @details Accepts any order of the auxiliary options `--dev`, `--develop`,
             and `--force`; returns `None` for unknown options, duplicate
             options, and the redundant `--dev` plus `--develop` combination.
             `--force` selects the `--force --reinstall --refresh`
             reinstallation argv; `--dev` or `--develop` selects the GitHub
             `--from` argv. Complexity O(n) where n is the option count.
    @param options {list[str]} Option tokens following `--upgrade`; empty for
            the plain `--upgrade` form.
    @return {list[str]} Matching upgrade argv; `None` when the options are
            invalid.
    @satisfies DES-040 DES-081 DES-103 REQ-010 REQ-063 REQ-067 REQ-068
    """
    allowed = ("--dev", "--develop", "--force")
    if any(option not in allowed for option in options):
        return None
    if len(set(options)) != len(options) or ("--dev" in options and "--develop" in options):
        return None
    if "--dev" in options or "--develop" in options:
        return UPGRADE_DEVELOP_FORCE if "--force" in options else UPGRADE_DEVELOP
    return UPGRADE_FORCE if "--force" in options else UPGRADE


def _configure(args: list[str], home: Path | None = None) -> int:
    """
    @brief Execute one configuration display or mutation command.
    @details Dispatches `--print`, `--info`, `--print-raw`, `--get`, `--set`,
             and `--unset` against the canonical schema. Valid output goes to
             stdout; every diagnostic goes to stderr with exit status 1 and no
             partial success output. `--print-raw` writes the stored bytes
             unchanged and never applies tree formatting.
    @param args {list[str]} Command token followed by its canonical path and value.
    @param home {Path | None} Optional home-directory override.
    @return {int} Exit code: 0 on success; 1 on any configuration failure.
    @satisfies DES-105 DES-106 DES-111 DES-115 DES-116 DES-117 DES-130
    """
    name = args[0]
    try:
        if name == "--print":
            if len(args) > 2:
                raise configops.ConfigError("Usage: cli-skills --print [<path>]")
            config = configops.read_config(home)
            print(configview.render_print(config, args[1] if len(args) == 2 else None))
            return 0
        if name == "--info":
            if len(args) > 2:
                raise configops.ConfigError("Usage: cli-skills --info [<path>]")
            print(configview.render_info(args[1] if len(args) == 2 else None))
            return 0
        if name == "--print-raw":
            if len(args) != 1:
                raise configops.ConfigError("Usage: cli-skills --print-raw")
            payload = configops.read_raw(home)
            buffer = getattr(sys.stdout, "buffer", None)
            if buffer is None:
                sys.stdout.write(payload.decode("utf-8"))
            else:
                buffer.write(payload)
                buffer.flush()
            return 0
        if name == "--get":
            if len(args) != 2:
                raise configops.ConfigError("Usage: cli-skills --get <path>")
            path = schema.parse_path(args[1])
            value = configops.get_value(configops.read_config(home), path)
            print(json.dumps(value, ensure_ascii=False))
            return 0
        if name == "--set":
            if len(args) != 3:
                raise configops.ConfigError("Usage: cli-skills --set <path> <value>")
            written = configops.set_path(args[1], args[2], home)
            print(f"Set {written.display}.")
            return 0
        if name == "--unset":
            if len(args) != 2:
                raise configops.ConfigError("Usage: cli-skills --unset <path>")
            written = configops.unset_path(args[1], home)
            print(f"Unset {written.display}.")
            return 0
    except (configops.ConfigError, schema.SchemaError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Error: unknown configuration command: {name}", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    """
    @brief Run the automatic release check and dispatch one CLI command.
    @details Executes `check_version` before argument parsing (forced by
             `--ver` or `--version`), then routes to help, version,
             management, enable/disable, install, uninstall, show, or
             configuration handlers. Configuration commands dispatch through
             `_configure` against the canonical schema. The `--upgrade`
             branch, for any accepted
             `--dev`/`--develop`/`--force` combination, chains
             `cli-skills install` after a successful Linux upgrade when the
             enabled configuration is non-empty and returns the chained exit
             code. The `--ver` and `--version` branch prints the installed,
             PyPI, and GitHub versions on the aligned `Current Installed`,
             `Latest @ PyPI`, and `Latest @ GitHub` lines built by
             `_report_line`, printing `unavailable (<reason>)` and
             `unknown (<reason>)` values when the PyPI or GitHub request
             fails.
    @param argv {list[str] | None} Command-line arguments; defaults to
            `sys.argv[1:]`.
    @return {int} Process exit code: 0 on success; 1 on upgrade or install
            failure; 2 on usage errors.
    @satisfies REQ-006 REQ-007 REQ-008 REQ-009 REQ-010 REQ-011 REQ-012
               REQ-013 REQ-014 REQ-015 REQ-024 REQ-025 REQ-026 REQ-029
               REQ-030 REQ-031 REQ-032 REQ-037 REQ-042 REQ-043 REQ-044
               REQ-045 REQ-046 REQ-047 REQ-054 REQ-055 REQ-056 REQ-057
               REQ-058 REQ-059 REQ-060 REQ-061 REQ-062 REQ-063 REQ-064
               REQ-065 REQ-066 REQ-067 REQ-068 REQ-069 REQ-070 REQ-071
               DES-089 DES-103 DES-105 DES-106 DES-130
    """
    args = list(sys.argv[1:] if argv is None else argv)
    check_version(force="--ver" in args or "--version" in args)
    if not args or args == ["--help"]:
        print(HELP)
        return 0
    if len(args) == 2 and args[1] == "--help":
        command = args[0]
        descriptions = {
            "--upgrade": "Upgrade cli-skills on Linux; print manual command elsewhere.",
            "--uninstall": "Uninstall cli-skills on Linux; print manual command elsewhere.",
            "--ver": "Print the cli-skills version.",
            "--version": "Print the cli-skills version.",
            "--dev": "With --upgrade, install the latest GitHub release instead of PyPI.",
            "--force": "With --upgrade, force download and complete reinstallation.",
            "enable": "Enable skill installation for a supported CLI.",
            "disable": "Disable skill installation for a supported CLI.",
            "install": "Install skills for every enabled CLI.",
            "uninstall": "Remove installed skills for every enabled CLI.",
            "show": "Show packaged resources, CLI configuration, and installation status.",
            "--print": "Print the configuration tree or a configuration subtree.",
            "--info": "Print the configuration schema reference or a schema subtree.",
            "--print-raw": "Print the raw configuration JSON file bytes.",
            "--get": "Print the JSON value stored at a canonical configuration path.",
            "--set": "Set a canonical configuration path to a value.",
            "--unset": "Reset or remove a canonical configuration path.",
        }
        if command in descriptions:
            print(f"{command} - {descriptions[command]}")
            return 0
    if args in (["--ver"], ["--version"]):
        print(_report_line("Current Installed", __version__))
        try:
            print(_report_line("Latest @ PyPI", fetch_pypi_latest()))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            print(_report_line("Latest @ PyPI", f"unavailable ({exc})"))
        try:
            print(_report_line("Latest @ GitHub", fetch_github_latest()))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            print(_report_line("Latest @ GitHub", f"unknown ({_failure_reason(exc)})"))
        return 0
    if args and args[0] == "--upgrade":
        command = _upgrade_command(args[1:])
        if command is not None:
            return _run_upgrade(command)
    if args == ["--uninstall"]:
        return _manage(UNINSTALL)
    if len(args) == 1 and args[0] in ("enable", "disable"):
        print(f"Usage: cli-skills {args[0]} <cli name>", file=sys.stderr)
        return 2
    if len(args) == 2 and args[0] == "enable":
        return _enable(args[1])
    if len(args) == 2 and args[0] == "disable":
        return _disable(args[1])
    if args == ["install"]:
        return _install()
    if args == ["uninstall"]:
        return _uninstall()
    if args == ["show"]:
        return _show()
    if args and args[0] in CONFIG_COMMANDS:
        return _configure(args)
    print(f"Unknown command or options: {' '.join(args)}", file=sys.stderr)
    return 2
