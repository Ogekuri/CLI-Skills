"""
@file targets.py
@brief Provide per-CLI skill installation adapters.
@details Defines the `CliTarget` abstraction and one concrete adapter for each
         supported CLI: `pi`, `openclaw`, `codex`, `antigravity`, and `claude`.
         Adapters resolve user-level skill destination directories from a home
         root and provide deterministic copy algorithms for skills.
         Shared copy primitives synchronize packaged trees, overwrite changed
         files, and prune destination entries absent from the package.
         Removal primitives delete managed skill directories while preserving
         unmanaged destination entries.
@satisfies PRJ-010 PRJ-011 DES-049 DES-050 DES-051 DES-052 DES-053 DES-054 DES-055 DES-056 DES-057 DES-058 DES-063 REQ-048 REQ-051 REQ-052
"""

from __future__ import annotations

import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable


def resolve_home(home: Path | None) -> Path:
    """
    @brief Resolve the user home directory used for destination paths.
    @details Returns the explicit override when provided; otherwise resolves
             `Path.home()`. Centralizes home resolution for deterministic tests
             and adapter reuse.
    @param home {Path | None} Optional home-directory override.
    @return {Path} Effective home directory path.
    @satisfies DES-049
    """
    return Path.home() if home is None else home


def sync_skill_tree(source: Path, destination: Path) -> None:
    """
    @brief Replace a destination skill directory with packaged contents.
    @details Copies the source tree recursively with overwrite, then removes
             destination files and directories absent from the source tree.
             Destination skill files become byte-identical copies of package
             files. Pruning runs deepest-first to keep directory removal safe.
    @param source {Path} Packaged skill directory containing `SKILL.md`.
    @param destination {Path} Target skill directory named after `source.name`.
    @return {None}
    @throws {OSError} When directory creation, copying, or pruning fails.
    @pre `source` MUST be an existing directory.
    @post `destination` contains exactly the source tree paths and contents.
    @complexity O(S + D) where S is source entries and D is destination entries.
    @satisfies DES-055 DES-056 DES-057 DES-063
    """
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination, dirs_exist_ok=True)
    expected = {path.relative_to(source) for path in source.rglob("*")}
    existing = sorted(
        destination.rglob("*"),
        key=lambda path: (len(path.parts), str(path)),
        reverse=True,
    )
    for path in existing:
        if path.relative_to(destination) in expected:
            continue
        if path.is_dir() and not path.is_symlink():
            path.rmdir()
        else:
            path.unlink()


class CliTarget(ABC):
    """
    @brief Abstract adapter for a supported CLI installation target.
    @details Subclasses declare the CLI name and resolve the user-level skill
             destination directory. Base methods implement deterministic
             skill-tree synchronization and managed skill removal.
    @satisfies DES-049 REQ-048
    """

    ## @brief Canonical CLI name used by the `enable` and `disable` commands.
    name: str

    @abstractmethod
    def skills_dir(self, home: Path | None = None) -> Path:
        """
        @brief Resolve the CLI user-level skills destination directory.
        @param home {Path | None} Optional home-directory override.
        @return {Path} Skills destination directory.
        @satisfies DES-050 DES-051 DES-052 DES-053 DES-054
        """

    def install_skills(self, sources: Iterable[Path], home: Path | None = None) -> int:
        """
        @brief Install packaged skill directories into this CLI destination.
        @details Synchronizes each source directory into
                 `<skills_dir>/<source.name>` using `sync_skill_tree`.
        @param sources {Iterable[Path]} Packaged skill directories.
        @param home {Path | None} Optional home-directory override.
        @return {int} Number of processed skill directories.
        @throws {OSError} When synchronization fails.
        @satisfies DES-055 DES-056 DES-057 DES-063
        """
        root = self.skills_dir(home)
        count = 0
        for source in sources:
            sync_skill_tree(source, root / source.name)
            count += 1
        return count

    def remove_skills(self, names: Iterable[str], home: Path | None = None) -> int:
        """
        @brief Remove managed skill directories from this CLI destination.
        @details Deletes `<skills_dir>/<name>` recursively for each name.
                 Missing destinations count as removed and do not raise.
                 Destination entries outside `names` are preserved and no
                 directory is created. Complexity O(N) deletions where N is
                 the number of names.
        @param names {Iterable[str]} Managed skill directory names.
        @param home {Path | None} Optional home-directory override.
        @return {int} Number of processed names; missing destinations count
                as removed.
        @throws {OSError} When recursive directory deletion fails.
        @satisfies REQ-048 REQ-051 REQ-052
        """
        root = self.skills_dir(home)
        count = 0
        for name in names:
            destination = root / name
            if destination.is_dir():
                shutil.rmtree(destination)
            count += 1
        return count

class PiTarget(CliTarget):
    """
    @brief Installation adapter for the `pi` coding agent.
    @details Installs skills under `$HOME/.pi/agent/skills`.
    @satisfies DES-050
    """

    name = "pi"

    def skills_dir(self, home: Path | None = None) -> Path:
        """
        @brief Resolve the pi user-level skills directory.
        @param home {Path | None} Optional home-directory override.
        @return {Path} `$HOME/.pi/agent/skills`.
        @satisfies DES-050
        """
        return resolve_home(home) / ".pi" / "agent" / "skills"


class OpenClawTarget(CliTarget):
    """
    @brief Installation adapter for the `openclaw` agent workspace.
    @details Installs skills under `$HOME/.openclaw/workspace/skills`.
    @satisfies DES-051
    """

    name = "openclaw"

    def skills_dir(self, home: Path | None = None) -> Path:
        """
        @brief Resolve the openclaw user-level skills directory.
        @param home {Path | None} Optional home-directory override.
        @return {Path} `$HOME/.openclaw/workspace/skills`.
        @satisfies DES-051
        """
        return resolve_home(home) / ".openclaw" / "workspace" / "skills"


class CodexTarget(CliTarget):
    """
    @brief Installation adapter for the `codex` CLI.
    @details Installs skills under `$HOME/.codex/skills`.
    @satisfies DES-052
    """

    name = "codex"

    def skills_dir(self, home: Path | None = None) -> Path:
        """
        @brief Resolve the codex user-level skills directory.
        @param home {Path | None} Optional home-directory override.
        @return {Path} `$HOME/.codex/skills`.
        @satisfies DES-052
        """
        return resolve_home(home) / ".codex" / "skills"


class AntigravityTarget(CliTarget):
    """
    @brief Installation adapter for Google Antigravity.
    @details Installs skills under `$HOME/.gemini/config/skills`.
    @satisfies DES-053
    """

    name = "antigravity"

    def skills_dir(self, home: Path | None = None) -> Path:
        """
        @brief Resolve the antigravity user-level skills directory.
        @param home {Path | None} Optional home-directory override.
        @return {Path} `$HOME/.gemini/config/skills`.
        @satisfies DES-053
        """
        return resolve_home(home) / ".gemini" / "config" / "skills"


class ClaudeTarget(CliTarget):
    """
    @brief Installation adapter for the `claude` CLI.
    @details Installs skills under `$HOME/.claude/skills`.
    @satisfies DES-054
    """

    name = "claude"

    def skills_dir(self, home: Path | None = None) -> Path:
        """
        @brief Resolve the claude user-level skills directory.
        @param home {Path | None} Optional home-directory override.
        @return {Path} `$HOME/.claude/skills`.
        @satisfies DES-054
        """
        return resolve_home(home) / ".claude" / "skills"


## @brief Registry of supported CLI adapters keyed by canonical CLI name.
# @details Insertion order defines the supported-name listing in diagnostics.
# @satisfies DES-049
TARGETS: dict[str, CliTarget] = {
    target.name: target
    for target in (
        PiTarget(),
        OpenClawTarget(),
        CodexTarget(),
        AntigravityTarget(),
        ClaudeTarget(),
    )
}


def resolve_target(name: str) -> CliTarget | None:
    """
    @brief Resolve a CLI adapter by canonical name.
    @details Trims surrounding whitespace and lowercases the input before a
             registry lookup.
    @param name {str} CLI name supplied on the command line.
    @return {CliTarget | None} Matching adapter; `None` when unsupported.
    @satisfies REQ-026
    """
    return TARGETS.get(name.strip().lower())
