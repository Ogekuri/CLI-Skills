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

# skills (0.5.0)

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/license-GPL--3.0-491?style=flat-square" alt="License: GPL-3.0">
  <img src="https://img.shields.io/badge/platform-Linux-6A7EC2?style=flat-square&logo=terminal&logoColor=white" alt="Platforms">
  <img src="https://img.shields.io/badge/docs-live-b31b1b" alt="Docs">
<img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json" alt="uv">
</p>
<p align="center">
<strong>Install and update LLM agent skills and prompts for supported CLI tools.</strong><br>
Manage user-level skills and prompt templates for <code>pi</code>, <code>openclaw</code>, <code>codex</code>, <code>antigravity</code>, and <code>claude</code>.
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
- Install manifest-listed prompt templates for `pi` and `claude`.
- Replace managed skill directories on every install and remove files that are no longer packaged.
- Enable or disable each target CLI; the selection persists in `~/.config/skills/config.json`.
- Inspect packaged resources, CLI configuration, and installation status with `show`.
- Check GitHub releases automatically with a 2-second timeout and a cached idle delay.
- Run from a repository checkout, as a uv tool, or with uvx.

Bundled skills:

- `astra-uv-project` - create a new Astral uv Python CLI project from scratch.
- `prompt-skill-architect` - create, review, and optimize LLM agent prompts and skills.


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
   uv tool install skills --force --from git+https://github.com/Ogekuri/SKILLs.git
   ```

2. Enable one or more target CLIs:

   ```bash
   skills enable pi
   skills enable claude
   ```

3. Install the bundled resources:

   ```bash
   skills install
   ```

4. Start or restart the target CLI so it discovers the installed skills.
5. Optional: review packaged resources and installation status:

   ```bash
   skills show
   ```

`enable` and `disable` persist their selection; `install` updates every enabled CLI.


## Commands

| Command | Behavior |
|---|---|
| `skills` | Print the full help screen. |
| `skills --help` | Print the full help screen. |
| `skills <command> --help` | Print help for `enable`, `disable`, `install`, `show`, `--upgrade`, `--uninstall`, `--ver`, or `--version`. |
| `skills --ver` | Print the installed version as `x.y.z` and force a release check. |
| `skills --version` | Print the installed version as `x.y.z` and force a release check. |
| `skills --upgrade` | Reinstall the tool with uv on Linux; print the manual command on other platforms. |
| `skills --uninstall` | Uninstall the tool with uv on Linux; print the manual command on other platforms. |
| `skills enable <cli name>` | Enable skill and prompt installation for a supported CLI. |
| `skills disable <cli name>` | Disable skill and prompt installation for a supported CLI. |
| `skills install` | Install or update bundled skills and prompts for every enabled CLI. |
| `skills show` | Show packaged resources, CLI configuration, and installation status. |

Exit codes:

- `0` - success, including `install` with no enabled CLI.
- `1` - installation failed for at least one enabled CLI.
- `2` - unknown command or option, unsupported CLI name, or missing CLI name.


## Supported CLI Targets

| CLI | Skills directory | Prompts directory |
|---|---|---|
| `pi` | `~/.pi/agent/skills` | `~/.pi/agent/prompts` |
| `openclaw` | `~/.openclaw/workspace/skills` | Not supported |
| `codex` | `~/.codex/skills` | Not supported |
| `antigravity` | `~/.gemini/config/skills` | Not supported |
| `claude` | `~/.claude/skills` | `~/.claude/commands` |

Only enabled CLIs are updated. Destinations are user-level configuration directories, not project directories.

Only manifest-listed prompt files are installed; the current package contains no prompt templates.


## Install Behavior

- `install` processes every enabled CLI.
- Each packaged skill is copied to `<skills directory>/<skill name>`.
- Existing skill files are overwritten with the packaged versions.
- Files and directories inside a managed skill directory that are absent from the package are deleted.
- Skill directories not managed by the package are left unchanged.
- Previously installed prompt files that are no longer packaged are deleted.
- A missing packaged source path aborts that CLI and reports an error; remaining enabled CLIs are still processed.
- Output reports the installed skill and prompt counts for each processed CLI.
- With no enabled CLI, `install` prints an informational message and exits with `0`.
- If any CLI installation fails, `install` prints the error and exits with `1`.


## Configuration

The CLI stores its user configuration at:

```text
~/.config/skills/config.json
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

`enable` and `disable` maintain the `enabled` array. The file may also contain prompt installation records, which are maintained automatically; edit only `enabled` when changing the configuration manually. A missing or invalid file is treated as an empty configuration.


## Release Checks

- A release check runs before command dispatch.
- The check requests the latest GitHub release with a 2-second timeout.
- Cache file: `~/.cache/skills/check_version_idle-time.json`.
- The check is skipped while the cached idle time is valid.
- `--ver` and `--version` force a check regardless of the cache.
- A newer release prints a bright-green message and sets a 3600-second idle delay.
- A failed check or no newer release prints a bright-red message and sets an 86400-second idle delay.
- Notifications are written to stderr.


## Upgrade and Uninstall

The tool is installed with Astral uv (see [Quick Start](#quick-start)). Upgrade through the CLI:

```bash
skills --upgrade
```

Uninstall through the CLI:

```bash
skills --uninstall
```

Manual uninstall:

```bash
uv tool uninstall skills
```


## Live execution with uvx

Run `skills` from the repository without installing the tool:

```bash
uvx --from git+https://github.com/Ogekuri/SKILLs.git skills --help
```

Use the same form for installation commands, for example:

```bash
uvx --from git+https://github.com/Ogekuri/SKILLs.git skills install
```


## Local Execution

Run the CLI from the repository checkout:

```bash
./scripts/skills.sh --help
./scripts/skills.sh enable pi
./scripts/skills.sh install
```

The launcher delegates execution to Astral uv from the repository root.


## Development

Run the tests:

```bash
uv run python -m unittest discover -s tests
```

Build distributions:

```bash
uv run --frozen --with build python -m build
```


## Acknowledgments

Uses [Astral uv](https://docs.astral.sh/uv/) for packaging and execution and the [Agent Skills](https://agentskills.io/specification) directory format for bundled resources.
