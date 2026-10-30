# Workflow

## Execution Units Index

| ID | Type | Parent Process | Role | Entrypoint(s) | Defining File(s) |
|---|---|---|---|---|---|
| `PROC:main` | process | — | `skills` CLI: dispatch management, enable/disable, installation, and show commands; run automatic release check | `main()` [`src/skills/core.py`]; module trigger `sys.exit(main())` [`src/skills/__main__.py`]; re-export `from .core import main` [`src/skills/__init__.py`] | `src/skills/core.py`, `src/skills/settings.py`, `src/skills/targets.py`, `src/skills/installer.py`, `src/skills/catalog.py`, `src/skills/show.py`, `src/skills/__main__.py`, `src/skills/__init__.py` |
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
  - `main(argv=None)`: CLI dispatch; run release check, then route to help/version/manage/enable/disable/install/error path [`src/skills/core.py`]
    - `check_version(force=...)`: automatic release-check decision; `force=True` when `--ver`/`--version` present [`src/skills/core.py`]
      - `cache_path()`: resolve cache file path [`src/skills/core.py`]
      - `_version(...)`: parse remote `tag_name` to version tuple (HTTP-success branch) [`src/skills/core.py`]
      - `_version(...)`: parse installed `__version__` to version tuple (HTTP-success branch) [`src/skills/core.py`]
      - `_human(...)`: format last-success epoch to ISO-8601 string [`src/skills/core.py`]
      - `_human(...)`: format idle-expiration epoch to ISO-8601 string [`src/skills/core.py`]
    - `_manage(UPGRADE)`: execute external `uv tool install ...` (`--upgrade` branch) [`src/skills/core.py`]
    - `_manage(UNINSTALL)`: execute external `uv tool uninstall ...` (`--uninstall` branch) [`src/skills/core.py`]
    - `_enable(name)`: resolve adapter and persist enabled CLI (`enable <cli name>` branch) [`src/skills/core.py`]
      - `_unsupported(name)`: build unsupported-CLI diagnostic (unsupported branch) [`src/skills/core.py`]
      - `resolve_target(name)`: normalize name and look up adapter [`src/skills/targets.py`]
      - `load_config(home)`: load normalized user configuration [`src/skills/settings.py`]
        - `config_path(home)`: resolve `$HOME/.config/skills/config.json` [`src/skills/settings.py`]
        - `_unique_strings(value)`: normalize enabled names and prompt filename lists [`src/skills/settings.py`]
      - `save_config(config, home)`: persist enabled CLI names [`src/skills/settings.py`]
        - `config_path(home)`: resolve configuration file path [`src/skills/settings.py`]
    - `_disable(name)`: resolve adapter and remove enabled CLI (`disable <cli name>` branch) [`src/skills/core.py`]
      - `_unsupported(name)`: build unsupported-CLI diagnostic (unsupported branch) [`src/skills/core.py`]
      - `resolve_target(name)`: normalize name and look up adapter [`src/skills/targets.py`]
      - `load_config(home)`: load normalized user configuration [`src/skills/settings.py`]
        - `config_path(home)`: resolve configuration file path [`src/skills/settings.py`]
        - `_unique_strings(value)`: normalize enabled names and prompt filename lists [`src/skills/settings.py`]
      - `save_config(config, home)`: persist enabled CLI names without the disabled CLI [`src/skills/settings.py`]
        - `config_path(home)`: resolve configuration file path [`src/skills/settings.py`]
    - `_install(home)`: install resources for enabled CLIs (`install` branch) [`src/skills/core.py`]
      - `install_enabled(home)`: orchestrate per-CLI installation [`src/skills/installer.py`]
        - `load_config(home)`: load enabled CLI names and prompt records [`src/skills/settings.py`]
          - `config_path(home)`: resolve configuration file path [`src/skills/settings.py`]
          - `_unique_strings(value)`: normalize enabled names and prompt filename lists [`src/skills/settings.py`]
        - `build_catalog()`: build manifest entries from bundled resources (non-empty enabled set) [`src/skills/catalog.py`]
          - `_discover_skills(root)`: collect sorted `SKILL.md` paths [`src/skills/catalog.py`]
          - `_parse_frontmatter(text)`: extract `name` and `description` per skill [`src/skills/catalog.py`]
          - `_discover_prompts(root)`: collect sorted prompt candidate paths [`src/skills/catalog.py`]
          - `_parse_frontmatter(text)`: extract `name` and `description` per prompt [`src/skills/catalog.py`]
        - `resolve_target(name)`: normalize enabled name and look up adapter [`src/skills/targets.py`]
        - `install_target(target, catalog, previous, home=home)`: install one CLI target [`src/skills/installer.py`]
          - `_skill_directories(resources_root, entries)`: validate manifest skill paths and deduplicate directories [`src/skills/installer.py`]
          - `_prompt_files(resources_root, entries)`: validate manifest prompt paths and reject filename collisions [`src/skills/installer.py`]
          - `install_skills(sources, home)`: synchronize skill directories for the adapter [`src/skills/targets.py`]
            - `skills_dir(home)`: resolve adapter skill destination [`src/skills/targets.py`]
              - `resolve_home(home)`: resolve explicit or platform home [`src/skills/targets.py`]
            - `sync_skill_tree(source, destination)`: copy packaged tree, overwrite files, prune absent destination entries [`src/skills/targets.py`]
          - `install_prompts(sources, previous, home)`: copy prompts and delete stale managed prompt files [`src/skills/targets.py`]
            - `prompts_dir(home)`: resolve adapter prompt destination or `None` when unsupported [`src/skills/targets.py`]
              - `resolve_home(home)`: resolve explicit or platform home [`src/skills/targets.py`]
        - `save_config(config, home)`: persist installed prompt records and enabled CLI names (per successful target) [`src/skills/settings.py`]
          - `config_path(home)`: resolve configuration file path [`src/skills/settings.py`]
    - `_show(home)`: print packaged resources, CLI configuration, and installation status (`show` branch) [`src/skills/core.py`]
      - `build_show(home)`: render the three `show` tables [`src/skills/show.py`]
        - `build_catalog()`: load manifest skill and prompt entries [`src/skills/catalog.py`]
          - `_discover_skills(root)`: collect sorted `SKILL.md` paths [`src/skills/catalog.py`]
          - `_parse_frontmatter(text)`: extract `name` and `description` per skill [`src/skills/catalog.py`]
          - `_discover_prompts(root)`: collect sorted prompt candidate paths [`src/skills/catalog.py`]
          - `_parse_frontmatter(text)`: extract `name` and `description` per prompt [`src/skills/catalog.py`]
        - `load_config(home)`: load normalized user configuration [`src/skills/settings.py`]
          - `config_path(home)`: resolve configuration file path [`src/skills/settings.py`]
          - `_unique_strings(value)`: normalize enabled names and prompt filename lists [`src/skills/settings.py`]
        - `_resource_rows(catalog)`: build packaged resource inventory rows [`src/skills/show.py`]
        - `render_table(...)`: render wrapped ASCII inventory table [`src/skills/show.py`]
          - `_wrap(text, width)`: wrap cell text to column width [`src/skills/show.py`]
        - `_cli_rows(config, home)`: build CLI enabled-state and destination-path rows [`src/skills/show.py`]
          - `skills_dir(home)`: resolve adapter skill destination [`src/skills/targets.py`]
            - `resolve_home(home)`: resolve explicit or platform home [`src/skills/targets.py`]
          - `prompts_dir(home)`: resolve adapter prompt destination or `None` when unsupported [`src/skills/targets.py`]
            - `resolve_home(home)`: resolve explicit or platform home [`src/skills/targets.py`]
        - `render_table(...)`: render wrapped CLI configuration table [`src/skills/show.py`]
          - `_wrap(text, width)`: wrap cell text to column width [`src/skills/show.py`]
        - `_install_rows(catalog, config, home)`: build per-resource per-CLI status rows [`src/skills/show.py`]
          - `_skill_status(source, destination)`: compare packaged skill tree with installed copy [`src/skills/show.py`]
            - `_files_match(source, destination)`: compare packaged and installed file bytes [`src/skills/show.py`]
          - `_files_match(source, destination)`: compare packaged and installed prompt bytes [`src/skills/show.py`]
        - `render_table(...)`: render wrapped installation status table [`src/skills/show.py`]
          - `_wrap(text, width)`: wrap cell text to column width [`src/skills/show.py`]
- **External Boundaries**:
  - stdout/stderr `print()` (help template, version, status/error messages) [`src/skills/core.py`]
  - cache read: `Path.open` + `json.load` [`src/skills/core.py`]
  - cache write: `Path.parent.mkdir` + `Path.write_text` [`src/skills/core.py`]
  - HTTP GET `https://api.github.com/repos/Ogekuri/SKILLs/releases/latest` via `urllib.request.Request` / `urlopen` (timeout 2 s) [`src/skills/core.py`]
  - regex version parse `re.fullmatch` [`src/skills/core.py`]
  - time/date formatting `time.time` + `datetime.fromtimestamp` [`src/skills/core.py`]
  - OS platform check `sys.platform.startswith("linux")` [`src/skills/core.py`]
  - child-process spawn `subprocess.run` [`src/skills/core.py`]
  - user configuration read/write: `Path.read_text`, `Path.write_text`, `Path.replace` [`src/skills/settings.py`]
  - manifest discovery: `importlib.resources.files`, `Path.rglob`, `Path.read_text` [`src/skills/catalog.py`]
  - skill synchronization: `shutil.copytree`, `Path.mkdir`, `Path.rglob`, `Path.rmdir`, `Path.unlink` [`src/skills/targets.py`]
  - prompt synchronization: `shutil.copy2`, `Path.mkdir`, `Path.unlink` [`src/skills/targets.py`]
  - installation scan: `Path.is_dir`, `Path.is_file`, `Path.rglob`, `Path.read_bytes` [`src/skills/show.py`]
  - table rendering: `str.ljust` [`src/skills/show.py`]

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
