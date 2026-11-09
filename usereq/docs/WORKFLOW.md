# Workflow

## Execution Units Index

| ID | Type | Parent Process | Role | Entrypoint(s) | Defining File(s) |
|---|---|---|---|---|---|
| `PROC:main` | process | — | `cli-skills` CLI: dispatch management, enable/disable, installation, uninstallation, and show commands; run automatic release check | `main()` [`src/cli_skills/core.py`]; module trigger `sys.exit(main())` [`src/cli_skills/__main__.py`]; re-export `from .core import main` [`src/cli_skills/__init__.py`]; console-script launchers `cli-skills` and `skills` bound to `main()` [`pyproject.toml`] | `src/cli_skills/core.py`, `src/cli_skills/settings.py`, `src/cli_skills/targets.py`, `src/cli_skills/installer.py`, `src/cli_skills/catalog.py`, `src/cli_skills/show.py`, `src/cli_skills/__main__.py`, `src/cli_skills/__init__.py` |
| `PROC:uv` | process | `PROC:main` | child process executing external `uv` tool for `--upgrade` / `--uninstall` | external `uv` executable (no internal entrypoint) | `src/cli_skills/core.py` (spawn site) |
| `PROC:cli-skills-install` | process | `PROC:main` | child process executing the freshly upgraded `cli-skills` executable to install bundled resources into enabled CLIs after `--upgrade` | external `cli-skills` executable (no internal entrypoint) | `src/cli_skills/core.py` (spawn site) |

## Execution Units

### `PROC:main`

- **Type**: process
- **Parent Process**: none (main process)
- **Threads**: no explicit threads detected
- **Entrypoint(s)**:
  - `main(argv=None)`: CLI argument dispatch and release-check orchestration [`src/cli_skills/core.py`]
    - module-execution trigger: `sys.exit(main())` [`src/cli_skills/__main__.py`]
    - package re-export: `from .core import main` [`src/cli_skills/__init__.py`]
    - console-script launchers: `cli-skills` and `skills` console scripts bound to the same `main()` entry point [`pyproject.toml`]
- **Lifecycle / Trigger**:
  - Start: OS launches the `cli-skills` process (`python -m cli_skills` or console script); `main()` executes once.
  - Loop/Block: no persistent loop; single-pass dispatch. `check_version()` may block on network/file I/O; `_manage()` blocks on `subprocess.run` until the child exits.
  - Stop: `main()` returns an `int` exit code; module entry propagates it via `sys.exit`.
- **Internal Call-Trace Tree**:
  - `main(argv=None)`: CLI dispatch; run release check, then route to help/version/manage/enable/disable/install/uninstall/show/error path [`src/cli_skills/core.py`]
    - `check_version(force=...)`: automatic release-check decision against PyPI; `force=True` when `--ver`/`--version` present [`src/cli_skills/core.py`]
      - `cache_path()`: resolve cache file path [`src/cli_skills/core.py`]
      - `fetch_pypi_latest()`: fetch the newest PyPI version (check branch) [`src/cli_skills/core.py`]
        - `_http_json(url, accept)`: HTTP GET and JSON decode [`src/cli_skills/core.py`]
      - `_version(...)`: parse PyPI latest version to version tuple (HTTP-success branch) [`src/cli_skills/core.py`]
      - `_version(...)`: parse installed `__version__` to version tuple (HTTP-success branch) [`src/cli_skills/core.py`]
      - `_human(...)`: format last-success epoch to ISO-8601 string [`src/cli_skills/core.py`]
      - `_human(...)`: format idle-expiration epoch to ISO-8601 string [`src/cli_skills/core.py`]
    - `fetch_pypi_latest()`: fetch the newest PyPI version (`--ver`/`--version` report line) [`src/cli_skills/core.py`]
      - `_http_json(url, accept)`: HTTP GET and JSON decode [`src/cli_skills/core.py`]
    - `fetch_github_latest()`: fetch the newest GitHub release normalized to `x.y.z` (`--ver`/`--version` report line) [`src/cli_skills/core.py`]
      - `_http_json(url, accept)`: HTTP GET and JSON decode [`src/cli_skills/core.py`]
    - `_failure_reason(exc)`: normalize a GitHub fetch failure to the actual-error reason printed as `GitHub latest: unknown (<reason>)` (`--ver`/`--version` failure branch) [`src/cli_skills/core.py`]
    - `_upgrade_command(options)`: resolve the accepted `--dev`/`--develop`/`--force` option combination to the upgrade argv, returning `None` for invalid combinations (`--upgrade` branch) [`src/cli_skills/core.py`]
    - `_run_upgrade(UPGRADE)`: execute external `uv tool install ...` from PyPI without force options and chain the install (`--upgrade` branch) [`src/cli_skills/core.py`]
      - `_post_upgrade_install(home)`: chain the post-upgrade install when the upgrade succeeded on Linux [`src/cli_skills/core.py`]
        - `load_config(home)`: load the enabled CLI set to gate the chained install [`src/cli_skills/settings.py`]
          - `config_path(home)`: resolve configuration file path [`src/cli_skills/settings.py`]
          - `_unique_strings(value)`: normalize enabled CLI names [`src/cli_skills/settings.py`]
        - `_manage(SKILLS_INSTALL)`: execute external `cli-skills install` child when the enabled set is non-empty [`src/cli_skills/core.py`]
    - `_run_upgrade(UPGRADE_FORCE)`: execute external forced `uv tool install ... --force --reinstall --refresh` from PyPI and chain the install (`--upgrade --force` branch) [`src/cli_skills/core.py`]
      - `_post_upgrade_install(home)`: chain the post-upgrade install when the upgrade succeeded on Linux [`src/cli_skills/core.py`]
        - `load_config(home)`: load the enabled CLI set to gate the chained install [`src/cli_skills/settings.py`]
          - `config_path(home)`: resolve configuration file path [`src/cli_skills/settings.py`]
          - `_unique_strings(value)`: normalize enabled CLI names [`src/cli_skills/settings.py`]
        - `_manage(SKILLS_INSTALL)`: execute external `cli-skills install` child when the enabled set is non-empty [`src/cli_skills/core.py`]
    - `_run_upgrade(UPGRADE_DEVELOP)`: execute external `uv tool install ...` from GitHub without force options and chain the install (`--upgrade --dev` / `--upgrade --develop` branch) [`src/cli_skills/core.py`]
      - `_post_upgrade_install(home)`: chain the post-upgrade install when the upgrade succeeded on Linux [`src/cli_skills/core.py`]
        - `load_config(home)`: load the enabled CLI set to gate the chained install [`src/cli_skills/settings.py`]
          - `config_path(home)`: resolve configuration file path [`src/cli_skills/settings.py`]
          - `_unique_strings(value)`: normalize enabled CLI names [`src/cli_skills/settings.py`]
        - `_manage(SKILLS_INSTALL)`: execute external `cli-skills install` child when the enabled set is non-empty [`src/cli_skills/core.py`]
    - `_run_upgrade(UPGRADE_DEVELOP_FORCE)`: execute external forced `uv tool install ... --force --reinstall --refresh` from GitHub and chain the install (`--upgrade` with `--dev`/`--develop` and `--force` branch) [`src/cli_skills/core.py`]
      - `_post_upgrade_install(home)`: chain the post-upgrade install when the upgrade succeeded on Linux [`src/cli_skills/core.py`]
        - `load_config(home)`: load the enabled CLI set to gate the chained install [`src/cli_skills/settings.py`]
          - `config_path(home)`: resolve configuration file path [`src/cli_skills/settings.py`]
          - `_unique_strings(value)`: normalize enabled CLI names [`src/cli_skills/settings.py`]
        - `_manage(SKILLS_INSTALL)`: execute external `cli-skills install` child when the enabled set is non-empty [`src/cli_skills/core.py`]
    - `_manage(UNINSTALL)`: execute external `uv tool uninstall ...` (`--uninstall` branch) [`src/cli_skills/core.py`]
    - `_enable(name)`: resolve adapter and persist enabled CLI (`enable <cli name>` branch) [`src/cli_skills/core.py`]
      - `_unsupported(name)`: build unsupported-CLI diagnostic (unsupported branch) [`src/cli_skills/core.py`]
      - `resolve_target(name)`: normalize name and look up adapter [`src/cli_skills/targets.py`]
      - `load_config(home)`: load normalized user configuration [`src/cli_skills/settings.py`]
        - `config_path(home)`: resolve `$HOME/.config/cli-skills/config.json` [`src/cli_skills/settings.py`]
        - `_unique_strings(value)`: normalize enabled CLI names [`src/cli_skills/settings.py`]
      - `save_config(config, home)`: persist enabled CLI names [`src/cli_skills/settings.py`]
        - `config_path(home)`: resolve configuration file path [`src/cli_skills/settings.py`]
    - `_disable(name)`: resolve adapter and remove enabled CLI (`disable <cli name>` branch) [`src/cli_skills/core.py`]
      - `_unsupported(name)`: build unsupported-CLI diagnostic (unsupported branch) [`src/cli_skills/core.py`]
      - `resolve_target(name)`: normalize name and look up adapter [`src/cli_skills/targets.py`]
      - `load_config(home)`: load normalized user configuration [`src/cli_skills/settings.py`]
        - `config_path(home)`: resolve configuration file path [`src/cli_skills/settings.py`]
        - `_unique_strings(value)`: normalize enabled CLI names [`src/cli_skills/settings.py`]
      - `save_config(config, home)`: persist enabled CLI names without the disabled CLI [`src/cli_skills/settings.py`]
        - `config_path(home)`: resolve configuration file path [`src/cli_skills/settings.py`]
    - `_install(home)`: install resources for enabled CLIs and print per-CLI installed skill counts and names (`install` branch) [`src/cli_skills/core.py`]
      - `install_enabled(home)`: orchestrate per-CLI installation [`src/cli_skills/installer.py`]
        - `load_config(home)`: load enabled CLI names [`src/cli_skills/settings.py`]
          - `config_path(home)`: resolve configuration file path [`src/cli_skills/settings.py`]
          - `_unique_strings(value)`: normalize enabled CLI names [`src/cli_skills/settings.py`]
        - `build_catalog()`: build manifest entries from bundled resources (non-empty enabled set) [`src/cli_skills/catalog.py`]
          - `_discover_skills(root)`: collect sorted `SKILL.md` paths [`src/cli_skills/catalog.py`]
          - `validate_skill_layout(skill_dir)`: reject non-canonical skill support layout [`src/cli_skills/catalog.py`]
          - `_parse_frontmatter(text)`: extract `name` and `description` per skill [`src/cli_skills/catalog.py`]
        - `resolve_target(name)`: normalize enabled name and look up adapter [`src/cli_skills/targets.py`]
        - `install_target(target, catalog, home=home)`: install one CLI target [`src/cli_skills/installer.py`]
          - `_skill_directories(resources_root, entries)`: validate manifest skill paths and deduplicate directories [`src/cli_skills/installer.py`]
          - `install_skills(sources, home)`: synchronize skill directories for the adapter [`src/cli_skills/targets.py`]
            - `skills_dir(home)`: resolve adapter skill destination [`src/cli_skills/targets.py`]
              - `resolve_home(home)`: resolve explicit or platform home [`src/cli_skills/targets.py`]
            - `sync_skill_tree(source, destination)`: copy packaged tree, overwrite files, prune absent destination entries [`src/cli_skills/targets.py`]
    - `_uninstall(home)`: remove installed resources for enabled CLIs (`uninstall` branch) [`src/cli_skills/core.py`]
      - `uninstall_enabled(home)`: orchestrate per-CLI uninstallation [`src/cli_skills/installer.py`]
        - `load_config(home)`: load enabled CLI names [`src/cli_skills/settings.py`]
          - `config_path(home)`: resolve configuration file path [`src/cli_skills/settings.py`]
          - `_unique_strings(value)`: normalize enabled CLI names [`src/cli_skills/settings.py`]
        - `build_catalog()`: build manifest entries from bundled resources (non-empty enabled set) [`src/cli_skills/catalog.py`]
          - `_discover_skills(root)`: collect sorted `SKILL.md` paths [`src/cli_skills/catalog.py`]
          - `validate_skill_layout(skill_dir)`: reject non-canonical skill support layout [`src/cli_skills/catalog.py`]
          - `_parse_frontmatter(text)`: extract `name` and `description` per skill [`src/cli_skills/catalog.py`]
        - `resolve_target(name)`: normalize enabled name and look up adapter [`src/cli_skills/targets.py`]
        - `uninstall_target(target, catalog, home=home)`: uninstall one CLI target [`src/cli_skills/installer.py`]
          - `_skill_directories(resources_root, entries)`: validate manifest skill paths and deduplicate directories [`src/cli_skills/installer.py`]
          - `remove_skills(names, home)`: delete manifest skill directories for the adapter [`src/cli_skills/targets.py`]
            - `skills_dir(home)`: resolve adapter skill destination [`src/cli_skills/targets.py`]
              - `resolve_home(home)`: resolve explicit or platform home [`src/cli_skills/targets.py`]
    - `_show(home)`: print packaged resources, CLI configuration, and installation status (`show` branch) [`src/cli_skills/core.py`]
      - `build_show(home)`: render the three `show` tables [`src/cli_skills/show.py`]
        - `build_catalog()`: load manifest skill entries [`src/cli_skills/catalog.py`]
          - `_discover_skills(root)`: collect sorted `SKILL.md` paths [`src/cli_skills/catalog.py`]
          - `validate_skill_layout(skill_dir)`: reject non-canonical skill support layout [`src/cli_skills/catalog.py`]
          - `_parse_frontmatter(text)`: extract `name` and `description` per skill [`src/cli_skills/catalog.py`]
        - `load_config(home)`: load normalized user configuration [`src/cli_skills/settings.py`]
          - `config_path(home)`: resolve configuration file path [`src/cli_skills/settings.py`]
          - `_unique_strings(value)`: normalize enabled CLI names [`src/cli_skills/settings.py`]
        - `_resource_rows(catalog)`: build packaged resource inventory rows [`src/cli_skills/show.py`]
        - `render_table(...)`: render wrapped box-drawing inventory table [`src/cli_skills/show.py`]
          - `_wrap(text, width)`: wrap cell text to column width [`src/cli_skills/show.py`]
        - `_cli_rows(config, home)`: build CLI enabled-state and home-relative skills path rows [`src/cli_skills/show.py`]
          - `resolve_home(home)`: resolve the home root used to relativize skills paths [`src/cli_skills/targets.py`]
          - `skills_dir(home)`: resolve adapter skill destination [`src/cli_skills/targets.py`]
            - `resolve_home(home)`: resolve explicit or platform home [`src/cli_skills/targets.py`]
        - `render_table(...)`: render wrapped CLI configuration table [`src/cli_skills/show.py`]
          - `_wrap(text, width)`: wrap cell text to column width [`src/cli_skills/show.py`]
        - `_install_rows(catalog, config, home)`: build per-skill per-enabled-CLI status rows [`src/cli_skills/show.py`]
          - `_skill_status(source, destination)`: compare packaged skill tree with installed copy [`src/cli_skills/show.py`]
            - `_files_match(source, destination)`: compare packaged and installed file bytes [`src/cli_skills/show.py`]
        - `render_table(...)`: render wrapped installation status table [`src/cli_skills/show.py`]
          - `_wrap(text, width)`: wrap cell text to column width [`src/cli_skills/show.py`]
- **External Boundaries**:
  - stdout/stderr `print()` (help template, version, status/error messages) [`src/cli_skills/core.py`]
  - cache read: `Path.open` + `json.load` [`src/cli_skills/core.py`]
  - cache write: `Path.parent.mkdir` + `Path.write_text` [`src/cli_skills/core.py`]
  - HTTP GET `https://pypi.org/pypi/cli-skills/json` via `urllib.request.Request` / `urlopen` (timeout 2 s; automatic release check and `--ver`/`--version` report) [`src/cli_skills/core.py`]
  - HTTP GET `https://api.github.com/repos/Ogekuri/CLI-Skills/releases/latest` via `urllib.request.Request` / `urlopen` (timeout 2 s; `--ver`/`--version` report and `--dev` upgrade source) [`src/cli_skills/core.py`]
  - HTTP error-body decode `HTTPError.read` + `json.loads` (GitHub failure `message` extraction) [`src/cli_skills/core.py`]
  - regex version parse `re.fullmatch` [`src/cli_skills/core.py`]
  - time/date formatting `time.time` + `datetime.fromtimestamp` [`src/cli_skills/core.py`]
  - OS platform check `sys.platform.startswith("linux")` [`src/cli_skills/core.py`]
  - child-process spawn `subprocess.run` [`src/cli_skills/core.py`]
  - user configuration read/write: `Path.read_text`, `Path.write_text`, `Path.replace` [`src/cli_skills/settings.py`]
  - manifest discovery: `importlib.resources.files`, `Path.rglob`, `Path.read_text` [`src/cli_skills/catalog.py`]
  - skill layout validation: `Path.iterdir` [`src/cli_skills/catalog.py`]
  - skill synchronization: `shutil.copytree`, `Path.mkdir`, `Path.rglob`, `Path.rmdir`, `Path.unlink` [`src/cli_skills/targets.py`]
  - managed skill removal: `shutil.rmtree` [`src/cli_skills/targets.py`]
  - installation scan: `Path.is_dir`, `Path.is_file`, `Path.rglob`, `Path.read_bytes` [`src/cli_skills/show.py`]
  - table rendering: `str.ljust` [`src/cli_skills/show.py`]

### `PROC:uv`

- **Type**: process
- **Parent Process**: `PROC:main`
- **Threads**: no explicit threads detected
- **Entrypoint(s)**: external `uv` executable (no internal function defined under `src/`)
- **Lifecycle / Trigger**:
  - Start: spawned by `subprocess.run` in `_manage()` with argv `UPGRADE`, `UPGRADE_FORCE`, `UPGRADE_DEVELOP`, `UPGRADE_DEVELOP_FORCE`, or `UNINSTALL` [`src/cli_skills/core.py`]
  - Loop/Block: child runs to completion while parent blocks.
  - Stop: child exits; returncode is returned to `_manage()`.
- **Internal Call-Trace Tree**: none (no internal functions; target implementation external)
- **External Boundaries**: `uv` executable (tool install / tool uninstall)

### `PROC:cli-skills-install`

- **Type**: process
- **Parent Process**: `PROC:main`
- **Threads**: no explicit threads detected
- **Entrypoint(s)**: external `cli-skills` executable (no internal function defined under `src/` for the child)
- **Lifecycle / Trigger**:
  - Start: spawned by `subprocess.run` in `_post_upgrade_install()` with argv `SKILLS_INSTALL` after a successful Linux `--upgrade` with or without `--dev` when the enabled configuration is non-empty [`src/cli_skills/core.py`]
  - Loop/Block: child runs to completion while parent blocks.
  - Stop: child exits; returncode is returned to `_post_upgrade_install()` and propagated as the `--upgrade` exit code.
- **Internal Call-Trace Tree**: none (no internal functions; the child runs the freshly upgraded external `cli-skills` package)
- **External Boundaries**: `cli-skills` executable (`install` command: manifest-driven skill synchronization with per-CLI count and installed-name report)

## Communication Edges

| ID | Direction | Mechanism | Endpoint / Channel | Payload / Data-Shape | Declaration File(s) |
|---|---|---|---|---|---|
| `EDGE:main→uv-install` | `PROC:main` → `PROC:uv` | OS process spawn (blocking `subprocess.run`) | child argv `["uv","tool","install","cli-skills"]` | `UPGRADE` `list[str]` in; returncode `int` out | `src/cli_skills/core.py` |
| `EDGE:main→uv-install-force` | `PROC:main` → `PROC:uv` | OS process spawn (blocking `subprocess.run`) | child argv `["uv","tool","install","cli-skills","--force","--reinstall","--refresh"]` | `UPGRADE_FORCE` `list[str]` in; returncode `int` out | `src/cli_skills/core.py` |
| `EDGE:main→uv-install-develop` | `PROC:main` → `PROC:uv` | OS process spawn (blocking `subprocess.run`) | child argv `["uv","tool","install","cli-skills","--from","git+https://github.com/Ogekuri/CLI-Skills.git"]` | `UPGRADE_DEVELOP` `list[str]` in; returncode `int` out | `src/cli_skills/core.py` |
| `EDGE:main→uv-install-develop-force` | `PROC:main` → `PROC:uv` | OS process spawn (blocking `subprocess.run`) | child argv `["uv","tool","install","cli-skills","--force","--reinstall","--refresh","--from","git+https://github.com/Ogekuri/CLI-Skills.git"]` | `UPGRADE_DEVELOP_FORCE` `list[str]` in; returncode `int` out | `src/cli_skills/core.py` |
| `EDGE:main→uv-uninstall` | `PROC:main` → `PROC:uv` | OS process spawn (blocking `subprocess.run`) | child argv `["uv","tool","uninstall","cli-skills"]` | `UNINSTALL` `list[str]` in; returncode `int` out | `src/cli_skills/core.py` |
| `EDGE:main→cli-skills-install` | `PROC:main` → `PROC:cli-skills-install` | OS process spawn (blocking `subprocess.run` via `_manage`) | child argv `["cli-skills","install"]` | `SKILLS_INSTALL` `list[str]` in; returncode `int` out | `src/cli_skills/core.py` |
