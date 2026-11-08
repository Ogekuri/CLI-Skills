# Files Structure
```
.
└── src
    ├── cli_skills
    │   ├── __init__.py
    │   ├── __main__.py
    │   ├── catalog.py
    │   ├── core.py
    │   ├── installer.py
    │   ├── settings.py
    │   ├── show.py
    │   └── targets.py
    └── resources
        └── __init__.py
```

# __init__.py | Python | 13L | 0 symbols | 1 imports | 7 comments
> Path: `src/cli_skills/__init__.py`

## Imports
```
from .core import main  # noqa: F401
```


---

# __main__.py | Python | 11L | 0 symbols | 2 imports | 5 comments
> Path: `src/cli_skills/__main__.py`

## Imports
```
from .core import main
import sys
```


---

# catalog.py | Python | 165L | 10 symbols | 4 imports | 11 comments
> Path: `src/cli_skills/catalog.py`
- @brief Generate the skills manifest for `src/resources`.
- @details Deterministic generator for `src/resources/manifest.json`. Recursively
scans `src/resources/skills` for `SKILL.md` files, extracts frontmatter
`name` and `description`, and emits entries sorted by relative path.
Validates every skill directory against the canonical support layout
before accepting its metadata. Single maintenance path guaranteeing
each manifest description equals its source frontmatter `description`
string (exact match).
- @satisfies DES-021 DES-022 DES-023 DES-024 DES-067 DES-068 DES-069 DES-070 DES-071 DES-072 DES-073

## Imports
```
from __future__ import annotations
import importlib.resources as ires
import json
from pathlib import Path
```

## Definitions

- var `RESOURCES_ROOT = Path(str(ires.files("resources")))` (L20)
- var `MANIFEST_PATH = RESOURCES_ROOT / "manifest.json"` (L21)
- var `SKILL_SUPPORT_DIRECTORIES = ("scripts", "references", "assets", "images")` (L24)
- @brief Canonical skill support subdirectory names allowed at the skill root.
- @details Any other root directory or non-`SKILL.md` root file violates DES-067.
- var `REFERENCE_SUPPORT_DIRECTORIES = ("images",)` (L27)
- @brief Canonical nested subdirectory names allowed directly under `references`.
- @details Any other nested directory under `references` violates DES-069 and DES-070.
### class `class SkillLayoutError(ValueError)` : ValueError (L30-39)
- @brief Signal a bundled skill layout that violates the canonical support layout.
- @details Raised by `validate_skill_layout` when a skill root contains an entry outside the canonical support subdirectories or when `references` contains a non-canonical subdirectory.
- @satisfies DES-073

### fn `def validate_skill_layout(skill_dir: Path) -> None` (L40-68)
- @brief Validate a bundled skill directory against the canonical support layout.
- @details Accepts `SKILL.md` plus the canonical support subdirectories at the skill root; accepts only `images` as a nested directory directly under `references`. Non-canonical root files and directories are rejected. Complexity O(E) where E is the number of root entries plus direct `references` entries.
- @param skill_dir {Path} Packaged skill directory containing `SKILL.md`.
- @return {None}
- @throws {SkillLayoutError} When a root entry or a nested `references` directory violates DES-067 through DES-072.
- @satisfies DES-067 DES-068 DES-069 DES-070 DES-071 DES-072 DES-073
- @pre `skill_dir` MUST be an existing directory.
- @post The directory layout is canonical or an exception is raised.

### fn `def _parse_frontmatter(text: str) -> dict[str, str]` `priv` (L69-101)
- @brief Parse `name` and `description` from a YAML frontmatter block.
- @details Reads key/value lines up to the closing `---` delimiter, strips surrounding YAML quotes from scalar values, and returns only the `name` and `description` keys when present.
- @param text {str} Raw file text (UTF-8).
- @return {Dict[str, str]} Frontmatter `name`/`description` mapping; empty when the block or keys are absent.
- @pre `text` must be a non-empty string.

### fn `def _discover_skills(root: Path) -> list[Path]` `priv` (L102-114)
- @brief Discover `SKILL.md` files under `root/skills`.
- @details Recursively collects every file named `SKILL.md`, sorted by path.
- @param root {Path} Resources root directory.
- @return {List[Path]} Sorted `SKILL.md` file paths.

### fn `def build_catalog(` (L115-116)

### fn `def write_catalog(` (L146-148)
- @brief Build the skills catalog dictionary.
- @details Validates each skill directory layout, then scans the skills
directory, extracts frontmatter metadata, and emits entries
sorted by relative path. Entries missing `name` or `description`
are omitted.
- @param resources_root {Path} Resources root directory to scan.
- @return {Dict[str, List[Dict[str, str]]]} Catalog with a `skills` list;
each entry contains `file`, `name`, `description`.
- @throws {SkillLayoutError} When a discovered skill directory violates the
canonical support layout.
- @satisfies DES-021 DES-022 DES-023 DES-024 DES-067 DES-068 DES-069 DES-070 DES-071 DES-072 DES-073

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`RESOURCES_ROOT`|var|pub|20||
|`MANIFEST_PATH`|var|pub|21||
|`SKILL_SUPPORT_DIRECTORIES`|var|pub|24||
|`REFERENCE_SUPPORT_DIRECTORIES`|var|pub|27||
|`SkillLayoutError`|class|pub|30-39|class SkillLayoutError(ValueError)|
|`validate_skill_layout`|fn|pub|40-68|def validate_skill_layout(skill_dir: Path) -> None|
|`_parse_frontmatter`|fn|priv|69-101|def _parse_frontmatter(text: str) -> dict[str, str]|
|`_discover_skills`|fn|priv|102-114|def _discover_skills(root: Path) -> list[Path]|
|`build_catalog`|fn|pub|115-116|def build_catalog(|
|`write_catalog`|fn|pub|146-148|def write_catalog(|


---

# core.py | Python | 478L | 24 symbols | 15 imports | 22 comments
> Path: `src/cli_skills/core.py`

## Imports
```
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
from .installer import install_enabled, uninstall_enabled
from .settings import load_config, save_config
from .show import build_show
from .targets import TARGETS, resolve_target
```

## Definitions

- var `PYPI_ENDPOINT = "https://pypi.org/pypi/cli-skills/json"` (L23)
- @brief PyPI JSON API endpoint for the newest published version.
- @satisfies DES-042
- var `ENDPOINT = "https://api.github.com/repos/Ogekuri/CLI-Skills/releases/latest"` (L24)
- var `UPGRADE = ["uv", "tool", "install", "cli-skills", "--force"]` (L25)
- var `UPGRADE_DEVELOP = ["uv", "tool", "install", "cli-skills", "--force", "--from", "git+https://github.com/Ogekuri/CLI-Skills.git"]` (L29)
- @brief Upgrade command argv installing the latest tagged GitHub release via git.
- @details Executed for `--upgrade --dev`; bypasses PyPI.
- @satisfies DES-081 REQ-063
- var `UNINSTALL = ["uv", "tool", "uninstall", "cli-skills"]` (L30)
- var `SKILLS_INSTALL = ["cli-skills", "install"]` (L31)
### fn `def cache_path() -> Path` (L61-64)
- @brief Child `cli-skills install` command executed after a successful upgrade.
- @details Spawned by `_post_upgrade_install` so the freshly upgraded package
installs its bundled skills into every enabled CLI.
- @satisfies REQ-043

### fn `def _human(timestamp: float | None) -> str | None` `priv` (L65-68)

### fn `def _version(value: str) -> tuple[int, int, int]` `priv` (L69-75)

### fn `def _http_json(url: str, accept: str) -> dict` `priv` (L76-93)
- @brief Perform one HTTP GET and parse the JSON response body.
- @details Sends a `cli-skills` User-Agent with the caller-supplied Accept header and enforces the hardcoded 2-second timeout. Network and protocol errors propagate to the caller.
- @param url {str} Absolute HTTP/HTTPS endpoint URL.
- @param accept {str} HTTP Accept header value.
- @return {Dict} Decoded top-level JSON object.
- @throws {OSError} On transport or HTTP errors, including 429 and 503.
- @throws {ValueError} When the response body is not valid JSON.
- @satisfies CTN-006 DES-042 DES-083

### fn `def fetch_pypi_latest() -> str` (L94-111)
- @brief Fetch the newest published version from the PyPI JSON API.
- @details Requests `PYPI_ENDPOINT`, reads `info.version`, and returns it trimmed. Any transport, HTTP, or payload-shape failure raises.
- @return {str} Newest PyPI version string.
- @throws {OSError} On transport or HTTP errors, including 429 and 503.
- @throws {ValueError} When the payload is not valid JSON or omits a non-empty string `info.version`.
- @throws {KeyError} When the payload omits `info.version`.
- @satisfies DES-042 REQ-002 REQ-003 REQ-059

### fn `def fetch_github_latest() -> str` (L112-134)
- @brief Fetch the newest GitHub release version in `x.y.z` form.
- @details Requests `ENDPOINT`, reads `tag_name`, and strips an optional `v` prefix. The returned release is the newest tagged GitHub release regardless of its source branch, matching the `--upgrade --dev` download source.
- @return {str} Newest GitHub release version as `x.y.z`.
- @throws {OSError} On transport or HTTP errors, including 429 and 503.
- @throws {ValueError} When the payload omits or holds an invalid `tag_name`.
- @throws {KeyError} When the payload omits `tag_name`.
- @satisfies DES-083 REQ-061 REQ-062 REQ-063

### fn `def _failure_reason(exc: Exception) -> str` `priv` (L135-158)
- @brief Normalize one release-fetch failure to a concise reason string.
- @details For `HTTPError`, decodes the error body as JSON and surfaces the API `message` field prefixed with `HTTP <code>`; this exposes GitHub rate-limit causes such as `API rate limit exceeded` that arrive with HTTP 404. Body decode failures fall back to `HTTP <code>`; non-HTTP errors return `str(exc)`. Complexity O(B) where B is the error-body byte length.
- @param exc {Exception} Failure raised by `_http_json` or its callers.
- @return {str} Human-readable reason identifying the actual error cause.
- @satisfies REQ-066

### fn `def check_version(force: bool = False) -> None` (L159-221)
- @brief Run the cached automatic release check against PyPI.
- @details Skips while the cached idle-time is valid unless `force` is set; otherwise fetches the newest PyPI version via `fetch_pypi_latest`, compares it with `__version__`, prints a bright-green available-versus-installed message when a newer version exists or a bright-red message for a failed or negative check, records last-success timestamps on success only, and writes the cache with a 3600-second (positive) or 86400-second (negative or failed) expiration.
- @param force {bool} Bypass the cached idle-time and perform the request.
- @return {None}
- @note Cache read/write and network failures are reported to stderr and do not raise.
- @satisfies REQ-001 REQ-002 REQ-003 REQ-004 REQ-005 REQ-016 REQ-017 REQ-018 REQ-019 REQ-020 REQ-021 REQ-022 REQ-023 REQ-059 CTN-006 CTN-007 CTN-008 DES-042 DES-043 DES-044 DES-045 DES-046

### fn `def _manage(command: list[str]) -> int` `priv` (L222-232)

### fn `def _post_upgrade_install(home: Path | None = None) -> int` `priv` (L233-257)
- @brief Install bundled resources through `cli-skills install` after a successful upgrade.
- @details Loads the user configuration and, when at least one CLI is enabled, spawns `cli-skills install` as a child process so the freshly upgraded package synchronizes its bundled skills into every enabled CLI. Skips the child process when the enabled configuration is empty. The child reads the upgraded package resources, not the running process ones. The child inherits stdout, so its per-CLI count and installed-name report surfaces as visible `--upgrade` output.
- @param home {Path | None} Optional home-directory override used only for the configuration read; the child process inherits the real environment.
- @return {int} 0 when no CLI is enabled; otherwise the `cli-skills install` exit code (1 on spawn or installation failure).
- @throws {OSError} When reading the configuration file fails.
- @satisfies REQ-043 REQ-044 REQ-046 REQ-058

### fn `def _run_upgrade(command: list[str]) -> int` `priv` (L258-276)
- @brief Execute one upgrade command and chain the post-upgrade install.
- @details Delegates to `_manage` and, on a zero exit code under Linux, chains `_post_upgrade_install` so the freshly upgraded package installs bundled resources into every enabled CLI. Used by both the PyPI `--upgrade` form and the GitHub `--upgrade --dev` form.
- @param command {list[str]} Upgrade command argv executed on Linux and printed as the manual command on other operating systems.
- @return {int} Upgrade exit code, or the chained `cli-skills install` exit code when the chained install executes.
- @satisfies REQ-010 REQ-011 REQ-012 REQ-043 REQ-044 REQ-045 REQ-046 REQ-063

### fn `def _unsupported(name: str) -> str` `priv` (L277-288)
- @brief Build an unsupported-CLI diagnostic message.
- @details Lists the canonical CLI names accepted by the adapter registry in alphabetical order.
- @param name {str} Unsupported CLI name from the command line.
- @return {str} Human-readable diagnostic message.
- @satisfies REQ-026 DES-092

### fn `def _enable(name: str, home: Path | None = None) -> int` `priv` (L289-314)
- @brief Enable resource installation for one supported CLI.
- @details Resolves the CLI adapter, loads the user configuration, appends the canonical CLI name when absent, and persists the configuration. Re-enabling an enabled CLI leaves configuration unchanged.
- @param name {str} CLI name from the command line.
- @param home {Path | None} Optional home-directory override.
- @return {int} Exit code: 0 on success; 2 for an unsupported CLI.
- @throws {OSError} When saving the configuration file fails.
- @satisfies REQ-024 REQ-026 REQ-027 REQ-028

### fn `def _disable(name: str, home: Path | None = None) -> int` `priv` (L315-341)
- @brief Disable resource installation for one supported CLI.
- @details Resolves the CLI adapter, loads the user configuration, removes the canonical CLI name when present, and persists the configuration. Disabling an already disabled CLI is a successful no-op.
- @param name {str} CLI name from the command line.
- @param home {Path | None} Optional home-directory override.
- @return {int} Exit code: 0 on success; 2 for an unsupported CLI.
- @throws {OSError} When saving the configuration file fails.
- @satisfies REQ-025 REQ-026 REQ-027 REQ-028

### fn `def _install(home: Path | None = None) -> int` `priv` (L342-365)
- @brief Install bundled resources for all enabled CLIs.
- @details Delegates installation to `install_enabled`, prints per-CLI installed skill counts plus the installed skill names, prints an informational message when no CLI is enabled, and reports collected failures.
- @param home {Path | None} Optional home-directory override.
- @return {int} Exit code: 0 when no failure occurs; 1 when any failure occurs.
- @satisfies REQ-029 REQ-030 REQ-031 REQ-032 REQ-057

### fn `def _uninstall(home: Path | None = None) -> int` `priv` (L366-387)
- @brief Remove installed bundled resources for all enabled CLIs.
- @details Delegates uninstallation to `uninstall_enabled`, prints per-CLI removed skill counts, prints an informational message when no CLI is enabled, and reports collected failures.
- @param home {Path | None} Optional home-directory override.
- @return {int} Exit code: 0 when no failure occurs; 1 when any failure occurs.
- @satisfies REQ-047 REQ-054 REQ-055 REQ-056

### fn `def _show(home: Path | None = None) -> int` `priv` (L388-400)
- @brief Print packaged resources, CLI configuration, and installation status.
- @details Delegates report rendering to `build_show` and prints the result.
- @param home {Path | None} Optional home-directory override.
- @return {int} Exit code 0 after printing the report.
- @throws {OSError} When bundled resources or the configuration cannot be read.
- @satisfies REQ-037 REQ-038 REQ-039 REQ-042

### fn `def main(argv: list[str] | None = None) -> int` (L401-479)
- @brief Run the automatic release check and dispatch one CLI command.
- @details Executes `check_version` before argument parsing (forced by `--ver` or `--version`), then routes to help, version, management, enable/disable, install, uninstall, or show handlers. The `--upgrade` branch with or without `--dev` chains `cli-skills install` after a successful Linux upgrade when the enabled configuration is non-empty and returns the chained exit code. The `--ver` and `--version` branch prints the installed version plus the PyPI and GitHub latest-version lines, printing `GitHub latest: unknown (<reason>)` with the normalized failure reason when the GitHub request fails.
- @param argv {list[str] | None} Command-line arguments; defaults to `sys.argv[1:]`.
- @return {int} Process exit code: 0 on success; 1 on upgrade or install failure; 2 on usage errors.
- @satisfies REQ-006 REQ-007 REQ-008 REQ-009 REQ-010 REQ-011 REQ-012 REQ-013 REQ-014 REQ-015 REQ-024 REQ-025 REQ-026 REQ-029 REQ-030 REQ-031 REQ-032 REQ-037 REQ-042 REQ-043 REQ-044 REQ-045 REQ-046 REQ-047 REQ-054 REQ-055 REQ-056 REQ-057 REQ-058 REQ-059 REQ-060 REQ-061 REQ-062 REQ-063 REQ-064 REQ-065 REQ-066 DES-089

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PYPI_ENDPOINT`|var|pub|23||
|`ENDPOINT`|var|pub|24||
|`UPGRADE`|var|pub|25||
|`UPGRADE_DEVELOP`|var|pub|29||
|`UNINSTALL`|var|pub|30||
|`SKILLS_INSTALL`|var|pub|31||
|`cache_path`|fn|pub|61-64|def cache_path() -> Path|
|`_human`|fn|priv|65-68|def _human(timestamp: float | None) -> str | None|
|`_version`|fn|priv|69-75|def _version(value: str) -> tuple[int, int, int]|
|`_http_json`|fn|priv|76-93|def _http_json(url: str, accept: str) -> dict|
|`fetch_pypi_latest`|fn|pub|94-111|def fetch_pypi_latest() -> str|
|`fetch_github_latest`|fn|pub|112-134|def fetch_github_latest() -> str|
|`_failure_reason`|fn|priv|135-158|def _failure_reason(exc: Exception) -> str|
|`check_version`|fn|pub|159-221|def check_version(force: bool = False) -> None|
|`_manage`|fn|priv|222-232|def _manage(command: list[str]) -> int|
|`_post_upgrade_install`|fn|priv|233-257|def _post_upgrade_install(home: Path | None = None) -> int|
|`_run_upgrade`|fn|priv|258-276|def _run_upgrade(command: list[str]) -> int|
|`_unsupported`|fn|priv|277-288|def _unsupported(name: str) -> str|
|`_enable`|fn|priv|289-314|def _enable(name: str, home: Path | None = None) -> int|
|`_disable`|fn|priv|315-341|def _disable(name: str, home: Path | None = None) -> int|
|`_install`|fn|priv|342-365|def _install(home: Path | None = None) -> int|
|`_uninstall`|fn|priv|366-387|def _uninstall(home: Path | None = None) -> int|
|`_show`|fn|priv|388-400|def _show(home: Path | None = None) -> int|
|`main`|fn|pub|401-479|def main(argv: list[str] | None = None) -> int|


---

# installer.py | Python | 215L | 8 symbols | 7 imports | 14 comments
> Path: `src/cli_skills/installer.py`
- @brief Orchestrate skill installation for enabled CLI targets.
- @details Builds the bundled resource catalog, resolves manifest skill
directories, invokes the configured CLI adapters, and aggregates
per-CLI outcomes for installation and uninstallation. Rejects a
non-canonical skill support layout through the catalog builder.
- @satisfies PRJ-009 PRJ-011 REQ-029 REQ-030 REQ-032 REQ-035 REQ-047 REQ-048 REQ-051 REQ-052 REQ-053 REQ-056 DES-055 DES-062 DES-064 DES-073

## Imports
```
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from .catalog import RESOURCES_ROOT, SkillLayoutError, build_catalog
from .settings import load_config
from .targets import CliTarget, resolve_target
```

## Definitions

### class `class InstallError(RuntimeError)` : RuntimeError (L22-30)
- @brief Signal a manifest or packaged-resource installation failure.
- @details Raised when a manifest-listed source path is missing, duplicated, or otherwise not installable.
- @satisfies REQ-035

### class `class InstallSummary` `@dataclass(frozen=True)` (L32-47)
- @brief Summarize one CLI installation result.
- @details Carries the canonical CLI name, installed skill count, and sorted installed skill directory names for reporting.
- @satisfies REQ-030 REQ-057

### class `class UninstallSummary` `@dataclass(frozen=True)` (L49-62)
- @brief Summarize one CLI uninstallation result.
- @details Carries the canonical CLI name and processed manifest skill directory count. Missing destinations count as removed.
- @satisfies REQ-054

### fn `def _skill_directories(` `priv` (L63-65)

### fn `def install_target(` (L93-97)
- @brief Resolve manifest skill entries to packaged skill directories.
- @details Validates each entry file path, deduplicates by directory name, and
returns directories sorted by name.
- @param resources_root {Path} Resources root directory.
- @param entries {Iterable[dict[str, str]]} Manifest skill entries.
- @return {list[Path]} Sorted unique skill directories.
- @throws {InstallError} When a manifest-listed skill file or directory is
missing.
- @satisfies DES-055 DES-062 REQ-035

### fn `def install_enabled(` (L121-122)
- @brief Install manifest skills for one CLI target.
- @details Resolves manifest skill directories and delegates skill-tree
synchronization to the adapter.
- @param target {CliTarget} CLI adapter to install.
- @param catalog {dict[str, list[dict[str, str]]]} Manifest catalog.
- @param resources_root {Path} Resources root directory.
- @param home {Path | None} Optional home-directory override.
- @return {InstallSummary} Installed skill count and names.
- @throws {InstallError} When a manifest-listed source path is missing.
- @throws {OSError} When copying, pruning, or directory creation fails.
- @satisfies REQ-029 REQ-030 REQ-057 DES-055 DES-056 DES-057 DES-062

### fn `def uninstall_target(` (L155-159)
- @brief Install bundled resources for every enabled CLI.
- @details Loads user configuration and builds the resource catalog once.
Processes each enabled CLI independently and collects failures
without stopping remaining CLI processing.
- @param home {Path | None} Optional home-directory override.
- @return {tuple[list[InstallSummary], list[str]]} Installation summaries and
failure diagnostics; both empty when no CLI is enabled.
- @satisfies REQ-029 REQ-030 REQ-031 REQ-032 DES-064 DES-073

### fn `def uninstall_enabled(` (L184-185)
- @brief Remove manifest skills for one CLI target.
- @details Resolves manifest skill directory names and delegates deletion to
the adapter removal method. Missing destinations count as removed.
Destination entries outside manifest skill names are preserved.
- @param target {CliTarget} CLI adapter to clean.
- @param catalog {dict[str, list[dict[str, str]]]} Manifest catalog.
- @param resources_root {Path} Resources root directory.
- @param home {Path | None} Optional home-directory override.
- @return {UninstallSummary} Removed skill count.
- @throws {InstallError} When a manifest-listed source path is missing.
- @throws {OSError} When destination deletion fails.
- @satisfies REQ-047 REQ-048 REQ-051 REQ-052

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`InstallError`|class|pub|22-30|class InstallError(RuntimeError)|
|`InstallSummary`|class|pub|32-47|class InstallSummary|
|`UninstallSummary`|class|pub|49-62|class UninstallSummary|
|`_skill_directories`|fn|priv|63-65|def _skill_directories(|
|`install_target`|fn|pub|93-97|def install_target(|
|`install_enabled`|fn|pub|121-122|def install_enabled(|
|`uninstall_target`|fn|pub|155-159|def uninstall_target(|
|`uninstall_enabled`|fn|pub|184-185|def uninstall_enabled(|


---

# settings.py | Python | 98L | 5 symbols | 4 imports | 8 comments
> Path: `src/cli_skills/settings.py`
- @brief Persist enabled CLI targets.
- @details User configuration is a JSON object stored at
`$HOME/.config/cli-skills/config.json` with the schema
`{"enabled": ["<cli>", ...]}`.
Loading tolerates missing, unreadable, or malformed content by
returning normalized defaults.
- @satisfies DES-047 DES-048

## Imports
```
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
```

## Definitions

- var `CONFIG_RELATIVE = Path(".config") / "cli-skills" / "config.json"` (L21)
- @brief Configuration path relative to the user home directory.
- @details `$HOME` + `.config/cli-skills/config.json`.
- @satisfies DES-047
### fn `def config_path(home: Path | None = None) -> Path` (L24-35)
- @brief Resolve the user configuration file path.
- @details Joins the effective home directory with `.config/cli-skills/config.json`.
- @param home {Path | None} Optional home-directory override.
- @return {Path} Configuration file path.
- @satisfies DES-047

### fn `def _unique_strings(value: Any) -> list[str]` `priv` (L36-55)
- @brief Filter an arbitrary JSON value into unique non-empty strings.
- @details Preserves first-seen order and drops non-string, empty, and duplicate entries.
- @param value {Any} Candidate JSON value.
- @return {list[str]} Unique strings in first-seen order; empty for non-list input. @complexity O(n) where n is the list length.
- @satisfies DES-048

### fn `def load_config(home: Path | None = None) -> dict[str, Any]` (L56-76)
- @brief Load the user configuration with normalized defaults.
- @details Reads JSON from `config_path`. Missing, unreadable, non-object, or malformed content yields `{"enabled": []}`. Valid `enabled` entries are unique strings.
- @param home {Path | None} Optional home-directory override.
- @return {dict[str, Any]} Normalized configuration object.
- @note Read and decode errors are handled internally and are not raised.
- @satisfies DES-047 DES-048

### fn `def save_config(config: dict[str, Any], home: Path | None = None) -> Path` (L77-99)
- @brief Persist normalized configuration to the user configuration file.
- @details Creates parent directories, serializes with two-space indentation and a trailing newline, writes a sibling temporary file, then replaces the configuration file atomically.
- @param config {dict[str, Any]} Configuration object to persist.
- @param home {Path | None} Optional home-directory override.
- @return {Path} Written configuration file path.
- @throws {OSError} When directory creation or file writing fails.
- @satisfies DES-047 DES-048
- @post The configuration file contains the serialized `config` object.

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`CONFIG_RELATIVE`|var|pub|21||
|`config_path`|fn|pub|24-35|def config_path(home: Path | None = None) -> Path|
|`_unique_strings`|fn|priv|36-55|def _unique_strings(value: Any) -> list[str]|
|`load_config`|fn|pub|56-76|def load_config(home: Path | None = None) -> dict[str, Any]|
|`save_config`|fn|pub|77-99|def save_config(config: dict[str, Any], home: Path | None...|


---

# show.py | Python | 289L | 14 symbols | 6 imports | 13 comments
> Path: `src/cli_skills/show.py`
- @brief Render packaged resource inventory, CLI configuration, and installation status.
- @details Builds three deterministic box-drawing-bordered tables: bundled skills from
the manifest, every supported CLI with enabled state and home-relative
skills path, and a per-skill per-enabled-CLI installation status
derived from destination-directory scans.
- @satisfies DES-065 DES-066 REQ-037 REQ-038 REQ-039 REQ-040

## Imports
```
from __future__ import annotations
from pathlib import Path
from typing import Any, Iterable, Sequence
from .catalog import RESOURCES_ROOT, build_catalog
from .settings import load_config
from .targets import TARGETS, resolve_home
```

## Definitions

- var `MAX_CELL_WIDTH = 48` (L21)
- @brief Maximum rendered width of one table cell in characters.
- var `STATUS_OK = "OK"` (L23)
- @brief Status value for a resource whose destination files match the package.
- var `STATUS_MISSING = "MISSING"` (L25)
- @brief Status value for a resource with missing destination directories or files.
- var `STATUS_STALE = "STALE"` (L27)
- @brief Status value for a resource whose destination files differ from the package.
### fn `def _wrap(text: str, width: int) -> list[str]` `priv` (L30-63)
- @brief Wrap one cell value into fixed-width lines on word boundaries.
- @details Collapses whitespace, splits overlong tokens into `width`-sized chunks, and greedily packs words without exceeding `width`.
- @param text {str} Cell value to wrap.
- @param width {int} Maximum line width in characters; MUST be positive.
- @return {list[str]} Rendered lines; `[""]` for an empty value.
- @satisfies DES-066

### fn `def render_table(` (L64-67)

### fn `def border(left: str, middle: str, right: str) -> str` (L90-92)
- @brief Render a box-drawing-bordered grid table with aligned and wrapped cells.
- @details Column widths are the longest cell capped by `max_width`; the
header opens with a `┌─┬┐` border and closes with an `├─┼┤`
separator, rows are emitted between `│` verticals, and the table
ends with a `└─┴┘` border. Multi-line cells are padded to the row
height.
- @param headers {Sequence[str]} Column header labels.
- @param rows {Iterable[Sequence[str]]} Row cell values; short rows are padded.
- @param max_width {int} Maximum column width in characters.
- @return {str} Rendered table text without trailing newline.
- @satisfies DES-066

### fn `def render(cells: Sequence[str]) -> list[str]` (L97-115)

### fn `def _resource_rows(` `priv` (L123-124)

### fn `def _cli_rows(` `priv` (L146-148)
- @brief Build inventory rows from manifest catalog entries.
- @details Emits skills preserving manifest entry order.
- @param catalog {dict[str, list[dict[str, str]]]} Manifest catalog.
- @return {list[tuple[str, str, str, str]]} `(type, name, file, description)` rows.
- @satisfies REQ-037

### fn `def _files_match(source: Path, destination: Path) -> str` `priv` (L173-191)
- @brief Build CLI configuration rows from the adapter registry.
- @brief Compare one packaged file with its installed destination file.
- @details Reports alphabetical registry order, enabled state, and the
home-relative skills destination.
- @param config {dict[str, object]} Normalized user configuration.
- @param home {Path | None} Optional home-directory override.
- @param source {Path} Packaged file path.
- @param destination {Path} Installed destination file path.
- @return {list[tuple[str, str, str]]} `(cli, enabled, skills path)` rows.
- @return {str} `OK` for identical bytes, `MISSING` for absent destination, `STALE` for differing bytes or unreadable content.
- @satisfies REQ-038 DES-092
- @satisfies REQ-040

### fn `def _skill_status(source: Path, destination: Path) -> str` `priv` (L192-215)
- @brief Compare a packaged skill directory with its installed copy.
- @details Every packaged regular file must exist in the destination with identical bytes.
- @param source {Path} Packaged skill directory.
- @param destination {Path} Installed skill destination directory.
- @return {str} `OK` when all files match; `MISSING` when the package or a destination file is absent; `STALE` on content mismatch.
- @satisfies REQ-040

### fn `def _install_rows(` `priv` (L216-219)

### fn `def build_show(home: Path | None = None) -> str` (L256-290)
- @brief Build per-skill per-enabled-CLI installation status rows.
- @brief Build the complete `show` report text.
- @details Scans adapter destination directories for each manifest skill
and emits rows only for CLIs present in the enabled
configuration.
- @details Renders the packaged-resource inventory, CLI configuration, and installation status tables in this order.
- @param catalog {dict[str, list[dict[str, str]]]} Manifest catalog.
- @param config {dict[str, object]} Normalized user configuration.
- @param home {Path | None} Optional home-directory override.
- @param home {Path | None} Optional home-directory override for deterministic destination resolution.
- @return {list[tuple[str, str, str, str, str]]} `(type, name, cli, enabled,
installed)` rows.
- @return {str} Report text with three titled tables separated by blank lines.
- @throws {OSError} When the manifest or bundled resources cannot be read.
- @satisfies REQ-039 REQ-040
- @satisfies DES-065 REQ-037 REQ-038 REQ-039 REQ-042

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`MAX_CELL_WIDTH`|var|pub|21||
|`STATUS_OK`|var|pub|23||
|`STATUS_MISSING`|var|pub|25||
|`STATUS_STALE`|var|pub|27||
|`_wrap`|fn|priv|30-63|def _wrap(text: str, width: int) -> list[str]|
|`render_table`|fn|pub|64-67|def render_table(|
|`border`|fn|pub|90-92|def border(left: str, middle: str, right: str) -> str|
|`render`|fn|pub|97-115|def render(cells: Sequence[str]) -> list[str]|
|`_resource_rows`|fn|priv|123-124|def _resource_rows(|
|`_cli_rows`|fn|priv|146-148|def _cli_rows(|
|`_files_match`|fn|priv|173-191|def _files_match(source: Path, destination: Path) -> str|
|`_skill_status`|fn|priv|192-215|def _skill_status(source: Path, destination: Path) -> str|
|`_install_rows`|fn|priv|216-219|def _install_rows(|
|`build_show`|fn|pub|256-290|def build_show(home: Path | None = None) -> str|


---

# targets.py | Python | 293L | 21 symbols | 5 imports | 27 comments
> Path: `src/cli_skills/targets.py`
- @brief Provide per-CLI skill installation adapters.
- @details Defines the `CliTarget` abstraction and one concrete adapter for each
supported CLI: `antigravity`, `claude`, `codex`, `copilot`, `opencode`,
`openclaw`, and `pi`.
Adapters resolve user-level skill destination directories from a home
root and provide deterministic copy algorithms for skills.
Shared copy primitives synchronize packaged trees, overwrite changed
files, and prune destination entries absent from the package.
Removal primitives delete managed skill directories while preserving
unmanaged destination entries.
- @satisfies PRJ-010 PRJ-011 DES-049 DES-050 DES-051 DES-052 DES-053 DES-054 DES-090 DES-091 DES-092 DES-055 DES-056 DES-057 DES-058 DES-063 REQ-048 REQ-051 REQ-052

## Imports
```
from __future__ import annotations
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable
```

## Definitions

### fn `def resolve_home(home: Path | None) -> Path` (L24-36)
- @brief Resolve the user home directory used for destination paths.
- @details Returns the explicit override when provided; otherwise resolves `Path.home()`. Centralizes home resolution for deterministic tests and adapter reuse.
- @param home {Path | None} Optional home-directory override.
- @return {Path} Effective home directory path.
- @satisfies DES-049

### fn `def sync_skill_tree(source: Path, destination: Path) -> None` (L37-69)
- @brief Replace a destination skill directory with packaged contents.
- @details Copies the source tree recursively with overwrite, then removes destination files and directories absent from the source tree. Destination skill files become byte-identical copies of package files. Pruning runs deepest-first to keep directory removal safe.
- @param source {Path} Packaged skill directory containing `SKILL.md`.
- @param destination {Path} Target skill directory named after `source.name`.
- @return {None}
- @throws {OSError} When directory creation, copying, or pruning fails.
- @satisfies DES-055 DES-056 DES-057 DES-063
- @pre `source` MUST be an existing directory.
- @post `destination` contains exactly the source tree paths and contents. @complexity O(S + D) where S is source entries and D is destination entries.

### class `class CliTarget(ABC)` : ABC (L70-132)
- @brief Abstract adapter for a supported CLI installation target.
- @details Subclasses declare the CLI name and resolve the user-level skill destination directory. Base methods implement deterministic skill-tree synchronization and managed skill removal.
- @satisfies DES-049 REQ-048
- fn `def skills_dir(self, home: Path | None = None) -> Path` (L83-90)
  - @brief Resolve the CLI user-level skills destination directory.
  - @param home {Path | None} Optional home-directory override.
  - @return {Path} Skills destination directory.
  - @satisfies DES-050 DES-051 DES-052 DES-053 DES-054
- fn `def install_skills(self, sources: Iterable[Path], home: Path | None = None) -> int` (L91-108)
  - @brief Install packaged skill directories into this CLI destination.
  - @details Synchronizes each source directory into `<skills_dir>/<source.name>` using `sync_skill_tree`.
  - @param sources {Iterable[Path]} Packaged skill directories.
  - @param home {Path | None} Optional home-directory override.
  - @return {int} Number of processed skill directories.
  - @throws {OSError} When synchronization fails.
  - @satisfies DES-055 DES-056 DES-057 DES-063
- fn `def remove_skills(self, names: Iterable[str], home: Path | None = None) -> int` (L109-132)
  - @brief Remove managed skill directories from this CLI destination.
  - @details Deletes `<skills_dir>/<name>` recursively for each name. Missing destinations count as removed and do not raise. Destination entries outside `names` are preserved and no directory is created. Complexity O(N) deletions where N is the number of names.
  - @param names {Iterable[str]} Managed skill directory names.
  - @param home {Path | None} Optional home-directory override.
  - @return {int} Number of processed names; missing destinations count as removed.
  - @throws {OSError} When recursive directory deletion fails.
  - @satisfies REQ-048 REQ-051 REQ-052

### class `class PiTarget(CliTarget)` : CliTarget (L133-151)
- @brief Installation adapter for the `pi` coding agent.
- @details Installs skills under `$HOME/.pi/agent/skills`.
- @satisfies DES-050
- fn `def skills_dir(self, home: Path | None = None) -> Path` (L142-151)
  - @brief Installation adapter for the `pi` coding agent.
  - @brief Resolve the pi user-level skills directory.
  - @details Installs skills under `$HOME/.pi/agent/skills`.
  - @param home {Path | None} Optional home-directory override.
  - @return {Path} `$HOME/.pi/agent/skills`.
  - @satisfies DES-050
  - @satisfies DES-050

### class `class OpenClawTarget(CliTarget)` : CliTarget (L152-170)
- @brief Installation adapter for the `openclaw` agent workspace.
- @details Installs skills under `$HOME/.openclaw/workspace/skills`.
- @satisfies DES-051
- fn `def skills_dir(self, home: Path | None = None) -> Path` (L161-170)
  - @brief Installation adapter for the `openclaw` agent workspace.
  - @brief Resolve the openclaw user-level skills directory.
  - @details Installs skills under `$HOME/.openclaw/workspace/skills`.
  - @param home {Path | None} Optional home-directory override.
  - @return {Path} `$HOME/.openclaw/workspace/skills`.
  - @satisfies DES-051
  - @satisfies DES-051

### class `class CodexTarget(CliTarget)` : CliTarget (L171-189)
- @brief Installation adapter for the `codex` CLI.
- @details Installs skills under `$HOME/.codex/skills`.
- @satisfies DES-052
- fn `def skills_dir(self, home: Path | None = None) -> Path` (L180-189)
  - @brief Installation adapter for the `codex` CLI.
  - @brief Resolve the codex user-level skills directory.
  - @details Installs skills under `$HOME/.codex/skills`.
  - @param home {Path | None} Optional home-directory override.
  - @return {Path} `$HOME/.codex/skills`.
  - @satisfies DES-052
  - @satisfies DES-052

### class `class CopilotTarget(CliTarget)` : CliTarget (L190-208)
- @brief Installation adapter for the `copilot` CLI.
- @details Installs skills under `$HOME/.copilot/skills`.
- @satisfies DES-091
- fn `def skills_dir(self, home: Path | None = None) -> Path` (L199-208)
  - @brief Installation adapter for the `copilot` CLI.
  - @brief Resolve the copilot user-level skills directory.
  - @details Installs skills under `$HOME/.copilot/skills`.
  - @param home {Path | None} Optional home-directory override.
  - @return {Path} `$HOME/.copilot/skills`.
  - @satisfies DES-091
  - @satisfies DES-091

### class `class AntigravityTarget(CliTarget)` : CliTarget (L209-227)
- @brief Installation adapter for Google Antigravity.
- @details Installs skills under `$HOME/.gemini/config/skills`.
- @satisfies DES-053
- fn `def skills_dir(self, home: Path | None = None) -> Path` (L218-227)
  - @brief Installation adapter for Google Antigravity.
  - @brief Resolve the antigravity user-level skills directory.
  - @details Installs skills under `$HOME/.gemini/config/skills`.
  - @param home {Path | None} Optional home-directory override.
  - @return {Path} `$HOME/.gemini/config/skills`.
  - @satisfies DES-053
  - @satisfies DES-053

### class `class OpenCodeTarget(CliTarget)` : CliTarget (L228-246)
- @brief Installation adapter for the `opencode` CLI.
- @details Installs skills under `$HOME/.config/opencode/skills`.
- @satisfies DES-090
- fn `def skills_dir(self, home: Path | None = None) -> Path` (L237-246)
  - @brief Installation adapter for the `opencode` CLI.
  - @brief Resolve the opencode user-level skills directory.
  - @details Installs skills under `$HOME/.config/opencode/skills`.
  - @param home {Path | None} Optional home-directory override.
  - @return {Path} `$HOME/.config/opencode/skills`.
  - @satisfies DES-090
  - @satisfies DES-090

### class `class ClaudeTarget(CliTarget)` : CliTarget (L247-265)
- @brief Installation adapter for the `claude` CLI.
- @details Installs skills under `$HOME/.claude/skills`.
- @satisfies DES-054
- fn `def skills_dir(self, home: Path | None = None) -> Path` (L256-265)
  - @brief Installation adapter for the `claude` CLI.
  - @brief Resolve the claude user-level skills directory.
  - @details Installs skills under `$HOME/.claude/skills`.
  - @param home {Path | None} Optional home-directory override.
  - @return {Path} `$HOME/.claude/skills`.
  - @satisfies DES-054
  - @satisfies DES-054

### fn `def resolve_target(name: str) -> CliTarget | None` (L284-294)
- @brief Registry of supported CLI adapters keyed by canonical CLI name.
- @brief Resolve a CLI adapter by canonical name.
- @details Alphabetical key order defines the supported-name listing in
diagnostics and `show` tables.
- @details Trims surrounding whitespace and lowercases the input before a registry lookup.
- @param name {str} CLI name supplied on the command line.
- @return {CliTarget | None} Matching adapter; `None` when unsupported.
- @satisfies DES-049 DES-092
- @satisfies REQ-026

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`resolve_home`|fn|pub|24-36|def resolve_home(home: Path | None) -> Path|
|`sync_skill_tree`|fn|pub|37-69|def sync_skill_tree(source: Path, destination: Path) -> None|
|`CliTarget`|class|pub|70-132|class CliTarget(ABC)|
|`CliTarget.skills_dir`|fn|pub|83-90|def skills_dir(self, home: Path | None = None) -> Path|
|`CliTarget.install_skills`|fn|pub|91-108|def install_skills(self, sources: Iterable[Path], home: P...|
|`CliTarget.remove_skills`|fn|pub|109-132|def remove_skills(self, names: Iterable[str], home: Path ...|
|`PiTarget`|class|pub|133-151|class PiTarget(CliTarget)|
|`PiTarget.skills_dir`|fn|pub|142-151|def skills_dir(self, home: Path | None = None) -> Path|
|`OpenClawTarget`|class|pub|152-170|class OpenClawTarget(CliTarget)|
|`OpenClawTarget.skills_dir`|fn|pub|161-170|def skills_dir(self, home: Path | None = None) -> Path|
|`CodexTarget`|class|pub|171-189|class CodexTarget(CliTarget)|
|`CodexTarget.skills_dir`|fn|pub|180-189|def skills_dir(self, home: Path | None = None) -> Path|
|`CopilotTarget`|class|pub|190-208|class CopilotTarget(CliTarget)|
|`CopilotTarget.skills_dir`|fn|pub|199-208|def skills_dir(self, home: Path | None = None) -> Path|
|`AntigravityTarget`|class|pub|209-227|class AntigravityTarget(CliTarget)|
|`AntigravityTarget.skills_dir`|fn|pub|218-227|def skills_dir(self, home: Path | None = None) -> Path|
|`OpenCodeTarget`|class|pub|228-246|class OpenCodeTarget(CliTarget)|
|`OpenCodeTarget.skills_dir`|fn|pub|237-246|def skills_dir(self, home: Path | None = None) -> Path|
|`ClaudeTarget`|class|pub|247-265|class ClaudeTarget(CliTarget)|
|`ClaudeTarget.skills_dir`|fn|pub|256-265|def skills_dir(self, home: Path | None = None) -> Path|
|`resolve_target`|fn|pub|284-294|def resolve_target(name: str) -> CliTarget | None|


---

# __init__.py | Python | 8L | 0 symbols | 0 imports | 1 comments
> Path: `src/resources/__init__.py`
- @brief Mark `resources` as the bundled skills distribution package.
- @details Provides an importable namespace for the `src/resources` data tree so
setuptools packages it with the `cli-skills` distribution and downstream
LLM agents can resolve bundled artifacts via `importlib.resources`.
- @satisfies PRJ-006 PRJ-007 DES-020

