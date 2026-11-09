# cli-skills Requirements

## 1. Introduction

### 1.1 Document Rules

- **DOC-001**: MUST write and maintain this document in English.
- **DOC-002**: MUST use RFC 2119 keywords for normative requirements.
- **DOC-003**: MUST assign each requirement a unique, stable ID using the DOC, PRJ, CTN, DES, or REQ prefix.
- **DOC-004**: MUST NOT renumber, reuse, or repurpose requirement IDs outside a dedicated reorganization workflow that provides an old-to-new mapping.
- **DOC-005**: MUST express each requirement as one testable sentence in the canonical requirement-line format.
- **DOC-006**: MUST keep the first line as a level-1 title without YAML front matter or in-document revision history.

### 1.2 Project Scope

Python CLI application `cli-skills` provides management commands, online release checks, and bundled LLM agent skills, and is published on PyPI and installable with Astral uv and uvx. This specification derives exclusively from the user request.

The application installs bundled skills into user-level configuration directories of supported LLM agent CLIs when those CLIs are enabled.

The `uninstall` command removes the skills previously installed by `install` from the destinations of every enabled CLI.

The distribution package provides the additional `skills` console-script executable bound to the same application entry point as `cli-skills`.

Assumptions:

- The archive supplies the pre-established source layout, project version, and release workflow; no application-specific commands beyond management commands are specified.
- A valid latest-release response with no newer version is a negative outcome and uses the requested error notification and one-day delay.
- On a failed check, the cache preserves the last successful timestamp when available; its idle-time is calculated from the failed attempt so the one-day delay is effective. Before any success, the successful timestamps are null.
- Cache field names, human-readable timestamp format, version comparison rules, command-specific help content, and exit codes are unspecified and may be selected during implementation.
- The `astra-uv-project` skill name and routing text are implementation choices; its body is the English rendering of the user-supplied PHASE 0–4 project-scaffold specification.
- Supported CLI names are `antigravity`, `claude`, `codex`, `copilot`, `opencode`, `openclaw`, and `pi`; prompt installation is out of scope.
- The enabled-CLI configuration file is `$HOME/.config/cli-skills/config.json`.

## 2. Project Requirements

### 2.1 Project Functions

- **PRJ-001**: MUST provide a Python command-line application named `cli-skills`.
- **PRJ-002**: MUST provide management commands independently of application core logic.
- **PRJ-003**: MUST support local execution through `scripts/cli-skills.sh`.
- **PRJ-004**: MUST support installation using Astral uv and on-the-fly execution using uvx.
- **PRJ-005**: MUST check online for newer releases using a local idle-time cache.
- **PRJ-006**: MUST distribute LLM agent skills together with the `cli-skills` program under `src/resources`.
- **PRJ-007**: MUST maintain skills under `src/resources/skills`.
- **PRJ-008**: MUST distribute an `astra-uv-project` skill under `src/resources/skills/astra-uv-project` for creating new Astral uv Python projects from scratch.
- **PRJ-009**: MUST install bundled skills into user-level configuration directories of supported LLM agent CLIs.
- **PRJ-010**: MUST support installation targets `antigravity`, `claude`, `codex`, `copilot`, `opencode`, `openclaw`, and `pi`.
- **PRJ-011**: MUST remove installed bundled skills from enabled CLI destinations through the `uninstall` command.
- **PRJ-012**: MUST publish the `cli-skills` package to PyPI through OIDC Trusted Publishing from the `release-pypi.yml` workflow.
- **PRJ-013**: MUST run every release-workflow step for a tagged version on any branch and publish to PyPI only when the tag is on `master`.
- **PRJ-014**: MUST provide `scripts/pre-release-check.sh` running build, metadata, and unit-test checks required before an official release.
- **PRJ-015**: MUST execute the unit-test suite in a dedicated `release-pypi.yml` job before any build or release step.
- **PRJ-016**: MUST prevent release-artifact creation and PyPI publication when the unit-test job fails.
- **PRJ-017**: MUST distribute the `skills` executable alongside the `cli-skills` executable in the same `cli-skills` distribution package.

### 2.2 Project Constraints

- **CTN-001**: MUST use `Francesco Rolando` for `%AUTHOR%`.
- **CTN-002**: MUST use `Agent skills and prompts` for `%DESCRIPTION%`.
- **CTN-003**: MUST use `cli-skills` for `%PROGRAM%` and `%SHORTNAME%`, and `cli_skills` for `%SRCDIR%`.
- **CTN-004**: MUST use `Ogekuri` for `%OWNER%`.
- **CTN-005**: MUST use `CLI-Skills` for `%REPOSITORY%`.
- **CTN-006**: MUST use a hardcoded HTTP/HTTPS timeout of 2 seconds for release checks.
- **CTN-007**: MUST use a hardcoded standard idle delay of 3600 seconds.
- **CTN-008**: MUST use a hardcoded negative-outcome idle delay of 86400 seconds.
- **CTN-009**: MUST treat the `skell.tgz` archive content as an externally maintained input of the `astra-uv-project` skill.
- **CTN-010**: MUST pin every GitHub Action referenced by `.github/workflows/release-pypi.yml` to a major version whose runtime is Node24 or later.

## 3. Requirements

### 3.1 Design and Implementation

- **DES-001**: MUST extract every file and directory, including empty directories, from `assets/skell.tgz` into the current directory before keyword substitution.
- **DES-002**: MUST overwrite existing files when extracting archive entries.
- **DES-003**: MUST replace the seven specified keywords with their configured values in `.g.conf`, `README.md`, `pyproject.toml`, and `uv.lock` after extraction.
- **DES-004**: MUST replace the seven specified keywords with their configured values in `src/skell/core.py`, `scripts/skell.sh`, and `src/skell/__main__.py` after extraction.
- **DES-005**: MUST rename `scripts/skell.sh` to `scripts/cli-skills.sh` after keyword substitution.
- **DES-006**: MUST rename `src/skell` to `src/cli_skills` after keyword substitution.
- **DES-007**: MUST generate application sources in `src/cli_skills` following the archive's pre-established layout.
- **DES-008**: MUST configure `pyproject.toml` to include all files needed for operation in the package generated by `.github/workflows/release-pypi.yml`.
- **DES-009**: MUST store release-check cache data at `$HOME/.cache/cli-skills/check_version_idle-time.json`.
- **DES-010**: MUST store the last successful check timestamp as an epoch value in the JSON cache.
- **DES-011**: MUST store the last successful check timestamp in human-readable form in the JSON cache.
- **DES-012**: MUST store the idle-time expiration timestamp as an epoch value in the JSON cache.
- **DES-013**: MUST store the idle-time expiration timestamp in human-readable form in the JSON cache.
- **DES-014**: MUST author every skill in English.
- **DES-015**: MUST write and optimize every skill for LLM agents following the guidance in `src/resources/skills/prompt-skill-architect/SKILL.md`.
- **DES-016**: MUST load `src/resources/skills/prompt-skill-architect/SKILL.md` into context before creating, verifying, or modifying any skill.
- **DES-017**: MUST represent each skill as a directory containing a `SKILL.md` file and related files.
- **DES-018**: MUST begin every `SKILL.md` with YAML frontmatter declaring the skill `name`.
- **DES-019**: MUST declare a `description` in every `SKILL.md` frontmatter stating the skill capability and an unambiguous use trigger.
- **DES-020**: MUST include the `src/resources` directory tree in the `cli-skills` distribution package.
- **DES-021**: MUST maintain a JSON manifest file under `src/resources` listing every skill in the `src/resources` folders and subfolders.
- **DES-022**: MUST record for each manifest entry the file path relative to `src/resources`.
- **DES-023**: MUST record for each manifest entry the skill `name` from its frontmatter.
- **DES-024**: MUST record for each manifest entry the skill `description` as an exact string match of its frontmatter `description`.
- **DES-025**: MUST define the `astra-uv-project` skill trigger as creating a new Python project based on Astral uv from scratch.
- **DES-026**: MUST declare use of the `astra-uv-project` skill on existing projects out of scope.
- **DES-027**: MUST bundle the project skeleton archive as `assets/skell.tgz` inside the `astra-uv-project` skill directory.
- **DES-028**: MUST define bootstrap keywords `%AUTHOR%`, `%DESCRIPTION%`, `%PROGRAM%`, `%SHORTNAME%`, `%SRCDIR%`, `%OWNER%`, and `%REPOSITORY%` resolved from the user request or project context.
- **DES-029**: MUST terminate skill execution and request missing values instead of inventing bootstrap keyword values that cannot be identified unambiguously.
- **DES-030**: MUST normalize `%PROGRAM%`, `%SHORTNAME%`, and `%SRCDIR%` values to lowercase.
- **DES-031**: MUST specify extraction of every `assets/skell.tgz` entry, including empty directories, into the target project directory with overwrite of existing files.
- **DES-032**: MUST specify replacing the seven bootstrap keywords in `.g.conf`, `README.md`, `pyproject.toml`, `uv.lock`, `src/skell/core.py`, `scripts/skell.sh`, and `src/skell/__main__.py` after extraction.
- **DES-033**: MUST specify renaming `scripts/skell.sh` to `scripts/%SHORTNAME%.sh` and directory `src/skell` to `src/%SRCDIR%` after keyword substitution.
- **DES-034**: MUST specify application source generation under `src/%SRCDIR%` following the archive pre-established layout, where `core.py` ships as a comment-only stub implemented in PHASE 2 through PHASE 4.
- **DES-035**: MUST specify a Python CLI application named `%PROGRAM%` packaged for Astral uv tool installation and uvx on-the-fly execution.
- **DES-036**: MUST specify local execution support through `scripts/%SHORTNAME%.sh` delegating to `uv run python -m %SRCDIR%`.
- **DES-037**: MUST specify `pyproject.toml` configuration including every file needed by the `.github/workflows/release-pypi.yml` package build.
- **DES-038**: MUST include the exact English help template listing `--upgrade`, `--uninstall`, `--ver`, `--version`, `--dev`, and `--help` management commands.
- **DES-039**: MUST specify `--ver` and `--version` printing the installed version as `x.y.z` followed by `PyPI latest:` and `GitHub latest:` lines.
- **DES-040**: MUST specify Linux execution of `uv tool install %PROGRAM% --force` for `--upgrade` with manual-command printing on other operating systems.
- **DES-041**: MUST specify Linux execution of `uv tool uninstall %PROGRAM%` for `--uninstall` with manual-command printing on other operating systems.
- **DES-042**: MUST specify the automatic release-check endpoint `https://pypi.org/pypi/%PROGRAM%/json` with a hardcoded 2-second timeout.
- **DES-043**: MUST specify the release-check cache file `$HOME/.cache/%PROGRAM%/check_version_idle-time.json` storing last-success and idle-time timestamps in epoch and human-readable forms.
- **DES-044**: MUST specify the automatic release check before parameter parsing, forced by `--ver` and `--version` and skipped while the cached idle-time is valid.
- **DES-045**: MUST specify a bright-green available-versus-installed message and a 3600-second cache expiration when a newer version is found.
- **DES-046**: MUST specify a bright-red error message and an 86400-second cache expiration when a release check fails or finds no newer version.
- **DES-047**: MUST store user configuration in `$HOME/.config/cli-skills/config.json` as a JSON object.
- **DES-048**: MUST store enabled CLI names as a JSON array under the `enabled` key in the user configuration.
- **DES-049**: MUST implement one CLI adapter per supported CLI in a dedicated module exposing skill destinations.
- **DES-050**: MUST resolve `pi` skills to `$HOME/.pi/agent/skills`.
- **DES-051**: MUST resolve `openclaw` skills to `$HOME/.openclaw/workspace/skills`.
- **DES-052**: MUST resolve `codex` skills to `$HOME/.codex/skills`.
- **DES-053**: MUST resolve `antigravity` skills to `$HOME/.gemini/config/skills`.
- **DES-054**: MUST resolve `claude` skills to `$HOME/.claude/skills`.
- **DES-090**: MUST resolve `opencode` skills to `$HOME/.config/opencode/skills`.
- **DES-091**: MUST resolve `copilot` skills to `$HOME/.copilot/skills`.
- **DES-055**: MUST install each manifest skill directory as a subdirectory named after its source directory under the adapter skills directory.
- **DES-056**: MUST overwrite existing destination files with packaged skill file contents during installation.
- **DES-057**: MUST delete destination files inside an installed skill directory when absent from the packaged skill directory.
- **DES-058**: MUST preserve destination files outside skill directories managed by the current installation.
- **DES-062**: MUST install only skills listed in the `src/resources` manifest.
- **DES-063**: MUST create missing destination directories before copying skill files.
- **DES-064**: MUST continue installation for remaining enabled CLIs after an adapter installation failure.
- **DES-065**: MUST implement the `show` report in a dedicated `src/cli_skills/show.py` module exposing table rendering and a home-directory override.
- **DES-066**: MUST render every `show` table with box-drawing borders using `┌ ─ ┬ ┐ │ ├ ┼ ┤ └ ┴ ┘` and word-wrapped cell content.
- **DES-067**: MUST organize every skill support file under exactly one canonical subdirectory of the skill directory: `scripts`, `references`, `assets`, or `images`.
- **DES-068**: MUST place shell and Python scripts for a skill under its `scripts` subdirectory.
- **DES-069**: MUST place Markdown support files for a skill under its `references` subdirectory.
- **DES-070**: MUST place images referenced by Markdown files under `references/images` within the skill directory.
- **DES-071**: MUST place data and configuration files for a skill under its `assets` subdirectory.
- **DES-072**: MUST place vector or raster images referenced by `SKILL.md` under the skill `images` subdirectory.
- **DES-073**: MUST reject a bundled skill whose layout violates DES-067 through DES-072 during catalog generation.
- **DES-074**: MUST ship `%AUTHOR%` in the `pyproject.toml` author field inside `assets/skell.tgz` instead of a hardcoded author name.
- **DES-075**: MUST ship `%OWNER%` in `README.md` repository URLs and the `scripts/skell.sh` author header inside `assets/skell.tgz` instead of hardcoded owner names.
- **DES-076**: MUST specify a bounded post-implementation execution check such as `scripts/%SHORTNAME%.sh --help` in addition to the build smoke check.
- **DES-077**: MUST verify the CTN-010 constraint through a unit test that parses `.github/workflows/release-pypi.yml` and validates every referenced action version.
- **DES-078**: MUST keep the existing build, attestation, changelog, and GitHub-release steps in `release-pypi.yml` for tagged versions on every branch.
- **DES-079**: MUST publish built distributions to PyPI with `pypa/gh-action-pypi-publish` using OIDC `id-token: write` and no API token, only on `master`.
- **DES-080**: MUST declare PyPI-compliant package metadata in `pyproject.toml`, including the PEP 639 SPDX license expression and project URLs.
- **DES-081**: MUST specify Linux execution of `uv tool install %PROGRAM% --force --from git+https://github.com/%OWNER%/%REPOSITORY%.git` for `--upgrade` combined with `--dev` or `--develop`.
- **DES-082**: MUST accept `--dev` and `--develop` only as suffixes of `--upgrade`, selecting the latest GitHub release regardless of its branch.
- **DES-083**: MUST specify `https://api.github.com/repos/%OWNER%/%REPOSITORY%/releases/latest` as the GitHub latest-release endpoint backing `--ver`, `--version`, and `--dev` upgrades.
- **DES-084**: MUST build the sdist and wheel with the release workflow build command into a temporary directory in `scripts/pre-release-check.sh`.
- **DES-085**: MUST validate the built distributions with `twine check` in `scripts/pre-release-check.sh`.
- **DES-086**: MUST run the unit-test suite through the project-defined uv test command in `scripts/pre-release-check.sh`.
- **DES-087**: MUST remove every build and test artifact, including the temporary build directory, egg-info directories, and `__pycache__` directories, on success and failure.
- **DES-088**: MUST verify the PRJ-015 and PRJ-016 gating through a unit test that parses `release-pypi.yml` and checks the test-job dependency and test command.
- **DES-089**: MUST document in the help template only user-facing usage of the listed commands, without internal-implementation details or legacy-support references.
- **DES-092**: MUST print every supported-CLI list, including `show` tables and diagnostics, in alphabetical order.
- **DES-094**: MUST make `prompt-skill-architect` select artifact profiles using evidenced host loading, authority, directory scope, lifecycle, persistence, and orchestration ownership.
- **DES-095**: MUST make `prompt-skill-architect` preserve exact template tokens and output invariants while validating substitutions with synthetic normal, empty, malformed, delimiter-containing, and quoted values.
- **DES-096**: MUST make `prompt-skill-architect` require linear shell instructions with validated literal arguments, correct quoting, and explicit option termination for hyphen-prefixed `rg` and `git grep` patterns.
- **DES-097**: MUST make `prompt-skill-architect` verify actual resource dependencies within authorized path boundaries while distinguishing labeled example paths from dependencies.
- **DES-098**: MUST make `prompt-skill-architect` record a finite correction budget before verification and report residual blockers when that budget expires.
- **DES-099**: MUST make `prompt-skill-architect` record case identifiers, inputs, expected and forbidden behavior, methods, observations, results, and evidence for applicable acceptance cases.
- **DES-100**: MUST make `prompt-skill-architect` distinguish repository packaging constraints from portable conventions and treat size recommendations as review triggers rather than universal host validity limits.
- **DES-101**: MUST declare the `skills` console-script entry point in the `pyproject.toml` `[project.scripts]` table bound to the same application entry point as `cli-skills`.
- **DES-102**: MUST make the `skills` executable accept the same commands and options as `cli-skills` and produce identical output and exit codes.

Canonical skill support layout; support subdirectories are optional and `SKILL.md` is the only file at the skill root:

```text
<skill-name>/
├── SKILL.md
├── scripts/
│   └── <script-name>.sh
├── references/
│   ├── images/
│   │   └── <picture-name>.png
│   └── <reference-template-name>.md
├── images/
│   └── <picture-name>.svg
└── assets/
    └── <data-or-configuration-name>.json
```

Logical structure after initialization; archive-provided additional files are not enumerated:

```text
.
├── .g.conf
├── .github/
│   └── workflows/
│       └── release-pypi.yml
├── README.md
├── pyproject.toml
├── uv.lock
├── scripts/
│   └── cli-skills.sh
└── src/
    └── cli_skills/
        ├── __main__.py
        └── core.py
```

### 3.2 Functions

- **REQ-001**: MUST perform the automatic release-check decision before parsing incoming parameters.
- **REQ-002**: MUST perform an HTTP request to `https://pypi.org/pypi/cli-skills/json` when the cache file does not exist.
- **REQ-003**: MUST perform a release-check request when the cached idle-time has expired.
- **REQ-004**: MUST skip the automatic request while the cached idle-time has not expired, except for forced version checks.
- **REQ-005**: MUST force a release-check request for `--ver` or `--version` regardless of cache contents or idle delay.
- **REQ-006**: MUST print the installed version as `x.y.z` for `--ver` and `--version`.
- **REQ-007**: MUST print the full English help template below when invoked without parameters.
- **REQ-008**: MUST print the full English help template below when invoked with `--help` alone.
- **REQ-009**: MUST provide command-specific help when `--help` is requested for a specific command.
- **REQ-010**: MUST execute `uv tool install cli-skills --force` for `--upgrade` on Linux.
- **REQ-011**: MUST NOT execute the upgrade command for `--upgrade` on non-Linux operating systems.
- **REQ-012**: MUST print a warning and the manual upgrade command for `--upgrade` on non-Linux operating systems.
- **REQ-013**: MUST execute `uv tool uninstall cli-skills` for `--uninstall` on Linux.
- **REQ-014**: MUST NOT execute the uninstall command for `--uninstall` on non-Linux operating systems.
- **REQ-015**: MUST print a warning and the manual uninstall command for `--uninstall` on non-Linux operating systems.
- **REQ-016**: MUST print a bright-green message identifying the available and installed versions when a newer version is found.
- **REQ-017**: MUST create or update the cache with an expiration 3600 seconds after a successful check that finds a newer version.
- **REQ-018**: MUST print a bright-red message identifying the error or negative outcome when a release check fails or finds no newer version.
- **REQ-019**: MUST create or update the cache with an expiration 86400 seconds after a failed or negative check.
- **REQ-020**: MUST treat HTTP errors, including 429 and 503, as failed release checks.
- **REQ-021**: MUST preserve the last successful check timestamps in the cache after a failed check when prior successful timestamps exist.
- **REQ-022**: MUST use null for the last successful check timestamps after a failed check when no successful check has been recorded.
- **REQ-023**: MUST record the successful check time in both successful timestamp fields when a release check succeeds.
- **REQ-024**: MUST persist the CLI name in the enabled configuration when invoked as `enable <cli name>`.
- **REQ-025**: MUST remove the CLI name from the enabled configuration when invoked as `disable <cli name>`.
- **REQ-026**: MUST reject an unsupported `<cli name>` for `enable` or `disable` with an error message and exit code 2.
- **REQ-027**: MUST print a confirmation message after processing `enable <cli name>` or `disable <cli name>`.
- **REQ-028**: MUST treat repeated `enable` or `disable` of the same CLI as a successful no-op.
- **REQ-029**: MUST install skills for every enabled CLI when invoked as `install`.
- **REQ-030**: MUST print the installed skill count for each CLI processed by `install`.
- **REQ-031**: MUST print an informational message and exit with code 0 when `install` finds no enabled CLI.
- **REQ-032**: MUST print an error and exit with code 1 when any enabled CLI installation fails.
- **REQ-033**: MUST provide command-specific help for `enable`, `disable`, `install`, and `uninstall` when invoked as `<command> --help`.
- **REQ-034**: MUST print the full help template containing `enable`, `disable`, `install`, `uninstall`, and `show` when invoked without parameters or with `--help` alone.
- **REQ-035**: MUST terminate installation for a CLI with an error when a manifest-listed source path is missing.
- **REQ-036**: MUST provide command-specific help for `show` when invoked as `show --help`.
- **REQ-037**: MUST print every manifest skill as a table when invoked as `show`.
- **REQ-038**: MUST print a CLI configuration table listing every supported CLI with its enabled state and skills path relative to the user home directory when invoked as `show`.
- **REQ-039**: MUST print an installation status table with one row per packaged skill and enabled CLI when invoked as `show`.
- **REQ-040**: MUST report each installation status row by scanning the CLI destination directories and comparing packaged paths and file contents.
- **REQ-042**: MUST print the complete `show` report and exit with code 0 when invoked as `show`.
- **REQ-043**: MUST execute `cli-skills install` as a child process after an `--upgrade` command with or without `--dev` succeeds when the enabled configuration contains at least one CLI.
- **REQ-044**: MUST NOT execute `cli-skills install` for `--upgrade` when the enabled configuration contains no CLI.
- **REQ-045**: MUST NOT execute `cli-skills install` for `--upgrade` when the upgrade command fails or is not executed.
- **REQ-046**: MUST return the `cli-skills install` exit code as the `--upgrade` exit code when `cli-skills install` executes.
- **REQ-047**: MUST remove manifest skills for every enabled CLI when invoked as `uninstall`.
- **REQ-048**: MUST delete each enabled CLI skill directory named after a manifest skill directory during `uninstall`.
- **REQ-051**: MUST preserve destination files outside manifest skill directories during `uninstall`.
- **REQ-052**: MUST treat a missing destination skill directory as removed during `uninstall`.
- **REQ-053**: MUST continue uninstallation for the remaining enabled CLIs after one CLI uninstallation fails.
- **REQ-054**: MUST print the removed skill count for each CLI processed by `uninstall`.
- **REQ-055**: MUST print an informational message and exit with code 0 when `uninstall` finds no enabled CLI.
- **REQ-056**: MUST print an error and exit with code 1 when any enabled CLI uninstallation fails.
- **REQ-057**: MUST list every installed skill name for each CLI processed by `install`.
- **REQ-058**: MUST surface the chained `cli-skills install` report as visible `--upgrade` output when the upgrade command and the chained installation both succeed.
- **REQ-059**: MUST compare the installed version against the PyPI latest version for the automatic release-check outcome.
- **REQ-060**: MUST print a `PyPI latest: <version>` line for `--ver` and `--version` reporting the newest PyPI version.
- **REQ-061**: MUST print a `GitHub latest: <version>` line for `--ver` and `--version` reporting the newest GitHub release as `x.y.z`.
- **REQ-062**: MUST report on the `GitHub latest:` line the same release that `--upgrade` with `--dev` installs.
- **REQ-063**: MUST execute `uv tool install cli-skills --force --from git+https://github.com/Ogekuri/CLI-Skills.git` for `--upgrade --dev` and `--upgrade --develop` on Linux.
- **REQ-064**: MUST treat `--dev` or `--develop` without `--upgrade` as an unknown command with exit code 2.
- **REQ-065**: MUST treat `--help` before a command name, or `--dev` or `--develop` before `--upgrade`, as an unknown command with exit code 2.
- **REQ-066**: MUST print `GitHub latest: unknown (<reason>)` for `--ver` and `--version` when the GitHub latest-release request fails, with `<reason>` identifying the actual error.

Full help template: substitute `cli-skills` for `%PROGRAM%` and the installed version for `x.y.z`; retain all other text and spacing.

```text
Usage: %PROGRAM% [command] [options] (x.y.z)

Management Commands:
  --upgrade   - Reinstall %PROGRAM% on Linux; print manual command elsewhere.
  --uninstall - Uninstall %PROGRAM% on Linux; print manual command elsewhere.
  --ver       - Print the %PROGRAM% version.
  --version   - Print the %PROGRAM% version.
  --dev       - With --upgrade, install the latest GitHub release instead of PyPI.
  --help      - Print the full help screen or the help text of a specific command.

Installation Commands:
  enable <cli name>  - Enable skill installation for a supported CLI.
  disable <cli name> - Disable skill installation for a supported CLI.
  install            - Install skills for every enabled CLI.
  uninstall          - Remove installed skills for every enabled CLI.

Reporting Commands:
  show               - Show packaged resources, CLI configuration, and installation status.

Commands:
  ...
```

## 4. Test Requirements

No unit tests were explicitly requested.
