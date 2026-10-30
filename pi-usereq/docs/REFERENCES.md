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
        └── core.py
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

# core.py | Python | 131L | 9 symbols | 10 imports | 2 comments
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
```

## Definitions

- var `ENDPOINT = "https://api.github.com/repos/Ogekuri/SKILLs/releases/latest"` (L16)
- var `UPGRADE = ["uv", "tool", "install", "skills", "--force", "--from", "git+https://github.com/Ogekuri/SKILLs.git"]` (L17)
- var `UNINSTALL = ["uv", "tool", "uninstall", "skills"]` (L18)
### fn `def cache_path() -> Path` (L32-35)

### fn `def _human(timestamp: float | None) -> str | None` `priv` (L36-39)

### fn `def _version(value: str) -> tuple[int, int, int]` `priv` (L40-46)

### fn `def check_version(force: bool = False) -> None` (L47-94)

### fn `def _manage(command: list[str]) -> int` `priv` (L95-105)

### fn `def main(argv: list[str] | None = None) -> int` (L106-132)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`ENDPOINT`|var|pub|16||
|`UPGRADE`|var|pub|17||
|`UNINSTALL`|var|pub|18||
|`cache_path`|fn|pub|32-35|def cache_path() -> Path|
|`_human`|fn|priv|36-39|def _human(timestamp: float | None) -> str | None|
|`_version`|fn|priv|40-46|def _version(value: str) -> tuple[int, int, int]|
|`check_version`|fn|pub|47-94|def check_version(force: bool = False) -> None|
|`_manage`|fn|priv|95-105|def _manage(command: list[str]) -> int|
|`main`|fn|pub|106-132|def main(argv: list[str] | None = None) -> int|

