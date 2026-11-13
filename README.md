> [!CAUTION]
> ### 🚨 STRICTLY EXPERIMENTAL — PROOF OF CONCEPT (PRE-ALPHA)
> 
> ![Status: Proof of Concept](https://img.shields.io/badge/Status-Proof_of_Concept-red?style=flat-square) ![Stage: Pre-Alpha](https://img.shields.io/badge/Stage-Pre--Alpha-critical?style=flat-square) ![Maintenance: Personal Use Only](https://img.shields.io/badge/Scope-Personal_Use_Only-important?style=flat-square) ![Issues: Closed](https://img.shields.io/badge/Issues_%26_PRs-Not_Accepted-inactive?style=flat-square)
>
> **PLEASE READ CAREFULLY BEFORE USING THIS SOFTWARE:**
> 
> * **Very Early Stage:** This project is currently a raw **Proof of Concept (PoC)** in a **pre-alpha** state. It is nowhere near production-ready and may contain severe bugs, breaking changes, or incomplete logic.
> * **Personal Use Only:** This repository is developed, maintained, and shared strictly for **personal use**. 
> * **No Support or Feature Requests:** Please **do not** open issues, bug reports, or feature requests. They will not be addressed or accepted at this stage of development.
> * **No Warranty:** This software is provided **"AS IS"**, without warranty of any kind, express or implied. You may use it strictly for **testing and evaluation purposes** at your own sole risk.

# cli-skills (0.10.8)

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/license-GPL--3.0-491?style=flat-square" alt="License: GPL-3.0">
  <img src="https://img.shields.io/badge/platform-Linux-6A7EC2?style=flat-square&logo=terminal&logoColor=white" alt="Platforms">
  <img src="https://img.shields.io/badge/docs-live-b31b1b" alt="Docs">
<img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json" alt="uv">
</p>
<p align="center">
<strong>Install and update LLM agent skills for supported CLI tools.</strong><br>
Manage user-level skills for <code>antigravity</code>, <code>claude</code>, <code>codex</code>, <code>copilot</code>, <code>opencode</code>, <code>openclaw</code>, and <code>pi</code>.
</p>


<p align="center">
  <a href="#feature-highlights">Feature Highlights</a> |
  <a href="#skill-support-layout">Skill Layout</a> |
  <a href="#quick-start">Quick Start</a> |
  <a href="#commands">Commands</a> |
  <a href="#supported-cli-targets">CLI Targets</a> |
  <a href="#install-behavior">Install Behavior</a> |
  <a href="#configuration">Configuration</a> |
  <a href="#release-checks">Release Checks</a> |
  <a href="#upgrade-and-uninstall">Upgrade and Uninstall</a> |
  <a href="#live-execution-with-uvx">Live execution with uvx</a> |
  <a href="#local-execution">Local Execution</a> |
  <a href="#development">Development</a> |
  <a href="#acknowledgments">Acknowledgments</a>
</p>

<p align="center">
<br>
🚧 <strong>DRAFT:</strong> Proof-of-Concept (PoC) Version 📝 - Work in Progress 🏗️ 🚧<br>
⚠️ <strong>IMPORTANT NOTICE</strong>: Created with <a href="https://www.npmjs.com/package/pi-usereq"><strong>PI-useReq/pi-usereq</strong></a> 🤖✨ ⚠️<br>
<br>
</p>


## Feature Highlights

- Install bundled skills into each enabled CLI's user-level skills directory.
- Synchronize managed skill directories on every install: packaged files are overwritten and files no longer packaged are deleted.
- Enable or disable each target CLI; the selection persists in `~/.config/cli-skills/config.json`.
- Inspect packaged resources, CLI configuration, and installation status with `show`.
- Inspect and mutate the configuration with `--print`, `--info`, `--print-raw`, `--get`, `--set`, and `--unset`.
- Check PyPI releases automatically with a 2-second timeout and a cached idle delay; `--ver` also reports the latest GitHub release.
- Install the bundled skills automatically after a successful `--upgrade` when at least one CLI is enabled.
- Run from a repository checkout, as a uv tool, or with uvx; the `skills` executable accepts the same commands and options as `cli-skills`.

Bundled skills:

- `astra-uv-project` - create a new Astral uv Python CLI project from scratch.
- `prompt-skill-architect` - create, review, and optimize LLM agent prompts and skills.

All bundled skills are listed in the packaged manifest `src/resources/manifest.json`.


## Skill Support Layout

Each packaged skill keeps `SKILL.md` at its root and organizes support files by purpose:

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

- `scripts/` contains shell and Python scripts.
- `references/` contains Markdown support files; `references/images/` contains images referenced by those files.
- `assets/` contains data and configuration files.
- `images/` contains vector or raster images referenced by `SKILL.md`.


## Quick Start

Prerequisites: Python 3.11 or newer and [Astral uv](https://docs.astral.sh/uv/).

1. Install the CLI:

   ```bash
   uv tool install cli-skills
   ```

2. Enable one or more target CLIs:

   ```bash
   cli-skills enable pi
   cli-skills enable claude
   ```

3. Install the bundled resources:

   ```bash
   cli-skills install
   ```

4. Start or restart the target CLI so it discovers the installed skills.
5. Optional: review packaged resources, CLI configuration, and installation status:

   ```bash
   cli-skills show
   ```

`enable` and `disable` persist their selection; `install` updates every enabled CLI.


## Commands

| Command | Behavior |
|---|---|
| `cli-skills` | Print the full help screen. |
| `cli-skills --help` | Print the full help screen. |
| `cli-skills <command> --help` | Print help for `enable`, `disable`, `install`, `uninstall`, `show`, `--upgrade`, `--uninstall`, `--ver`, `--version`, `--dev`, `--force`, or any configuration command. |
| `cli-skills --ver` | Print the `Current Installed`, `Latest @ PyPI`, and `Latest @ GitHub` lines; force a release check. |
| `cli-skills --version` | Same as `--ver`. |
| `cli-skills --upgrade` | Upgrade from PyPI with uv on Linux, then install bundled skills for every enabled CLI; print the manual command on other platforms. |
| `cli-skills --upgrade --dev` | Upgrade to the latest tagged GitHub release instead of PyPI (Linux); print the manual command elsewhere. |
| `cli-skills --upgrade --develop` | Long form of `--upgrade --dev`. |
| `cli-skills --upgrade --force` | Force download and complete reinstallation from PyPI with `--force --reinstall --refresh` (Linux); print the manual command elsewhere. |
| `cli-skills --upgrade --dev --force` | Force download and complete reinstallation of the latest tagged GitHub release (Linux); print the manual command elsewhere. |
| `cli-skills --uninstall` | Uninstall the tool with uv on Linux; print the manual command on other platforms. |
| `cli-skills enable <cli name>` | Enable skill installation for a supported CLI. |
| `cli-skills disable <cli name>` | Disable skill installation for a supported CLI. |
| `cli-skills install` | Install or update bundled skills for every enabled CLI. |
| `cli-skills uninstall` | Remove installed bundled skills for every enabled CLI. |
| `cli-skills show` | Show packaged resources, CLI configuration, and installation status. |
| `cli-skills --print [<path>]` | Print the configuration tree or one configuration subtree. |
| `cli-skills --info [<path>]` | Print the configuration schema reference or one schema subtree. |
| `cli-skills --print-raw` | Print the raw configuration JSON file bytes. |
| `cli-skills --get <path>` | Print the JSON value stored at a canonical configuration path. |
| `cli-skills --set <path> <value>` | Validate and store a value at a canonical configuration path. |
| `cli-skills --unset <path>` | Reset a value to its default or delete one array item at a canonical configuration path. |

`--dev`, `--develop`, and `--force` are `--upgrade` options only. The `skills` executable exposes the same commands, output, and exit codes as `cli-skills`.

Exit codes:

- `0` - success, including help, version reporting, and `install` or `uninstall` with no enabled CLI.
- `1` - configuration command failure, installation or uninstallation failure for at least one enabled CLI, or chained post-upgrade install failure.
- `2` - unknown command or option, unsupported CLI name, missing CLI name, or an invalid `--upgrade` option combination.
- Any other nonzero status returned by uv for `--upgrade` or `--uninstall`.


## Supported CLI Targets

| CLI | Skills directory |
|---|---|
| `antigravity` | `~/.gemini/config/skills` |
| `claude` | `~/.claude/skills` |
| `codex` | `~/.codex/skills` |
| `copilot` | `~/.copilot/skills` |
| `opencode` | `~/.config/opencode/skills` |
| `openclaw` | `~/.openclaw/workspace/skills` |
| `pi` | `~/.pi/agent/skills` |

Only enabled CLIs are updated. Destinations are user-level configuration directories, not project directories.


## Install Behavior

- `install` processes every enabled CLI.
- Each packaged skill is copied to `<skills directory>/<skill name>`.
- Existing skill files are overwritten with the packaged versions.
- Files and directories inside a managed skill directory that are absent from the package are deleted.
- Skill directories not managed by the package are left unchanged.
- A missing packaged source path aborts that CLI and reports an error; remaining enabled CLIs are still processed.
- Output reports `Installed <n> skills for <cli>.` followed by an indented `Skills: <names>` line for each processed CLI.
- With no enabled CLI, `install` prints an informational message and exits with `0`.
- If any CLI installation fails, `install` prints the error and exits with `1`.
- `uninstall` deletes `<skills directory>/<skill name>` for every manifest skill and every enabled CLI, reports `Removed <n> skills for <cli>.` per CLI, and preserves destination entries outside managed skill directories.
- A missing destination skill directory counts as removed; with no enabled CLI, `uninstall` prints an informational message and exits with `0`.
- If any CLI uninstallation fails, `uninstall` prints the error, continues with the remaining enabled CLIs, and exits with `1`.


## Configuration

The CLI stores its user configuration at:

```text
~/.config/cli-skills/config.json
```

Example:

```json
{
  "enabled": [
    "pi",
    "claude"
  ]
}
```

The file root is the canonical section `Global`; its only key is `enabled`, a unique array of supported CLI names whose default is the empty array. `enable` and `disable` maintain `enabled` through the same schema used by the configuration commands.

Configuration commands:

| Command | Behavior |
|---|---|
| `cli-skills --print [<path>]` | Print the whole configuration tree or the requested subtree. |
| `cli-skills --info [<path>]` | Print the whole schema reference or the requested schema subtree, including types, constraints, defaults, and allowed values. |
| `cli-skills --print-raw` | Print the unmodified on-disk configuration bytes. |
| `cli-skills --get <path>` | Print exactly one JSON value without labels. |
| `cli-skills --set <path> <value>` | Validate and store one value. |
| `cli-skills --unset <path>` | Reset a value declaring a default or delete one array item. |

Canonical paths are case-sensitive and colon-separated, rooted at `Global`; use `Global:enabled` for the enabled array. Arrays address an item with `<Idx>` and accept `+`, `append`, or `insert:<Idx>` for additions.

```bash
cli-skills --print
cli-skills --info
cli-skills --get Global:enabled
cli-skills --set Global:enabled '["claude","pi"]'
cli-skills --set Global:enabled:+ pi
cli-skills --unset Global:enabled:0
cli-skills --unset Global
```

- A whole-array argument is a JSON array such as `'["claude","pi"]'`; a single array item is literal text such as `pi`.
- Valid output goes to stdout; every configuration diagnostic goes to stderr with exit status `1`.
- `--set` and `--unset` validate the whole resulting configuration, then replace the file atomically; a failed operation leaves the stored configuration unchanged and prints no success line.
- A successful `--set` prints `Set <path>.`; a successful `--unset` prints `Unset <path>.`.
- `--print`, `--print-raw`, `--get`, `--set`, and `--unset` initialize a missing configuration file from schema defaults; `--info` reads only the schema.
- Read commands tolerate a missing, unreadable, or malformed file; `--set` and `--unset` reject malformed or schema-invalid content.
- Unknown sections, unknown keys, unknown operations, invalid indices, and out-of-range indices are rejected with a diagnostic naming the path and, for indices, the valid range.


## Release Checks

- A release check runs before command dispatch on every invocation.
- The check requests the latest published version from the PyPI JSON API with a 2-second timeout.
- Cache file: `~/.cache/cli-skills/check_version_idle-time.json`, storing last-success and idle-time timestamps in epoch and human-readable form.
- The check is skipped while the cached idle time is valid.
- A newer release prints a bright-green available-versus-installed message and sets a 3600-second idle delay.
- A failed check or no newer release prints a bright-red message and sets an 86400-second idle delay.
- `--ver` and `--version` force a check and print three aligned lines:

  ```text
  Current Installed : x.y.z
  Latest @ PyPI    : x.y.z
  Latest @ GitHub  : x.y.z
  ```

- A failed PyPI request prints the `Latest @ PyPI    : unavailable (<reason>)` value; a failed GitHub request prints the `Latest @ GitHub  : unknown (<reason>)` value.
- Notifications are written to stderr; `--ver` and `--version` exit with `0`.


## Upgrade and Uninstall

The tool is installed with Astral uv (see [Quick Start](#quick-start)). Upgrade through the CLI (latest version published on PyPI):

```bash
cli-skills --upgrade
```

Upgrade from the newest tagged GitHub release instead (intermediate and test releases) by combining `--upgrade` with `--dev` or `--develop`:

```bash
cli-skills --upgrade --dev
```

Force the download and the complete reinstallation instead of the standard install/update process by combining `--upgrade` with `--force`; the upgrade command appends the uv reinstallation options `--force --reinstall --refresh`:

```bash
cli-skills --upgrade --force
```

Combine `--dev` or `--develop` with `--force` to force the reinstallation of the latest tagged GitHub release:

```bash
cli-skills --upgrade --dev --force
```

On Linux, a successful `--upgrade` runs `cli-skills install` automatically when at least one CLI is enabled, so the freshly upgraded package synchronizes the bundled skills into every enabled CLI. Its per-CLI report is part of the upgrade output and its exit code becomes the command exit code; no install runs when no CLI is enabled.

`--dev`, `--develop`, and `--force` are valid only after `--upgrade`; using them alone or before `--upgrade`, or combining `--dev` with `--develop`, prints an unknown-command diagnostic and exits with `2`.

Uninstall through the CLI:

```bash
cli-skills --uninstall
```

Manual uninstall:

```bash
uv tool uninstall cli-skills
```


## Install from GitHub

Intermediate and test releases are published on GitHub: `https://github.com/Ogekuri/CLI-Skills`.

Install the latest tagged GitHub release directly:

```bash
uv tool install cli-skills --from git+https://github.com/Ogekuri/CLI-Skills.git
```

Afterwards, upgrade to the newest GitHub release with the dedicated upgrade option:

```bash
cli-skills --upgrade --dev
```

`--dev` (long form `--develop`) is an `--upgrade` option: it always installs the newest tagged release on GitHub, regardless of the branch it was tagged on. Combine it with `--force` to force the download and the complete reinstallation of that release.


## Live execution with uvx

Run `cli-skills` on the fly from PyPI without installing the tool:

```bash
uvx cli-skills --help
```

Use the same form for installation commands, for example:

```bash
uvx cli-skills install
```


## Local Execution

Run the CLI from the repository checkout:

```bash
./scripts/cli-skills.sh --help
./scripts/cli-skills.sh enable pi
./scripts/cli-skills.sh install
```

The launcher delegates execution to Astral uv from the repository root.


## Development

Run the tests:

```bash
uv run python -m unittest discover -s tests
```

Build the sdist and wheel into `dist/`:

```bash
./scripts/build.sh
./scripts/build.sh --output-dir /absolute/release/dir
./scripts/build.sh --clean --output-dir /absolute/release/dir
```

`--output-dir` requires an absolute path and defaults to `dist/`. `--clean` empties the release output directory while preserving the directory itself, removes build intermediates, and exits with `0` without building. A build prints the published file names and SHA-256 digests and exits nonzero when a mandatory build phase fails.

Run the full pre-release validation before a release:

```bash
./scripts/pre-release-check.sh
```


## Acknowledgments

Uses [Astral uv](https://docs.astral.sh/uv/) for packaging and execution and the [Agent Skills](https://agentskills.io/specification) directory format for bundled resources.
