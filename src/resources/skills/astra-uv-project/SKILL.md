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

**Validation gate (runs before every file operation).** First normalize the resolved values: trim surrounding whitespace, then lowercase `%PROGRAM%`, `%SHORTNAME%`, and `%SRCDIR%` as listed in the table. Then check every value against the rules below. If any check fails, terminate exactly like a missing keyword: report every invalid value with the reason it failed, request corrected values, and perform no extraction, write, rename, or deletion.

- `%PROGRAM%` and `%SHORTNAME%`: non-empty; only lowercase ASCII letters, digits, hyphens, and underscores; MUST start with a letter; MUST NOT contain whitespace, path separators (`/` or `\`), the dot segments `.` or `..`, shell metacharacters, or line breaks.
- `%SRCDIR%`: non-empty; only lowercase ASCII letters, digits, and underscores; MUST start with a letter; MUST NOT contain a hyphen or any character rejected above, so it always forms a valid importable Python package name.
- `%OWNER%` and `%REPOSITORY%`: non-empty; only ASCII letters, digits, and single inner hyphens; MUST NOT start or end with a hyphen; MUST NOT contain `/`, whitespace, `..`, or line breaks, so both are safe inside a GitHub URL path.
- `%AUTHOR%` and `%DESCRIPTION%`: non-empty single-line free text after trimming; MUST NOT contain line breaks.

**Substituted values are data, never code.** Do not evaluate, `source`, or interpolate keyword values into shell commands or any other executable context. Serialize each value for its destination format at substitution time: write `%AUTHOR%` and `%DESCRIPTION%` into `pyproject.toml` as escaped TOML basic strings (escape backslashes and double quotes; reject a value that still cannot be represented), and write values into `README.md`, `uv.lock`, `.g.conf`, `src/skell/core.py`, `src/skell/__main__.py`, and the `scripts/skell.sh` comment header as plain literal text; the single-line rule above excludes line-break injection.

## 3. PHASE 1: File System and Initialization

Precondition: the PHASE 0 validation gate has passed. If it has not, no operation in this phase runs.

Run the following file operations in this exact order, inside the new project root directory:

**Path confinement.** Keep every extraction, substitution, rename, and write strictly inside the new project root. Before creating, renaming, or deleting any path, verify that the fully resolved absolute path remains inside the project root; if any resolved path would escape it, stop and report instead of performing the operation. The two renames below are fixed by this specification and MUST NOT be composed from any value other than the validated `%SHORTNAME%` and `%SRCDIR%`.

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

- **`--ver` / `--version`**: print the version report lines `Current Installed`, `Latest @ PyPI`, and `Latest @ GitHub`, each rendered as `<label> : <version>` with labels left-justified to a common width so the colons and version numbers align vertically, and FORCE the online new-version check, ignoring the delay and the JSON cache file described in PHASE 4.
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
- Negative-outcome `idle-delay`: hardcoded to `86400` seconds (1 day).
- Cache file: `$HOME/.cache/%PROGRAM%/check_version_idle-time.json`
- Required JSON content (field names are an implementation choice):
  1. `last-success`: the epoch of the most recent successful check, plus the same instant in human-readable form; `null` in both forms until the first successful check.
  2. `idle-time` expiration: the epoch after which the next automatic check is due, plus the same instant in human-readable form.

**Timestamp semantics.**

- The `last-success` fields record only checks that received and parsed a valid release response; a failed check attempt MUST NOT change them.
- The `idle-time` expiration is always computed from the timestamp of the attempt just performed, never from the stored `last-success` value, so a stored old success never shortens the configured delay.

**Version-check execution flow:**

1. **Initial decision.** Perform the HTTP call when the cache file does not exist, cannot be read, cannot be parsed, holds an expired `idle-time` (current time greater than or equal to the stored expiration epoch), or `--ver`/`--version` was passed; otherwise skip the check.
2. **Positive outcome (newer version found).** Print a message in BRIGHT GREEN color reporting "Available Version" versus "Installed Version". Record the attempt time `t` in both `last-success` fields and set the `idle-time` expiration to `t + 3600` seconds.
3. **Negative outcome, valid response (no newer version).** Print a BRIGHT RED message reporting that no newer version is available. Record the attempt time `t` in both `last-success` fields and set the `idle-time` expiration to `t + 86400` seconds.
4. **Negative outcome, failed check (HTTP errors such as 429 or 503, transport errors, or an unparseable response).** Print a BRIGHT RED message reporting the encountered error. Preserve the stored `last-success` fields unchanged when a prior successful check exists; keep them `null` when none exists. Set the `idle-time` expiration to the failed attempt time `t + 86400` seconds in both forms.

## 7. Verification

Before declaring completion, verify each item below and report its outcome. Items 1–4 are static file checks; item 5 runs bounded behavioral checks; report the two groups separately:

1. No literal keyword `%AUTHOR%`, `%DESCRIPTION%`, `%PROGRAM%`, `%SHORTNAME%`, `%SRCDIR%`, `%OWNER%`, or `%REPOSITORY%` remains in any scaffolded file.
2. `scripts/%SHORTNAME%.sh` exists, `src/skell` no longer exists, and `src/%SRCDIR%` exists.
3. Application sources live under `src/%SRCDIR%`.
4. `pyproject.toml` declares the package so that `.github/workflows/release-uvx.yml` can build it (project name, packages discovery, package data).
5. **Bounded build and execution checks.** When `uv` is available, run at most one attempt of each applicable check below and give each check a finite execution timeout (suggested values: 120 seconds for the build check, 60 seconds for the execution check). Do not retry a failed or timed-out check.
   - **Build check.** Run `uv build` as the build smoke check. `uv sync` is a separate dependency-synchronization check: run and report it on its own only when useful, and never report it as a substitute for the build check.
   - **Execution check.** Run exactly one bounded command, either `scripts/%SHORTNAME%.sh --help` or `uv run python -m %SRCDIR% --help`, to prove the package imports and runs.
   - **Outcome reporting.** Report every behavioral check with exactly one outcome: PASS (exit code 0 within the timeout), FAIL (non-zero exit; include the observed error), TIMEOUT (the finite limit expired before exit), or SKIPPED (precondition unmet, for example `uv` not available; include the reason). Report TIMEOUT as its own outcome, never as PASS or FAIL, and never report an unexecuted check as passed.
