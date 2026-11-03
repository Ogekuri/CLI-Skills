# Files Structure
```
.
└── src
    ├── resources
    │   └── __init__.py
    └── skills
        ├── __init__.py
        ├── __main__.py
        ├── catalog.py
        ├── core.py
        ├── installer.py
        ├── settings.py
        ├── show.py
        └── targets.py
```

# __init__.py | Python | 8L | 0 symbols | 0 imports | 1 comments
> Path: `src/resources/__init__.py`
- @brief Mark `resources` as the bundled skills and prompts distribution package.
- @details Provides an importable namespace for the `src/resources` data tree so
setuptools packages it with the `skills` distribution and downstream
LLM agents can resolve bundled artifacts via `importlib.resources`.
- @satisfies PRJ-006 PRJ-007 DES-020


---

# __init__.py | Python | 13L | 0 symbols | 1 imports | 7 comments
> Path: `src/skills/__init__.py`

## Imports
```
from .core import main  # noqa: F401
```


---

# __main__.py | Python | 11L | 0 symbols | 2 imports | 5 comments
> Path: `src/skills/__main__.py`

## Imports
```
from .core import main
import sys
```


---

# catalog.py | Python | 190L | 11 symbols | 4 imports | 12 comments
> Path: `src/skills/catalog.py`
- @brief Generate the skills and prompts manifest for `src/resources`.
- @details Deterministic generator for `src/resources/manifest.json`. Recursively
scans `src/resources/skills` for `SKILL.md` files and
`src/resources/prompts` for frontmatter files, extracts frontmatter
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

- var `RESOURCES_ROOT = Path(str(ires.files("resources")))` (L21)
- var `MANIFEST_PATH = RESOURCES_ROOT / "manifest.json"` (L22)
- var `SKILL_SUPPORT_DIRECTORIES = ("scripts", "references", "assets", "images")` (L25)
- @brief Canonical skill support subdirectory names allowed at the skill root.
- @details Any other root directory or non-`SKILL.md` root file violates DES-067.
- var `REFERENCE_SUPPORT_DIRECTORIES = ("images",)` (L28)
- @brief Canonical nested subdirectory names allowed directly under `references`.
- @details Any other nested directory under `references` violates DES-069 and DES-070.
### class `class SkillLayoutError(ValueError)` : ValueError (L31-40)
- @brief Signal a bundled skill layout that violates the canonical support layout.
- @details Raised by `validate_skill_layout` when a skill root contains an entry outside the canonical support subdirectories or when `references` contains a non-canonical subdirectory.
- @satisfies DES-073

### fn `def validate_skill_layout(skill_dir: Path) -> None` (L41-69)
- @brief Validate a bundled skill directory against the canonical support layout.
- @details Accepts `SKILL.md` plus the canonical support subdirectories at the skill root; accepts only `images` as a nested directory directly under `references`. Non-canonical root files and directories are rejected. Complexity O(E) where E is the number of root entries plus direct `references` entries.
- @param skill_dir {Path} Packaged skill directory containing `SKILL.md`.
- @return {None}
- @throws {SkillLayoutError} When a root entry or a nested `references` directory violates DES-067 through DES-072.
- @satisfies DES-067 DES-068 DES-069 DES-070 DES-071 DES-072 DES-073
- @pre `skill_dir` MUST be an existing directory.
- @post The directory layout is canonical or an exception is raised.

### fn `def _parse_frontmatter(text: str) -> dict[str, str]` `priv` (L70-102)
- @brief Parse `name` and `description` from a YAML frontmatter block.
- @details Reads key/value lines up to the closing `---` delimiter, strips surrounding YAML quotes from scalar values, and returns only the `name` and `description` keys when present.
- @param text {str} Raw file text (UTF-8).
- @return {Dict[str, str]} Frontmatter `name`/`description` mapping; empty when the block or keys are absent.
- @pre `text` must be a non-empty string.

### fn `def _discover_skills(root: Path) -> list[Path]` `priv` (L103-115)
- @brief Discover `SKILL.md` files under `root/skills`.
- @details Recursively collects every file named `SKILL.md`, sorted by path.
- @param root {Path} Resources root directory.
- @return {List[Path]} Sorted `SKILL.md` file paths.

### fn `def _discover_prompts(root: Path) -> list[Path]` `priv` (L116-129)
- @brief Discover candidate prompt files under `root/prompts`.
- @details Recursively collects every regular file, sorted by path. Frontmatter filtering is applied by `build_catalog`.
- @param root {Path} Resources root directory.
- @return {List[Path]} Sorted candidate prompt file paths.

### fn `def build_catalog(` (L130-131)

### fn `def write_catalog(` (L171-173)
- @brief Build the skills and prompts catalog dictionary.
- @details Validates each skill directory layout, then scans skills and prompts
directories, extracts frontmatter metadata, and emits entries
sorted by relative path. Entries missing `name` or `description`
are omitted.
- @param resources_root {Path} Resources root directory to scan.
- @return {Dict[str, List[Dict[str, str]]]} Catalog with `skills` and
`prompts` lists; each entry contains `file`, `name`, `description`.
- @throws {SkillLayoutError} When a discovered skill directory violates the
canonical support layout.
- @satisfies DES-021 DES-022 DES-023 DES-024 DES-067 DES-068 DES-069 DES-070 DES-071 DES-072 DES-073

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`RESOURCES_ROOT`|var|pub|21||
|`MANIFEST_PATH`|var|pub|22||
|`SKILL_SUPPORT_DIRECTORIES`|var|pub|25||
|`REFERENCE_SUPPORT_DIRECTORIES`|var|pub|28||
|`SkillLayoutError`|class|pub|31-40|class SkillLayoutError(ValueError)|
|`validate_skill_layout`|fn|pub|41-69|def validate_skill_layout(skill_dir: Path) -> None|
|`_parse_frontmatter`|fn|priv|70-102|def _parse_frontmatter(text: str) -> dict[str, str]|
|`_discover_skills`|fn|priv|103-115|def _discover_skills(root: Path) -> list[Path]|
|`_discover_prompts`|fn|priv|116-129|def _discover_prompts(root: Path) -> list[Path]|
|`build_catalog`|fn|pub|130-131|def build_catalog(|
|`write_catalog`|fn|pub|171-173|def write_catalog(|


---

# core.py | Python | 347L | 17 symbols | 14 imports | 11 comments
> Path: `src/skills/core.py`

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
from urllib.request import Request, urlopen
from . import __version__
from .installer import install_enabled, uninstall_enabled
from .settings import load_config, save_config
from .show import build_show
from .targets import TARGETS, resolve_target
```

## Definitions

- var `ENDPOINT = "https://api.github.com/repos/Ogekuri/SKILLs/releases/latest"` (L20)
- var `UPGRADE = ["uv", "tool", "install", "skills", "--force", "--from", "git+https://github.com/Ogekuri/SKILLs.git"]` (L21)
- var `UNINSTALL = ["uv", "tool", "uninstall", "skills"]` (L22)
- var `SKILLS_INSTALL = ["skills", "install"]` (L23)
### fn `def cache_path() -> Path` (L52-55)
- @brief Child `skills install` command executed after a successful upgrade.
- @details Spawned by `_post_upgrade_install` so the freshly upgraded package
installs its bundled skills and prompts into every enabled CLI.
- @satisfies REQ-043

### fn `def _human(timestamp: float | None) -> str | None` `priv` (L56-59)

### fn `def _version(value: str) -> tuple[int, int, int]` `priv` (L60-66)

### fn `def check_version(force: bool = False) -> None` (L67-114)

### fn `def _manage(command: list[str]) -> int` `priv` (L115-125)

### fn `def _post_upgrade_install(home: Path | None = None) -> int` `priv` (L126-150)
- @brief Install bundled resources through `skills install` after a successful upgrade.
- @details Loads the user configuration and, when at least one CLI is enabled, spawns `skills install` as a child process so the freshly upgraded package synchronizes its bundled skills and prompts into every enabled CLI. Skips the child process when the enabled configuration is empty. The child reads the upgraded package resources, not the running process ones. The child inherits stdout, so its per-CLI count and installed-name report surfaces as visible `--upgrade` output.
- @param home {Path | None} Optional home-directory override used only for the configuration read; the child process inherits the real environment.
- @return {int} 0 when no CLI is enabled; otherwise the `skills install` exit code (1 on spawn or installation failure).
- @throws {OSError} When reading the configuration file fails.
- @satisfies REQ-043 REQ-044 REQ-046 REQ-058

### fn `def _unsupported(name: str) -> str` `priv` (L151-161)
- @brief Build an unsupported-CLI diagnostic message.
- @details Lists the canonical CLI names accepted by the adapter registry.
- @param name {str} Unsupported CLI name from the command line.
- @return {str} Human-readable diagnostic message.
- @satisfies REQ-026

### fn `def _enable(name: str, home: Path | None = None) -> int` `priv` (L162-187)
- @brief Enable resource installation for one supported CLI.
- @details Resolves the CLI adapter, loads the user configuration, appends the canonical CLI name when absent, and persists the configuration. Re-enabling an enabled CLI leaves configuration unchanged.
- @param name {str} CLI name from the command line.
- @param home {Path | None} Optional home-directory override.
- @return {int} Exit code: 0 on success; 2 for an unsupported CLI.
- @throws {OSError} When saving the configuration file fails.
- @satisfies REQ-024 REQ-026 REQ-027 REQ-028

### fn `def _disable(name: str, home: Path | None = None) -> int` `priv` (L188-214)
- @brief Disable resource installation for one supported CLI.
- @details Resolves the CLI adapter, loads the user configuration, removes the canonical CLI name when present, and persists the configuration. Disabling an already disabled CLI is a successful no-op.
- @param name {str} CLI name from the command line.
- @param home {Path | None} Optional home-directory override.
- @return {int} Exit code: 0 on success; 2 for an unsupported CLI.
- @throws {OSError} When saving the configuration file fails.
- @satisfies REQ-025 REQ-026 REQ-027 REQ-028

### fn `def _install(home: Path | None = None) -> int` `priv` (L215-244)
- @brief Install bundled resources for all enabled CLIs.
- @details Delegates installation to `install_enabled`, prints per-CLI skill and prompt counts plus the installed skill names and prompt filenames, prints an informational message when no CLI is enabled, and reports collected failures.
- @param home {Path | None} Optional home-directory override.
- @return {int} Exit code: 0 when no failure occurs; 1 when any failure occurs.
- @satisfies REQ-029 REQ-030 REQ-031 REQ-032 REQ-057

### fn `def _uninstall(home: Path | None = None) -> int` `priv` (L245-269)
- @brief Remove installed bundled resources for all enabled CLIs.
- @details Delegates uninstallation to `uninstall_enabled`, prints per-CLI removed skill and prompt counts, prints an informational message when no CLI is enabled, and reports collected failures.
- @param home {Path | None} Optional home-directory override.
- @return {int} Exit code: 0 when no failure occurs; 1 when any failure occurs.
- @satisfies REQ-047 REQ-054 REQ-055 REQ-056

### fn `def _show(home: Path | None = None) -> int` `priv` (L270-282)
- @brief Print packaged resources, CLI configuration, and installation status.
- @details Delegates report rendering to `build_show` and prints the result.
- @param home {Path | None} Optional home-directory override.
- @return {int} Exit code 0 after printing the report.
- @throws {OSError} When bundled resources or the configuration cannot be read.
- @satisfies REQ-037 REQ-038 REQ-039 REQ-042

### fn `def main(argv: list[str] | None = None) -> int` (L283-348)
- @brief Run the automatic release check and dispatch one CLI command.
- @details Executes `check_version` before argument parsing (forced by `--ver` or `--version`), then routes to help, version, management, enable/disable, install, uninstall, or show handlers. The `--upgrade` branch chains `skills install` after a successful Linux upgrade when the enabled configuration is non-empty and returns the chained exit code.
- @param argv {list[str] | None} Command-line arguments; defaults to `sys.argv[1:]`.
- @return {int} Process exit code: 0 on success; 1 on upgrade or install failure; 2 on usage errors.
- @satisfies REQ-006 REQ-007 REQ-008 REQ-009 REQ-010 REQ-011 REQ-012 REQ-013 REQ-014 REQ-015 REQ-024 REQ-025 REQ-026 REQ-029 REQ-030 REQ-031 REQ-032 REQ-037 REQ-042 REQ-043 REQ-044 REQ-045 REQ-046 REQ-047 REQ-054 REQ-055 REQ-056 REQ-057 REQ-058

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`ENDPOINT`|var|pub|20||
|`UPGRADE`|var|pub|21||
|`UNINSTALL`|var|pub|22||
|`SKILLS_INSTALL`|var|pub|23||
|`cache_path`|fn|pub|52-55|def cache_path() -> Path|
|`_human`|fn|priv|56-59|def _human(timestamp: float | None) -> str | None|
|`_version`|fn|priv|60-66|def _version(value: str) -> tuple[int, int, int]|
|`check_version`|fn|pub|67-114|def check_version(force: bool = False) -> None|
|`_manage`|fn|priv|115-125|def _manage(command: list[str]) -> int|
|`_post_upgrade_install`|fn|priv|126-150|def _post_upgrade_install(home: Path | None = None) -> int|
|`_unsupported`|fn|priv|151-161|def _unsupported(name: str) -> str|
|`_enable`|fn|priv|162-187|def _enable(name: str, home: Path | None = None) -> int|
|`_disable`|fn|priv|188-214|def _disable(name: str, home: Path | None = None) -> int|
|`_install`|fn|priv|215-244|def _install(home: Path | None = None) -> int|
|`_uninstall`|fn|priv|245-269|def _uninstall(home: Path | None = None) -> int|
|`_show`|fn|priv|270-282|def _show(home: Path | None = None) -> int|
|`main`|fn|pub|283-348|def main(argv: list[str] | None = None) -> int|


---

# installer.py | Python | 292L | 9 symbols | 7 imports | 18 comments
> Path: `src/skills/installer.py`
- @brief Orchestrate skill and prompt installation for enabled CLI targets.
- @details Builds the bundled resource catalog, resolves manifest skill
directories and prompt files, invokes the configured CLI adapters,
updates prompt records, and aggregates per-CLI outcomes for
installation and uninstallation. Rejects a non-canonical skill
support layout through the catalog builder.
- @satisfies PRJ-009 PRJ-011 REQ-029 REQ-030 REQ-032 REQ-035 REQ-047 REQ-048 REQ-049 REQ-050 REQ-051 REQ-052 REQ-053 REQ-056 DES-055 DES-059 DES-060 DES-061 DES-062 DES-064 DES-073

## Imports
```
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from .catalog import RESOURCES_ROOT, SkillLayoutError, build_catalog
from .settings import load_config, save_config
from .targets import CliTarget, resolve_target
```

## Definitions

### class `class InstallError(RuntimeError)` : RuntimeError (L23-31)
- @brief Signal a manifest or packaged-resource installation failure.
- @details Raised when a manifest-listed source path is missing, duplicated, or otherwise not installable.
- @satisfies REQ-035

### class `class InstallSummary` `@dataclass(frozen=True)` (L33-53)
- @brief Summarize one CLI installation result.
- @details Carries the canonical CLI name, installed skill count, sorted installed skill directory names, installed prompt count, and installed prompt filenames for persistence and reporting.
- @satisfies REQ-030 REQ-057 DES-060

### class `class UninstallSummary` `@dataclass(frozen=True)` (L55-71)
- @brief Summarize one CLI uninstallation result.
- @details Carries the canonical CLI name, processed manifest skill directory count, and processed managed prompt filename count. Missing destinations count as removed.
- @satisfies REQ-054

### fn `def _skill_directories(` `priv` (L72-74)

### fn `def _prompt_files(` `priv` (L102-104)
- @brief Resolve manifest skill entries to packaged skill directories.
- @details Validates each entry file path, deduplicates by directory name, and
returns directories sorted by name.
- @param resources_root {Path} Resources root directory.
- @param entries {Iterable[dict[str, str]]} Manifest skill entries.
- @return {list[Path]} Sorted unique skill directories.
- @throws {InstallError} When a manifest-listed skill file or directory is
missing.
- @satisfies DES-055 DES-062 REQ-035

### fn `def install_target(` (L133-138)
- @brief Resolve manifest prompt entries to packaged prompt files.
- @details Validates each entry file path and rejects duplicate destination
filenames that would overwrite each other.
- @param resources_root {Path} Resources root directory.
- @param entries {Iterable[dict[str, str]]} Manifest prompt entries.
- @return {list[Path]} Packaged prompt files sorted by relative path.
- @throws {InstallError} When a manifest-listed prompt file is missing or two
entries share the same destination filename.
- @satisfies DES-059 DES-062 REQ-035

### fn `def install_enabled(` (L168-169)
- @brief Install manifest skills and prompts for one CLI target.
- @details Resolves manifest sources, delegates skill synchronization and
prompt-file replacement to the adapter, and returns installed
counts and prompt filenames.
- @param target {CliTarget} CLI adapter to install.
- @param catalog {dict[str, list[dict[str, str]]]} Manifest catalog.
- @param previous_prompts {Iterable[str]} Previously installed prompt filenames.
- @param resources_root {Path} Resources root directory.
- @param home {Path | None} Optional home-directory override.
- @return {InstallSummary} Installed skill and prompt counts.
- @throws {InstallError} When a manifest-listed source path is missing.
- @throws {OSError} When copying, pruning, or directory creation fails.
- @satisfies REQ-029 REQ-030 REQ-057 DES-055 DES-056 DES-057 DES-059 DES-061 DES-062

### fn `def uninstall_target(` (L212-217)
- @brief Install bundled resources for every enabled CLI.
- @details Loads user configuration and builds the resource catalog once.
Processes each enabled CLI independently, persists prompt records
after each successful CLI, and collects failures without stopping
remaining CLI processing.
- @param home {Path | None} Optional home-directory override.
- @return {tuple[list[InstallSummary], list[str]]} Installation summaries and
failure diagnostics; both empty when no CLI is enabled.
- @satisfies REQ-029 REQ-030 REQ-031 REQ-032 DES-064 DES-073

### fn `def uninstall_enabled(` (L251-252)
- @brief Remove manifest skills and installed prompts for one CLI target.
- @details Resolves manifest skill directory names and the union of
manifest prompt filenames with previously recorded prompt
filenames, then delegates deletion to the adapter removal
methods. Missing destinations count as removed. Destination
entries outside manifest skill names and managed prompt names
are preserved.
- @param target {CliTarget} CLI adapter to clean.
- @param catalog {dict[str, list[dict[str, str]]]} Manifest catalog.
- @param recorded_prompts {Iterable[str]} Previously recorded prompt
filenames for this CLI.
- @param resources_root {Path} Resources root directory.
- @param home {Path | None} Optional home-directory override.
- @return {UninstallSummary} Removed skill and prompt counts.
- @throws {InstallError} When a manifest-listed source path is missing.
- @throws {OSError} When destination deletion fails.
- @satisfies REQ-047 REQ-048 REQ-049 REQ-051 REQ-052

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`InstallError`|class|pub|23-31|class InstallError(RuntimeError)|
|`InstallSummary`|class|pub|33-53|class InstallSummary|
|`UninstallSummary`|class|pub|55-71|class UninstallSummary|
|`_skill_directories`|fn|priv|72-74|def _skill_directories(|
|`_prompt_files`|fn|priv|102-104|def _prompt_files(|
|`install_target`|fn|pub|133-138|def install_target(|
|`install_enabled`|fn|pub|168-169|def install_enabled(|
|`uninstall_target`|fn|pub|212-217|def uninstall_target(|
|`uninstall_enabled`|fn|pub|251-252|def uninstall_enabled(|


---

# settings.py | Python | 105L | 5 symbols | 4 imports | 8 comments
> Path: `src/skills/settings.py`
- @brief Persist enabled CLI targets and installed prompt records.
- @details User configuration is a JSON object stored at
`$HOME/.config/skills/config.json` with the schema
`{"enabled": ["<cli>", ...], "prompts": {"<cli>": ["<file>", ...]}}`.
Loading tolerates missing, unreadable, or malformed content by
returning normalized defaults.
- @satisfies DES-047 DES-048 DES-060

## Imports
```
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
```

## Definitions

- var `CONFIG_RELATIVE = Path(".config") / "skills" / "config.json"` (L21)
- @brief Configuration path relative to the user home directory.
- @details `$HOME` + `.config/skills/config.json`.
- @satisfies DES-047
### fn `def config_path(home: Path | None = None) -> Path` (L24-35)
- @brief Resolve the user configuration file path.
- @details Joins the effective home directory with `.config/skills/config.json`.
- @param home {Path | None} Optional home-directory override.
- @return {Path} Configuration file path.
- @satisfies DES-047

### fn `def _unique_strings(value: Any) -> list[str]` `priv` (L36-55)
- @brief Filter an arbitrary JSON value into unique non-empty strings.
- @details Preserves first-seen order and drops non-string, empty, and duplicate entries.
- @param value {Any} Candidate JSON value.
- @return {list[str]} Unique strings in first-seen order; empty for non-list input. @complexity O(n) where n is the list length.
- @satisfies DES-048 DES-060

### fn `def load_config(home: Path | None = None) -> dict[str, Any]` (L56-83)
- @brief Load the user configuration with normalized defaults.
- @details Reads JSON from `config_path`. Missing, unreadable, non-object, or malformed content yields `{"enabled": [], "prompts": {}}`. Valid `enabled` entries are unique strings; valid `prompts` entries map CLI names to unique filename lists.
- @param home {Path | None} Optional home-directory override.
- @return {dict[str, Any]} Normalized configuration object.
- @note Read and decode errors are handled internally and are not raised.
- @satisfies DES-047 DES-048 DES-060

### fn `def save_config(config: dict[str, Any], home: Path | None = None) -> Path` (L84-106)
- @brief Persist normalized configuration to the user configuration file.
- @details Creates parent directories, serializes with two-space indentation and a trailing newline, writes a sibling temporary file, then replaces the configuration file atomically.
- @param config {dict[str, Any]} Configuration object to persist.
- @param home {Path | None} Optional home-directory override.
- @return {Path} Written configuration file path.
- @throws {OSError} When directory creation or file writing fails.
- @satisfies DES-047 DES-048 DES-060
- @post The configuration file contains the serialized `config` object.

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`CONFIG_RELATIVE`|var|pub|21||
|`config_path`|fn|pub|24-35|def config_path(home: Path | None = None) -> Path|
|`_unique_strings`|fn|priv|36-55|def _unique_strings(value: Any) -> list[str]|
|`load_config`|fn|pub|56-83|def load_config(home: Path | None = None) -> dict[str, Any]|
|`save_config`|fn|pub|84-106|def save_config(config: dict[str, Any], home: Path | None...|


---

# show.py | Python | 297L | 14 symbols | 6 imports | 14 comments
> Path: `src/skills/show.py`
- @brief Render packaged resource inventory, CLI configuration, and installation status.
- @details Builds three deterministic ASCII tables: bundled skills and prompts from
the manifest, every supported CLI with enabled state and home-relative
skills path, and a per-resource per-enabled-CLI installation status
derived from destination-directory scans.
- @satisfies DES-065 DES-066 REQ-037 REQ-038 REQ-039 REQ-040 REQ-041

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
- var `STATUS_UNSUPPORTED = "UNSUPPORTED"` (L29)
- @brief Status value for prompt installation on a CLI without prompts support.
### fn `def _wrap(text: str, width: int) -> list[str]` `priv` (L32-65)
- @brief Wrap one cell value into fixed-width lines on word boundaries.
- @details Collapses whitespace, splits overlong tokens into `width`-sized chunks, and greedily packs words without exceeding `width`.
- @param text {str} Cell value to wrap.
- @param width {int} Maximum line width in characters; MUST be positive.
- @return {list[str]} Rendered lines; `[""]` for an empty value.
- @satisfies DES-066

### fn `def render_table(` (L66-69)

### fn `def render(cells: Sequence[str]) -> list[str]` (L91-109)
- @brief Render an ASCII grid table with aligned and wrapped cells.
- @details Column widths are the longest cell capped by `max_width`; every
row is emitted between `+---+` borders and multi-line cells are
padded to the row height.
- @param headers {Sequence[str]} Column header labels.
- @param rows {Iterable[Sequence[str]]} Row cell values; short rows are padded.
- @param max_width {int} Maximum column width in characters.
- @return {str} Rendered table text without trailing newline.
- @satisfies DES-066

### fn `def _resource_rows(` `priv` (L117-118)

### fn `def _cli_rows(` `priv` (L141-143)
- @brief Build inventory rows from manifest catalog entries.
- @details Emits skills before prompts, preserving manifest entry order.
- @param catalog {dict[str, list[dict[str, str]]]} Manifest catalog.
- @return {list[tuple[str, str, str, str]]} `(type, name, file, description)` rows.
- @satisfies REQ-037

### fn `def _files_match(source: Path, destination: Path) -> str` `priv` (L172-190)
- @brief Build CLI configuration rows from the adapter registry.
- @brief Compare one packaged file with its installed destination file.
- @details Reports registry order, enabled state, home-relative skills
destination, and prompts destination or `UNSUPPORTED` for
prompt-less adapters.
- @param config {dict[str, object]} Normalized user configuration.
- @param home {Path | None} Optional home-directory override.
- @param source {Path} Packaged file path.
- @param destination {Path} Installed destination file path.
- @return {list[tuple[str, str, str, str]]} `(cli, enabled, skills path,
prompts path)` rows.
- @return {str} `OK` for identical bytes, `MISSING` for absent destination, `STALE` for differing bytes or unreadable content.
- @satisfies REQ-038
- @satisfies REQ-040

### fn `def _skill_status(source: Path, destination: Path) -> str` `priv` (L191-214)
- @brief Compare a packaged skill directory with its installed copy.
- @details Every packaged regular file must exist in the destination with identical bytes.
- @param source {Path} Packaged skill directory.
- @param destination {Path} Installed skill destination directory.
- @return {str} `OK` when all files match; `MISSING` when the package or a destination file is absent; `STALE` on content mismatch.
- @satisfies REQ-040

### fn `def _install_rows(` `priv` (L215-218)

### fn `def build_show(home: Path | None = None) -> str` (L264-298)
- @brief Build per-resource per-enabled-CLI installation status rows.
- @brief Build the complete `show` report text.
- @details Scans adapter destination directories for each manifest skill or
prompt and emits rows only for CLIs present in the enabled
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
- @satisfies REQ-039 REQ-040 REQ-041
- @satisfies DES-065 REQ-037 REQ-038 REQ-039 REQ-042

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`MAX_CELL_WIDTH`|var|pub|21||
|`STATUS_OK`|var|pub|23||
|`STATUS_MISSING`|var|pub|25||
|`STATUS_STALE`|var|pub|27||
|`STATUS_UNSUPPORTED`|var|pub|29||
|`_wrap`|fn|priv|32-65|def _wrap(text: str, width: int) -> list[str]|
|`render_table`|fn|pub|66-69|def render_table(|
|`render`|fn|pub|91-109|def render(cells: Sequence[str]) -> list[str]|
|`_resource_rows`|fn|priv|117-118|def _resource_rows(|
|`_cli_rows`|fn|priv|141-143|def _cli_rows(|
|`_files_match`|fn|priv|172-190|def _files_match(source: Path, destination: Path) -> str|
|`_skill_status`|fn|priv|191-214|def _skill_status(source: Path, destination: Path) -> str|
|`_install_rows`|fn|priv|215-218|def _install_rows(|
|`build_show`|fn|pub|264-298|def build_show(home: Path | None = None) -> str|


---

# targets.py | Python | 351L | 22 symbols | 5 imports | 27 comments
> Path: `src/skills/targets.py`
- @brief Provide per-CLI skill and prompt installation adapters.
- @details Defines the `CliTarget` abstraction and one concrete adapter for each
supported CLI: `pi`, `openclaw`, `codex`, `antigravity`, and `claude`.
Adapters resolve user-level destination directories from a home root
and provide deterministic copy algorithms for skills and prompts.
Shared copy primitives synchronize packaged trees, overwrite changed
files, and prune destination entries absent from the package.
Removal primitives delete managed skill directories and managed
prompt filenames while preserving unmanaged destination entries.
- @satisfies PRJ-010 PRJ-011 DES-049 DES-050 DES-051 DES-052 DES-053 DES-054 DES-055 DES-056 DES-057 DES-058 DES-059 DES-063 REQ-048 REQ-049 REQ-051 REQ-052

## Imports
```
from __future__ import annotations
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable
```

## Definitions

### fn `def resolve_home(home: Path | None) -> Path` (L23-35)
- @brief Resolve the user home directory used for destination paths.
- @details Returns the explicit override when provided; otherwise resolves `Path.home()`. Centralizes home resolution for deterministic tests and adapter reuse.
- @param home {Path | None} Optional home-directory override.
- @return {Path} Effective home directory path.
- @satisfies DES-049

### fn `def sync_skill_tree(source: Path, destination: Path) -> None` (L36-68)
- @brief Replace a destination skill directory with packaged contents.
- @details Copies the source tree recursively with overwrite, then removes destination files and directories absent from the source tree. Destination skill files become byte-identical copies of package files. Pruning runs deepest-first to keep directory removal safe.
- @param source {Path} Packaged skill directory containing `SKILL.md`.
- @param destination {Path} Target skill directory named after `source.name`.
- @return {None}
- @throws {OSError} When directory creation, copying, or pruning fails.
- @satisfies DES-055 DES-056 DES-057 DES-063
- @pre `source` MUST be an existing directory.
- @post `destination` contains exactly the source tree paths and contents. @complexity O(S + D) where S is source entries and D is destination entries.

### class `class CliTarget(ABC)` : ABC (L69-208)
- @brief Abstract adapter for a supported CLI installation target.
- @details Subclasses declare the CLI name and resolve user-level destination directories. Base methods implement deterministic skill-tree synchronization, prompt-file synchronization with stale-record removal, and managed resource removal. Prompt-less adapters inherit a `None` prompt destination.
- @satisfies DES-049 REQ-048 REQ-049
- fn `def skills_dir(self, home: Path | None = None) -> Path` (L84-91)
  - @brief Resolve the CLI user-level skills destination directory.
  - @param home {Path | None} Optional home-directory override.
  - @return {Path} Skills destination directory.
  - @satisfies DES-050 DES-051 DES-052 DES-053 DES-054
- fn `def prompts_dir(self, home: Path | None = None) -> Path | None` (L92-102)
  - @brief Resolve the CLI user-level prompts destination directory.
  - @details Returns `None` for CLIs without prompt-file support.
  - @param home {Path | None} Optional home-directory override.
  - @return {Path | None} Prompts destination directory when supported; `None` otherwise.
  - @satisfies DES-050 DES-051 DES-052 DES-053 DES-054
- fn `def install_skills(self, sources: Iterable[Path], home: Path | None = None) -> int` (L103-120)
  - @brief Install packaged skill directories into this CLI destination.
  - @details Synchronizes each source directory into `<skills_dir>/<source.name>` using `sync_skill_tree`.
  - @param sources {Iterable[Path]} Packaged skill directories.
  - @param home {Path | None} Optional home-directory override.
  - @return {int} Number of processed skill directories.
  - @throws {OSError} When synchronization fails.
  - @satisfies DES-055 DES-056 DES-057 DES-063
- fn `def install_prompts(` (L121-125)
- fn `def remove_skills(self, names: Iterable[str], home: Path | None = None) -> int` (L157-180)
  - @brief Install packaged prompt files and remove stale managed prompts.
  - @brief Remove managed skill directories from this CLI destination.
  - @details No-ops with an empty list when prompts are unsupported.
Otherwise creates the destination directory, deletes previously
managed filenames absent from `sources`, then copies each source
file into the destination using its source filename. Recorded
names containing path components or traversal segments are
ignored during deletion.
  - @details Deletes `<skills_dir>/<name>` recursively for each name. Missing destinations count as removed and do not raise. Destination entries outside `names` are preserved and no directory is created. Complexity O(N) deletions where N is the number of names.
  - @param sources {Iterable[Path]} Packaged prompt files.
  - @param previous {Iterable[str]} Previously installed prompt filenames.
  - @param home {Path | None} Optional home-directory override.
  - @param names {Iterable[str]} Managed skill directory names.
  - @param home {Path | None} Optional home-directory override.
  - @return {list[str]} Sorted installed prompt filenames; empty when
prompts are unsupported.
  - @return {int} Number of processed names; missing destinations count as removed.
  - @throws {OSError} When deletion, directory creation, or copying fails.
  - @throws {OSError} When recursive directory deletion fails.
  - @satisfies DES-059 DES-060 DES-061 DES-063
  - @satisfies REQ-048 REQ-051 REQ-052
- fn `def remove_prompts(self, names: Iterable[str], home: Path | None = None) -> int` (L181-208)
  - @brief Remove managed prompt files from this CLI prompts destination.
  - @details No-ops with 0 when prompts are unsupported. Deletes `<prompts_dir>/<name>` for each safe name; names containing path components or traversal segments are skipped. Missing files count as removed and do not raise. Complexity O(N) deletions where N is the number of names.
  - @param names {Iterable[str]} Managed prompt filenames, manifest and recorded.
  - @param home {Path | None} Optional home-directory override.
  - @return {int} Number of processed safe names; missing files count as removed.
  - @throws {OSError} When file deletion fails.
  - @satisfies REQ-049 REQ-051 REQ-052

### class `class PiTarget(CliTarget)` : CliTarget (L209-237)
- @brief Installation adapter for the `pi` coding agent.
- @details Installs skills under `$HOME/.pi/agent/skills` and prompt templates under `$HOME/.pi/agent/prompts`.
- @satisfies DES-050
- fn `def skills_dir(self, home: Path | None = None) -> Path` (L219-227)
  - @brief Installation adapter for the `pi` coding agent.
  - @brief Resolve the pi user-level skills directory.
  - @details Installs skills under `$HOME/.pi/agent/skills` and prompt
templates under `$HOME/.pi/agent/prompts`.
  - @param home {Path | None} Optional home-directory override.
  - @return {Path} `$HOME/.pi/agent/skills`.
  - @satisfies DES-050
  - @satisfies DES-050
- fn `def prompts_dir(self, home: Path | None = None) -> Path` (L228-237)
  - @brief Resolve the pi user-level prompts directory.
  - @param home {Path | None} Optional home-directory override.
  - @return {Path} `$HOME/.pi/agent/prompts`.
  - @satisfies DES-050

### class `class OpenClawTarget(CliTarget)` : CliTarget (L238-257)
- @brief Installation adapter for the `openclaw` agent workspace.
- @details Installs skills under `$HOME/.openclaw/workspace/skills`; prompt template installation is unsupported.
- @satisfies DES-051
- fn `def skills_dir(self, home: Path | None = None) -> Path` (L248-257)
  - @brief Installation adapter for the `openclaw` agent workspace.
  - @brief Resolve the openclaw user-level skills directory.
  - @details Installs skills under `$HOME/.openclaw/workspace/skills`; prompt
template installation is unsupported.
  - @param home {Path | None} Optional home-directory override.
  - @return {Path} `$HOME/.openclaw/workspace/skills`.
  - @satisfies DES-051
  - @satisfies DES-051

### class `class CodexTarget(CliTarget)` : CliTarget (L258-277)
- @brief Installation adapter for the `codex` CLI.
- @details Installs skills under `$HOME/.codex/skills`; prompt template installation is unsupported.
- @satisfies DES-052
- fn `def skills_dir(self, home: Path | None = None) -> Path` (L268-277)
  - @brief Installation adapter for the `codex` CLI.
  - @brief Resolve the codex user-level skills directory.
  - @details Installs skills under `$HOME/.codex/skills`; prompt template
installation is unsupported.
  - @param home {Path | None} Optional home-directory override.
  - @return {Path} `$HOME/.codex/skills`.
  - @satisfies DES-052
  - @satisfies DES-052

### class `class AntigravityTarget(CliTarget)` : CliTarget (L278-297)
- @brief Installation adapter for Google Antigravity.
- @details Installs skills under `$HOME/.gemini/config/skills`; prompt template installation is unsupported.
- @satisfies DES-053
- fn `def skills_dir(self, home: Path | None = None) -> Path` (L288-297)
  - @brief Installation adapter for Google Antigravity.
  - @brief Resolve the antigravity user-level skills directory.
  - @details Installs skills under `$HOME/.gemini/config/skills`; prompt
template installation is unsupported.
  - @param home {Path | None} Optional home-directory override.
  - @return {Path} `$HOME/.gemini/config/skills`.
  - @satisfies DES-053
  - @satisfies DES-053

### class `class ClaudeTarget(CliTarget)` : CliTarget (L298-326)
- @brief Installation adapter for the `claude` CLI.
- @details Installs skills under `$HOME/.claude/skills` and slash-command prompt files under `$HOME/.claude/commands`.
- @satisfies DES-054
- fn `def skills_dir(self, home: Path | None = None) -> Path` (L308-316)
  - @brief Installation adapter for the `claude` CLI.
  - @brief Resolve the claude user-level skills directory.
  - @details Installs skills under `$HOME/.claude/skills` and slash-command
prompt files under `$HOME/.claude/commands`.
  - @param home {Path | None} Optional home-directory override.
  - @return {Path} `$HOME/.claude/skills`.
  - @satisfies DES-054
  - @satisfies DES-054
- fn `def prompts_dir(self, home: Path | None = None) -> Path` (L317-326)
  - @brief Resolve the claude user-level commands directory.
  - @param home {Path | None} Optional home-directory override.
  - @return {Path} `$HOME/.claude/commands`.
  - @satisfies DES-054

### fn `def resolve_target(name: str) -> CliTarget | None` (L342-352)
- @brief Registry of supported CLI adapters keyed by canonical CLI name.
- @brief Resolve a CLI adapter by canonical name.
- @details Insertion order defines the supported-name listing in diagnostics.
- @details Trims surrounding whitespace and lowercases the input before a registry lookup.
- @param name {str} CLI name supplied on the command line.
- @return {CliTarget | None} Matching adapter; `None` when unsupported.
- @satisfies DES-049
- @satisfies REQ-026

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`resolve_home`|fn|pub|23-35|def resolve_home(home: Path | None) -> Path|
|`sync_skill_tree`|fn|pub|36-68|def sync_skill_tree(source: Path, destination: Path) -> None|
|`CliTarget`|class|pub|69-208|class CliTarget(ABC)|
|`CliTarget.skills_dir`|fn|pub|84-91|def skills_dir(self, home: Path | None = None) -> Path|
|`CliTarget.prompts_dir`|fn|pub|92-102|def prompts_dir(self, home: Path | None = None) -> Path |...|
|`CliTarget.install_skills`|fn|pub|103-120|def install_skills(self, sources: Iterable[Path], home: P...|
|`CliTarget.install_prompts`|fn|pub|121-125|def install_prompts(|
|`CliTarget.remove_skills`|fn|pub|157-180|def remove_skills(self, names: Iterable[str], home: Path ...|
|`CliTarget.remove_prompts`|fn|pub|181-208|def remove_prompts(self, names: Iterable[str], home: Path...|
|`PiTarget`|class|pub|209-237|class PiTarget(CliTarget)|
|`PiTarget.skills_dir`|fn|pub|219-227|def skills_dir(self, home: Path | None = None) -> Path|
|`PiTarget.prompts_dir`|fn|pub|228-237|def prompts_dir(self, home: Path | None = None) -> Path|
|`OpenClawTarget`|class|pub|238-257|class OpenClawTarget(CliTarget)|
|`OpenClawTarget.skills_dir`|fn|pub|248-257|def skills_dir(self, home: Path | None = None) -> Path|
|`CodexTarget`|class|pub|258-277|class CodexTarget(CliTarget)|
|`CodexTarget.skills_dir`|fn|pub|268-277|def skills_dir(self, home: Path | None = None) -> Path|
|`AntigravityTarget`|class|pub|278-297|class AntigravityTarget(CliTarget)|
|`AntigravityTarget.skills_dir`|fn|pub|288-297|def skills_dir(self, home: Path | None = None) -> Path|
|`ClaudeTarget`|class|pub|298-326|class ClaudeTarget(CliTarget)|
|`ClaudeTarget.skills_dir`|fn|pub|308-316|def skills_dir(self, home: Path | None = None) -> Path|
|`ClaudeTarget.prompts_dir`|fn|pub|317-326|def prompts_dir(self, home: Path | None = None) -> Path|
|`resolve_target`|fn|pub|342-352|def resolve_target(name: str) -> CliTarget | None|

