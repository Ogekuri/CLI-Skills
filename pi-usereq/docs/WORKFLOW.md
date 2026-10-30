# Workflow

## Execution Units Index

| ID | Type | Parent Process | Role | Entrypoint(s) | Defining File(s) |
|---|---|---|---|---|---|
| `PROC:main` | process | — | `skills` CLI: dispatch management commands and run automatic release check | `main()` [`src/skills/core.py`]; module trigger `sys.exit(main())` [`src/skills/__main__.py`]; re-export `from .core import main` [`src/skills/__init__.py`] | `src/skills/core.py`, `src/skills/__main__.py`, `src/skills/__init__.py` |
| `PROC:uv` | process | `PROC:main` | child process executing external `uv` tool for `--upgrade` / `--uninstall` | external `uv` executable (no internal entrypoint) | `src/skills/core.py` (spawn site) |

## Execution Units

### `PROC:main`

- **Type**: process
- **Parent Process**: none (main process)
- **Threads**: no explicit threads detected
- **Entrypoint(s)**:
  - `main(argv=None)`: CLI argument dispatch and release-check orchestration [`src/skills/core.py`]
    - module-execution trigger: `sys.exit(main())` [`src/skills/__main__.py`]
    - package re-export: `from .core import main` [`src/skills/__init__.py`]
- **Lifecycle / Trigger**:
  - Start: OS launches the `skills` process (`python -m skills` or console script); `main()` executes once.
  - Loop/Block: no persistent loop; single-pass dispatch. `check_version()` may block on network/file I/O; `_manage()` blocks on `subprocess.run` until the child exits.
  - Stop: `main()` returns an `int` exit code; module entry propagates it via `sys.exit`.
- **Internal Call-Trace Tree**:
  - `main(argv=None)`: CLI dispatch; run release check, then route to help/version/manage/error path [`src/skills/core.py`]
    - `check_version(force=...)`: automatic release-check decision; `force=True` when `--ver`/`--version` present [`src/skills/core.py`]
      - `cache_path()`: resolve cache file path [`src/skills/core.py`]
      - `_version(...)`: parse remote `tag_name` to version tuple (HTTP-success branch) [`src/skills/core.py`]
      - `_version(...)`: parse installed `__version__` to version tuple (HTTP-success branch) [`src/skills/core.py`]
      - `_human(...)`: format last-success epoch to ISO-8601 string [`src/skills/core.py`]
      - `_human(...)`: format idle-expiration epoch to ISO-8601 string [`src/skills/core.py`]
    - `_manage(UPGRADE)`: execute external `uv tool install ...` (`--upgrade` branch) [`src/skills/core.py`]
    - `_manage(UNINSTALL)`: execute external `uv tool uninstall ...` (`--uninstall` branch) [`src/skills/core.py`]
- **External Boundaries**:
  - stdout/stderr `print()` (help template, version, status/error messages) [`src/skills/core.py`]
  - cache read: `Path.open` + `json.load` [`src/skills/core.py`]
  - cache write: `Path.parent.mkdir` + `Path.write_text` [`src/skills/core.py`]
  - HTTP GET `https://api.github.com/repos/Ogekuri/SKILLs/releases/latest` via `urllib.request.Request` / `urlopen` (timeout 2 s) [`src/skills/core.py`]
  - regex version parse `re.fullmatch` [`src/skills/core.py`]
  - time/date formatting `time.time` + `datetime.fromtimestamp` [`src/skills/core.py`]
  - OS platform check `sys.platform.startswith("linux")` [`src/skills/core.py`]
  - child-process spawn `subprocess.run` [`src/skills/core.py`]

### `PROC:uv`

- **Type**: process
- **Parent Process**: `PROC:main`
- **Threads**: no explicit threads detected
- **Entrypoint(s)**: external `uv` executable (no internal function defined under `src/`)
- **Lifecycle / Trigger**:
  - Start: spawned by `subprocess.run` in `_manage()` with argv `UPGRADE` or `UNINSTALL` [`src/skills/core.py`]
  - Loop/Block: child runs to completion while parent blocks.
  - Stop: child exits; returncode is returned to `_manage()`.
- **Internal Call-Trace Tree**: none (no internal functions; target implementation external)
- **External Boundaries**: `uv` executable (tool install / tool uninstall)

## Communication Edges

| ID | Direction | Mechanism | Endpoint / Channel | Payload / Data-Shape | Declaration File(s) |
|---|---|---|---|---|---|
| `EDGE:main→uv-install` | `PROC:main` → `PROC:uv` | OS process spawn (blocking `subprocess.run`) | child argv `["uv","tool","install","skills","--force","--from","git+https://github.com/Ogekuri/SKILLs.git"]` | `UPGRADE` `list[str]` in; returncode `int` out | `src/skills/core.py` |
| `EDGE:main→uv-uninstall` | `PROC:main` → `PROC:uv` | OS process spawn (blocking `subprocess.run`) | child argv `["uv","tool","uninstall","skills"]` | `UNINSTALL` `list[str]` in; returncode `int` out | `src/skills/core.py` |
