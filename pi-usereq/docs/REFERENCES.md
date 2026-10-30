# Files Structure
```
.
└── src
    ├── resources
    │   └── __init__.py
    └── skills
        ├── __init__.py
        ├── __main__.py
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

