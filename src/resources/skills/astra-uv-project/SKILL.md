---
name: astra-uv-project
description: Create a brand-new Python CLI project from scratch based on Astral uv and uvx, scaffolding the repository from the bundled skell.tgz skeleton with keyword substitution, file renames, management commands, and GitHub release version checking. Use only when a new project must be created from nothing; never use on existing projects.
---

# Astra UV Project

## 1. Purpose and applicability

Scaffold a complete, distributable Python CLI application for a NEW project: extract the bundled skeleton, substitute project keywords, rename skeleton artifacts, implement management commands and the online version-check logic, and leave a repository that builds with Astral `uv`, runs locally through a shell script, installs with `uv tool install`, and executes on-the-fly with `uvx`.

**Trigger.** Apply this skill only when the user asks to create a new Python project based on Astral uv from scratch.

**Exclusions.** Do not apply this skill to existing projects. Maintenance, refactoring, dependency upgrades, or feature work on an existing repository is out of scope: terminate and report the mismatch instead of executing the phases below.

**Bundled asset.** The skeleton archive `assets/skell.tgz` ships inside this skill directory. Resolve it relative to this skill directory, never relative to the process working directory. The archive content is externally maintained input: do not modify, regenerate, repackage, or document it; consume it as-is.

## 2. PHASE 0: System Context and Global Variables (Bootstrap)

Determine the following keywords from the user request or the project context and store them in session context for the whole session. Do not alter the keyword names.

| Keyword | Meaning | Normalization |
| --- | --- | --- |
| `%AUTHOR%` | Author name. | As provided. |
| `%DESCRIPTION%` | Project description. | As provided. |
| `%PROGRAM%` | Long program name. A long form and an abbreviated form may both be present; they coincide only when explicitly specified. | Lowercase. |
| `%SHORTNAME%` | Short program name. A long form and an abbreviated form may both be present; they coincide only when explicitly specified. | Lowercase. |
| `%SRCDIR%` | Source folder name; usually the long program name lowercased. | Lowercase. |
| `%OWNER%` | GitHub repository owner; required to reconstruct the repository URL. Derive from git data or the user request. | As derived. |
| `%REPOSITORY%` | GitHub repository name, typically mixed case; required to reconstruct the repository URL. Derive from git data or the user request. | As derived. |

**Missing-input rule.** Do not invent values. If any keyword cannot be identified clearly and unambiguously from the user request and project context, terminate the process prematurely: report the problem, list every missing keyword, and ask for the missing information before doing any file operation.

## 3. PHASE 1: File System and Initialization

Run the following file operations in this exact order, inside the new project root directory:

1. **Extraction.** Extract every file and directory from `assets/skell.tgz` into the current directory, including empty directories, overwriting any existing file.
2. **Keyword substitution.** Search and replace the keywords `%OWNER%`, `%AUTHOR%`, `%DESCRIPTION%`, `%REPOSITORY%`, `%PROGRAM%`, `%SHORTNAME%`, `%SRCDIR%` with their bootstrap values in exactly these files:
   - `.g.conf`
   - `README.md`
   - `pyproject.toml`
   - `uv.lock`
   - `src/skell/core.py`
   - `scripts/skell.sh`
   - `src/skell/__main__.py`
3. **Renaming.**
   - Rename `scripts/skell.sh` to `scripts/%SHORTNAME%.sh`.
   - Rename the directory `src/skell` to `src/%SRCDIR%`.
   - Note: `src/%SRCDIR%` is the Python package referenced by `pyproject.toml` and executed by `scripts/%SHORTNAME%.sh`; do not use `%SHORTNAME%` for the source directory unless it equals `%SRCDIR%`.

## 4. PHASE 2: Application Architecture

Develop a CLI-based Python application/module compiled and distributed through the **Astral UV Tool / UVX** stack:

- Name the application `%PROGRAM%`.
- Implement the application entrypoint in this phase: the extracted `src/%SRCDIR%/core.py` ships as a comment-only stub while `__init__.py` and `__main__.py` already import `main` from it; define `main` in `core.py` (behavior specified in PHASE 3 and PHASE 4) so the package imports and runs.
- Support local execution through `scripts/%SHORTNAME%.sh`, which delegates to `uv run --project <project root> python -m %SRCDIR%`.
- Package the application so it can be downloaded with `uv` and executed on-the-fly from the web with `uvx`.
- Configure `pyproject.toml` to include every file needed at runtime so the GitHub Actions workflow in `.github/workflows/release-uvx.yml` can build the package correctly.

## 5. PHASE 3: Management Commands Specification

Implement the following management commands independently of the core application logic.

### A) Help system (`--help` / no parameters)

Print the following text in ENGLISH when `--help` is passed or when the application runs without parameters. Use EXACTLY this template:

```text
Usage: %PROGRAM% [command] [options] (x.y.z)

Management Commands:
  --upgrade   - Reinstall %PROGRAM% on Linux; print manual command elsewhere.
  --uninstall - Uninstall %PROGRAM% on Linux; print manual command elsewhere.
  --ver       - Print the %PROGRAM% version.
  --version   - Print the %PROGRAM% version.
  --help      - Print the full help screen or the help text of a specific command.

Commands:
  ...
```

Substitute `%PROGRAM%` with its value and `x.y.z` with the installed version; keep all other text and spacing unchanged. In the template, `Commands:` followed by `...` is the placeholder where the project-specific commands are listed.

### B) Version, upgrade, and uninstall commands

- **`--ver` / `--version`**: print the current version in `x.y.z` format and FORCE the online new-version check, ignoring the delay and the JSON cache file described in PHASE 4.
- **`--upgrade`**:
  - Linux: execute `uv tool install %PROGRAM% --force --from git+https://github.com/%OWNER%/%REPOSITORY%.git`.
  - Other operating systems: do NOT execute the command. Print a warning and show the user the manual command to run.
- **`--uninstall`**:
  - Linux: execute `uv tool uninstall %PROGRAM%`.
  - Other operating systems: do NOT execute the command. Print a warning and show the user the manual command to run.

## 6. PHASE 4: Online Version Check Logic

Implement an automatic new-version check that runs before parsing incoming parameters, except `--ver` / `--version`, which force the check.

**Connection parameters:**

- Endpoint: `https://api.github.com/repos/%OWNER%/%REPOSITORY%/releases/latest`
- HTTP/HTTPS timeout: hardcoded to `2` seconds.

**Caching logic (idle-delay and idle-time):**

- Standard `idle-delay`: hardcoded to `3600` seconds (1 hour).
- Cache file: `$HOME/.cache/%PROGRAM%/check_version_idle-time.json`
- Required JSON structure in the file:
  1. Last successful check timestamp (epoch).
  2. Last successful check timestamp (human-readable).
  3. End-of-block timestamp / `idle-time` = (last timestamp + `idle-delay`) (epoch).
  4. End-of-block timestamp / `idle-time` (human-readable).

**Version-check execution flow:**

1. **Initial decision.** If the JSON file does not exist, or its `idle-time` has expired, or `--ver`/`--version` was passed, perform the HTTP call; otherwise skip the check.
2. **Positive outcome (newer version found).** Print a message in BRIGHT GREEN color reporting "Available Version" versus "Installed Version". Generate or update the JSON file using the standard `idle-delay` (3600 seconds).
3. **Negative outcome / HTTP errors (429, 503, ... any error).** Print an error message in BRIGHT RED color reporting the encountered error. Generate or update the JSON file with an inflated `idle-delay` of `86400` seconds (1 day).

## 7. Verification

Before declaring completion, verify, and report any failure:

1. No literal keyword `%AUTHOR%`, `%DESCRIPTION%`, `%PROGRAM%`, `%SHORTNAME%`, `%SRCDIR%`, `%OWNER%`, or `%REPOSITORY%` remains in any scaffolded file.
2. `scripts/%SHORTNAME%.sh` exists, `src/skell` no longer exists, and `src/%SRCDIR%` exists.
3. Application sources live under `src/%SRCDIR%`.
4. `pyproject.toml` declares the package so that `.github/workflows/release-uvx.yml` can build it (project name, packages discovery, package data).
5. When `uv` is available, run `uv build` (or `uv sync`) as a bounded smoke check and execute one bounded command such as `scripts/%SHORTNAME%.sh --help` or `uv run python -m %SRCDIR% --help` to prove the package imports and runs; when unavailable, record each skipped check with the reason.
