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

# catalog.py | Python | 139L | 7 symbols | 4 imports | 6 comments
> Path: `src/skills/catalog.py`
- @brief Generate the skills and prompts manifest for `src/resources`.
- @details Deterministic generator for `src/resources/manifest.json`. Recursively
scans `src/resources/skills` for `SKILL.md` files and
`src/resources/prompts` for frontmatter files, extracts frontmatter
`name` and `description`, and emits entries sorted by relative path.
Single maintenance path guaranteeing each manifest description equals
its source frontmatter `description` string (exact match).
- @satisfies DES-021 DES-022 DES-023 DES-024

## Imports
```
from __future__ import annotations
import importlib.resources as ires
import json
from pathlib import Path
```

## Definitions

- var `RESOURCES_ROOT = Path(str(ires.files("resources")))` (L19)
- var `MANIFEST_PATH = RESOURCES_ROOT / "manifest.json"` (L20)
### fn `def _parse_frontmatter(text: str) -> dict[str, str]` `priv` (L23-55)
- @brief Parse `name` and `description` from a YAML frontmatter block.
- @details Reads key/value lines up to the closing `---` delimiter, strips surrounding YAML quotes from scalar values, and returns only the `name` and `description` keys when present.
- @param text {str} Raw file text (UTF-8).
- @return {Dict[str, str]} Frontmatter `name`/`description` mapping; empty when the block or keys are absent.
- @pre `text` must be a non-empty string.

### fn `def _discover_skills(root: Path) -> list[Path]` `priv` (L56-68)
- @brief Discover `SKILL.md` files under `root/skills`.
- @details Recursively collects every file named `SKILL.md`, sorted by path.
- @param root {Path} Resources root directory.
- @return {List[Path]} Sorted `SKILL.md` file paths.

### fn `def _discover_prompts(root: Path) -> list[Path]` `priv` (L69-82)
- @brief Discover candidate prompt files under `root/prompts`.
- @details Recursively collects every regular file, sorted by path. Frontmatter filtering is applied by `build_catalog`.
- @param root {Path} Resources root directory.
- @return {List[Path]} Sorted candidate prompt file paths.

### fn `def build_catalog(` (L83-84)

### fn `def write_catalog(` (L120-122)
- @brief Build the skills and prompts catalog dictionary.
- @details Scans skills and prompts directories, extracts frontmatter
metadata, and emits entries sorted by relative path. Entries
missing `name` or `description` are omitted.
- @param resources_root {Path} Resources root directory to scan.
- @return {Dict[str, List[Dict[str, str]]]} Catalog with `skills` and
`prompts` lists; each entry contains `file`, `name`, `description`.
- @satisfies DES-021 DES-022 DES-023 DES-024

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`RESOURCES_ROOT`|var|pub|19||
|`MANIFEST_PATH`|var|pub|20||
|`_parse_frontmatter`|fn|priv|23-55|def _parse_frontmatter(text: str) -> dict[str, str]|
|`_discover_skills`|fn|priv|56-68|def _discover_skills(root: Path) -> list[Path]|
|`_discover_prompts`|fn|priv|69-82|def _discover_prompts(root: Path) -> list[Path]|
|`build_catalog`|fn|pub|83-84|def build_catalog(|
|`write_catalog`|fn|pub|120-122|def write_catalog(|


---

# core.py | Python | 260L | 14 symbols | 14 imports | 7 comments
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
from .installer import install_enabled
from .settings import load_config, save_config
from .show import build_show
from .targets import TARGETS, resolve_target
```

## Definitions

- var `ENDPOINT = "https://api.github.com/repos/Ogekuri/SKILLs/releases/latest"` (L20)
- var `UPGRADE = ["uv", "tool", "install", "skills", "--force", "--from", "git+https://github.com/Ogekuri/SKILLs.git"]` (L21)
- var `UNINSTALL = ["uv", "tool", "uninstall", "skills"]` (L22)
### fn `def cache_path() -> Path` (L44-47)

### fn `def _human(timestamp: float | None) -> str | None` `priv` (L48-51)

### fn `def _version(value: str) -> tuple[int, int, int]` `priv` (L52-58)

### fn `def check_version(force: bool = False) -> None` (L59-106)

### fn `def _manage(command: list[str]) -> int` `priv` (L107-117)

### fn `def _unsupported(name: str) -> str` `priv` (L118-128)
- @brief Build an unsupported-CLI diagnostic message.
- @details Lists the canonical CLI names accepted by the adapter registry.
- @param name {str} Unsupported CLI name from the command line.
- @return {str} Human-readable diagnostic message.
- @satisfies REQ-026

### fn `def _enable(name: str, home: Path | None = None) -> int` `priv` (L129-154)
- @brief Enable resource installation for one supported CLI.
- @details Resolves the CLI adapter, loads the user configuration, appends the canonical CLI name when absent, and persists the configuration. Re-enabling an enabled CLI leaves configuration unchanged.
- @param name {str} CLI name from the command line.
- @param home {Path | None} Optional home-directory override.
- @return {int} Exit code: 0 on success; 2 for an unsupported CLI.
- @throws {OSError} When saving the configuration file fails.
- @satisfies REQ-024 REQ-026 REQ-027 REQ-028

### fn `def _disable(name: str, home: Path | None = None) -> int` `priv` (L155-181)
- @brief Disable resource installation for one supported CLI.
- @details Resolves the CLI adapter, loads the user configuration, removes the canonical CLI name when present, and persists the configuration. Disabling an already disabled CLI is a successful no-op.
- @param name {str} CLI name from the command line.
- @param home {Path | None} Optional home-directory override.
- @return {int} Exit code: 0 on success; 2 for an unsupported CLI.
- @throws {OSError} When saving the configuration file fails.
- @satisfies REQ-025 REQ-026 REQ-027 REQ-028

### fn `def _install(home: Path | None = None) -> int` `priv` (L182-206)
- @brief Install bundled resources for all enabled CLIs.
- @details Delegates installation to `install_enabled`, prints per-CLI skill and prompt counts, prints an informational message when no CLI is enabled, and reports collected failures.
- @param home {Path | None} Optional home-directory override.
- @return {int} Exit code: 0 when no failure occurs; 1 when any failure occurs.
- @satisfies REQ-029 REQ-030 REQ-031 REQ-032

### fn `def _show(home: Path | None = None) -> int` `priv` (L207-219)
- @brief Print packaged resources, CLI configuration, and installation status.
- @details Delegates report rendering to `build_show` and prints the result.
- @param home {Path | None} Optional home-directory override.
- @return {int} Exit code 0 after printing the report.
- @throws {OSError} When bundled resources or the configuration cannot be read.
- @satisfies REQ-037 REQ-038 REQ-039 REQ-042

### fn `def main(argv: list[str] | None = None) -> int` (L220-261)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`ENDPOINT`|var|pub|20||
|`UPGRADE`|var|pub|21||
|`UNINSTALL`|var|pub|22||
|`cache_path`|fn|pub|44-47|def cache_path() -> Path|
|`_human`|fn|priv|48-51|def _human(timestamp: float | None) -> str | None|
|`_version`|fn|priv|52-58|def _version(value: str) -> tuple[int, int, int]|
|`check_version`|fn|pub|59-106|def check_version(force: bool = False) -> None|
|`_manage`|fn|priv|107-117|def _manage(command: list[str]) -> int|
|`_unsupported`|fn|priv|118-128|def _unsupported(name: str) -> str|
|`_enable`|fn|priv|129-154|def _enable(name: str, home: Path | None = None) -> int|
|`_disable`|fn|priv|155-181|def _disable(name: str, home: Path | None = None) -> int|
|`_install`|fn|priv|182-206|def _install(home: Path | None = None) -> int|
|`_show`|fn|priv|207-219|def _show(home: Path | None = None) -> int|
|`main`|fn|pub|220-261|def main(argv: list[str] | None = None) -> int|


---

# installer.py | Python | 185L | 6 symbols | 7 imports | 11 comments
> Path: `src/skills/installer.py`
- @brief Orchestrate skill and prompt installation for enabled CLI targets.
- @details Builds the bundled resource catalog, resolves manifest skill
directories and prompt files, invokes the configured CLI adapters,
updates prompt records, and aggregates per-CLI outcomes.
- @satisfies PRJ-009 REQ-029 REQ-030 REQ-032 REQ-035 DES-055 DES-059 DES-060 DES-061 DES-062 DES-064

## Imports
```
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from .catalog import RESOURCES_ROOT, build_catalog
from .settings import load_config, save_config
from .targets import CliTarget, resolve_target
```

## Definitions

### class `class InstallError(RuntimeError)` : RuntimeError (L21-29)
- @brief Signal a manifest or packaged-resource installation failure.
- @details Raised when a manifest-listed source path is missing, duplicated, or otherwise not installable.
- @satisfies REQ-035

### class `class InstallSummary` `@dataclass(frozen=True)` (L31-48)
- @brief Summarize one CLI installation result.
- @details Carries the canonical CLI name, installed skill count, installed prompt count, and installed prompt filenames for persistence.
- @satisfies REQ-030 DES-060

### fn `def _skill_directories(` `priv` (L49-51)

### fn `def _prompt_files(` `priv` (L79-81)
- @brief Resolve manifest skill entries to packaged skill directories.
- @details Validates each entry file path, deduplicates by directory name, and
returns directories sorted by name.
- @param resources_root {Path} Resources root directory.
- @param entries {Iterable[dict[str, str]]} Manifest skill entries.
- @return {list[Path]} Sorted unique skill directories.
- @throws {InstallError} When a manifest-listed skill file or directory is
missing.
- @satisfies DES-055 DES-062 REQ-035

### fn `def install_target(` (L110-115)
- @brief Resolve manifest prompt entries to packaged prompt files.
- @details Validates each entry file path and rejects duplicate destination
filenames that would overwrite each other.
- @param resources_root {Path} Resources root directory.
- @param entries {Iterable[dict[str, str]]} Manifest prompt entries.
- @return {list[Path]} Packaged prompt files sorted by relative path.
- @throws {InstallError} When a manifest-listed prompt file is missing or two
entries share the same destination filename.
- @satisfies DES-059 DES-062 REQ-035

### fn `def install_enabled(` (L144-145)
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
- @satisfies REQ-029 REQ-030 DES-055 DES-056 DES-057 DES-059 DES-061 DES-062

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`InstallError`|class|pub|21-29|class InstallError(RuntimeError)|
|`InstallSummary`|class|pub|31-48|class InstallSummary|
|`_skill_directories`|fn|priv|49-51|def _skill_directories(|
|`_prompt_files`|fn|priv|79-81|def _prompt_files(|
|`install_target`|fn|pub|110-115|def install_target(|
|`install_enabled`|fn|pub|144-145|def install_enabled(|


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

# show.py | Python | 293L | 14 symbols | 6 imports | 14 comments
> Path: `src/skills/show.py`
- @brief Render packaged resource inventory, CLI configuration, and installation status.
- @details Builds three deterministic ASCII tables: bundled skills and prompts from
the manifest, every supported CLI with enabled state and destination
paths, and a per-resource per-CLI installation status derived from
destination-directory scans.
- @satisfies DES-065 DES-066 REQ-037 REQ-038 REQ-039 REQ-040 REQ-041

## Imports
```
from __future__ import annotations
from pathlib import Path
from typing import Any, Iterable, Sequence
from .catalog import RESOURCES_ROOT, build_catalog
from .settings import load_config
from .targets import TARGETS
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

### fn `def _files_match(source: Path, destination: Path) -> str` `priv` (L170-188)
- @brief Build CLI configuration rows from the adapter registry.
- @brief Compare one packaged file with its installed destination file.
- @details Reports registry order, enabled state, skills destination, and
prompts destination or `UNSUPPORTED` for prompt-less adapters.
- @param config {dict[str, object]} Normalized user configuration.
- @param home {Path | None} Optional home-directory override.
- @param source {Path} Packaged file path.
- @param destination {Path} Installed destination file path.
- @return {list[tuple[str, str, str, str]]} `(cli, enabled, skills path,
prompts path)` rows.
- @return {str} `OK` for identical bytes, `MISSING` for absent destination, `STALE` for differing bytes or unreadable content.
- @satisfies REQ-038
- @satisfies REQ-040

### fn `def _skill_status(source: Path, destination: Path) -> str` `priv` (L189-212)
- @brief Compare a packaged skill directory with its installed copy.
- @details Every packaged regular file must exist in the destination with identical bytes.
- @param source {Path} Packaged skill directory.
- @param destination {Path} Installed skill destination directory.
- @return {str} `OK` when all files match; `MISSING` when the package or a destination file is absent; `STALE` on content mismatch.
- @satisfies REQ-040

### fn `def _install_rows(` `priv` (L213-216)

### fn `def build_show(home: Path | None = None) -> str` (L260-294)
- @brief Build per-resource per-CLI installation status rows.
- @brief Build the complete `show` report text.
- @details Scans adapter destination directories for each manifest skill or
prompt and reports the enabled state of the owning CLI.
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
|`_files_match`|fn|priv|170-188|def _files_match(source: Path, destination: Path) -> str|
|`_skill_status`|fn|priv|189-212|def _skill_status(source: Path, destination: Path) -> str|
|`_install_rows`|fn|priv|213-216|def _install_rows(|
|`build_show`|fn|pub|260-294|def build_show(home: Path | None = None) -> str|


---

# targets.py | Python | 297L | 20 symbols | 5 imports | 25 comments
> Path: `src/skills/targets.py`
- @brief Provide per-CLI skill and prompt installation adapters.
- @details Defines the `CliTarget` abstraction and one concrete adapter for each
supported CLI: `pi`, `openclaw`, `codex`, `antigravity`, and `claude`.
Adapters resolve user-level destination directories from a home root
and provide deterministic copy algorithms for skills and prompts.
Shared copy primitives synchronize packaged trees, overwrite changed
files, and prune destination entries absent from the package.
- @satisfies PRJ-010 DES-049 DES-050 DES-051 DES-052 DES-053 DES-054 DES-055 DES-056 DES-057 DES-058 DES-059 DES-063

## Imports
```
from __future__ import annotations
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable
```

## Definitions

### fn `def resolve_home(home: Path | None) -> Path` (L21-33)
- @brief Resolve the user home directory used for destination paths.
- @details Returns the explicit override when provided; otherwise resolves `Path.home()`. Centralizes home resolution for deterministic tests and adapter reuse.
- @param home {Path | None} Optional home-directory override.
- @return {Path} Effective home directory path.
- @satisfies DES-049

### fn `def sync_skill_tree(source: Path, destination: Path) -> None` (L34-66)
- @brief Replace a destination skill directory with packaged contents.
- @details Copies the source tree recursively with overwrite, then removes destination files and directories absent from the source tree. Destination skill files become byte-identical copies of package files. Pruning runs deepest-first to keep directory removal safe.
- @param source {Path} Packaged skill directory containing `SKILL.md`.
- @param destination {Path} Target skill directory named after `source.name`.
- @return {None}
- @throws {OSError} When directory creation, copying, or pruning fails.
- @satisfies DES-055 DES-056 DES-057 DES-063
- @pre `source` MUST be an existing directory.
- @post `destination` contains exactly the source tree paths and contents. @complexity O(S + D) where S is source entries and D is destination entries.

### class `class CliTarget(ABC)` : ABC (L67-154)
- @brief Abstract adapter for a supported CLI installation target.
- @details Subclasses declare the CLI name and resolve user-level destination directories. Base methods implement deterministic skill-tree synchronization and prompt-file synchronization with stale-record removal. Prompt-less adapters inherit a `None` prompt destination.
- @satisfies DES-049
- fn `def skills_dir(self, home: Path | None = None) -> Path` (L81-88)
  - @brief Resolve the CLI user-level skills destination directory.
  - @param home {Path | None} Optional home-directory override.
  - @return {Path} Skills destination directory.
  - @satisfies DES-050 DES-051 DES-052 DES-053 DES-054
- fn `def prompts_dir(self, home: Path | None = None) -> Path | None` (L89-99)
  - @brief Resolve the CLI user-level prompts destination directory.
  - @details Returns `None` for CLIs without prompt-file support.
  - @param home {Path | None} Optional home-directory override.
  - @return {Path | None} Prompts destination directory when supported; `None` otherwise.
  - @satisfies DES-050 DES-051 DES-052 DES-053 DES-054
- fn `def install_skills(self, sources: Iterable[Path], home: Path | None = None) -> int` (L100-117)
  - @brief Install packaged skill directories into this CLI destination.
  - @details Synchronizes each source directory into `<skills_dir>/<source.name>` using `sync_skill_tree`.
  - @param sources {Iterable[Path]} Packaged skill directories.
  - @param home {Path | None} Optional home-directory override.
  - @return {int} Number of processed skill directories.
  - @throws {OSError} When synchronization fails.
  - @satisfies DES-055 DES-056 DES-057 DES-063
- fn `def install_prompts(` (L118-122)

### class `class PiTarget(CliTarget)` : CliTarget (L155-183)
- @brief Installation adapter for the `pi` coding agent.
- @details Installs skills under `$HOME/.pi/agent/skills` and prompt templates under `$HOME/.pi/agent/prompts`.
- @satisfies DES-050
- fn `def skills_dir(self, home: Path | None = None) -> Path` (L165-173)
  - @brief Installation adapter for the `pi` coding agent.
  - @brief Resolve the pi user-level skills directory.
  - @details Installs skills under `$HOME/.pi/agent/skills` and prompt
templates under `$HOME/.pi/agent/prompts`.
  - @param home {Path | None} Optional home-directory override.
  - @return {Path} `$HOME/.pi/agent/skills`.
  - @satisfies DES-050
  - @satisfies DES-050
- fn `def prompts_dir(self, home: Path | None = None) -> Path` (L174-183)
  - @brief Resolve the pi user-level prompts directory.
  - @param home {Path | None} Optional home-directory override.
  - @return {Path} `$HOME/.pi/agent/prompts`.
  - @satisfies DES-050

### class `class OpenClawTarget(CliTarget)` : CliTarget (L184-203)
- @brief Installation adapter for the `openclaw` agent workspace.
- @details Installs skills under `$HOME/.openclaw/workspace/skills`; prompt template installation is unsupported.
- @satisfies DES-051
- fn `def skills_dir(self, home: Path | None = None) -> Path` (L194-203)
  - @brief Installation adapter for the `openclaw` agent workspace.
  - @brief Resolve the openclaw user-level skills directory.
  - @details Installs skills under `$HOME/.openclaw/workspace/skills`; prompt
template installation is unsupported.
  - @param home {Path | None} Optional home-directory override.
  - @return {Path} `$HOME/.openclaw/workspace/skills`.
  - @satisfies DES-051
  - @satisfies DES-051

### class `class CodexTarget(CliTarget)` : CliTarget (L204-223)
- @brief Installation adapter for the `codex` CLI.
- @details Installs skills under `$HOME/.codex/skills`; prompt template installation is unsupported.
- @satisfies DES-052
- fn `def skills_dir(self, home: Path | None = None) -> Path` (L214-223)
  - @brief Installation adapter for the `codex` CLI.
  - @brief Resolve the codex user-level skills directory.
  - @details Installs skills under `$HOME/.codex/skills`; prompt template
installation is unsupported.
  - @param home {Path | None} Optional home-directory override.
  - @return {Path} `$HOME/.codex/skills`.
  - @satisfies DES-052
  - @satisfies DES-052

### class `class AntigravityTarget(CliTarget)` : CliTarget (L224-243)
- @brief Installation adapter for Google Antigravity.
- @details Installs skills under `$HOME/.gemini/config/skills`; prompt template installation is unsupported.
- @satisfies DES-053
- fn `def skills_dir(self, home: Path | None = None) -> Path` (L234-243)
  - @brief Installation adapter for Google Antigravity.
  - @brief Resolve the antigravity user-level skills directory.
  - @details Installs skills under `$HOME/.gemini/config/skills`; prompt
template installation is unsupported.
  - @param home {Path | None} Optional home-directory override.
  - @return {Path} `$HOME/.gemini/config/skills`.
  - @satisfies DES-053
  - @satisfies DES-053

### class `class ClaudeTarget(CliTarget)` : CliTarget (L244-272)
- @brief Installation adapter for the `claude` CLI.
- @details Installs skills under `$HOME/.claude/skills` and slash-command prompt files under `$HOME/.claude/commands`.
- @satisfies DES-054
- fn `def skills_dir(self, home: Path | None = None) -> Path` (L254-262)
  - @brief Installation adapter for the `claude` CLI.
  - @brief Resolve the claude user-level skills directory.
  - @details Installs skills under `$HOME/.claude/skills` and slash-command
prompt files under `$HOME/.claude/commands`.
  - @param home {Path | None} Optional home-directory override.
  - @return {Path} `$HOME/.claude/skills`.
  - @satisfies DES-054
  - @satisfies DES-054
- fn `def prompts_dir(self, home: Path | None = None) -> Path` (L263-272)
  - @brief Resolve the claude user-level commands directory.
  - @param home {Path | None} Optional home-directory override.
  - @return {Path} `$HOME/.claude/commands`.
  - @satisfies DES-054

### fn `def resolve_target(name: str) -> CliTarget | None` (L288-298)
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
|`resolve_home`|fn|pub|21-33|def resolve_home(home: Path | None) -> Path|
|`sync_skill_tree`|fn|pub|34-66|def sync_skill_tree(source: Path, destination: Path) -> None|
|`CliTarget`|class|pub|67-154|class CliTarget(ABC)|
|`CliTarget.skills_dir`|fn|pub|81-88|def skills_dir(self, home: Path | None = None) -> Path|
|`CliTarget.prompts_dir`|fn|pub|89-99|def prompts_dir(self, home: Path | None = None) -> Path |...|
|`CliTarget.install_skills`|fn|pub|100-117|def install_skills(self, sources: Iterable[Path], home: P...|
|`CliTarget.install_prompts`|fn|pub|118-122|def install_prompts(|
|`PiTarget`|class|pub|155-183|class PiTarget(CliTarget)|
|`PiTarget.skills_dir`|fn|pub|165-173|def skills_dir(self, home: Path | None = None) -> Path|
|`PiTarget.prompts_dir`|fn|pub|174-183|def prompts_dir(self, home: Path | None = None) -> Path|
|`OpenClawTarget`|class|pub|184-203|class OpenClawTarget(CliTarget)|
|`OpenClawTarget.skills_dir`|fn|pub|194-203|def skills_dir(self, home: Path | None = None) -> Path|
|`CodexTarget`|class|pub|204-223|class CodexTarget(CliTarget)|
|`CodexTarget.skills_dir`|fn|pub|214-223|def skills_dir(self, home: Path | None = None) -> Path|
|`AntigravityTarget`|class|pub|224-243|class AntigravityTarget(CliTarget)|
|`AntigravityTarget.skills_dir`|fn|pub|234-243|def skills_dir(self, home: Path | None = None) -> Path|
|`ClaudeTarget`|class|pub|244-272|class ClaudeTarget(CliTarget)|
|`ClaudeTarget.skills_dir`|fn|pub|254-262|def skills_dir(self, home: Path | None = None) -> Path|
|`ClaudeTarget.prompts_dir`|fn|pub|263-272|def prompts_dir(self, home: Path | None = None) -> Path|
|`resolve_target`|fn|pub|288-298|def resolve_target(name: str) -> CliTarget | None|

