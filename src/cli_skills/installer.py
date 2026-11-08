"""
@file installer.py
@brief Orchestrate skill installation for enabled CLI targets.
@details Builds the bundled resource catalog, resolves manifest skill
         directories, invokes the configured CLI adapters, and aggregates
         per-CLI outcomes for installation and uninstallation. Rejects a
         non-canonical skill support layout through the catalog builder.
@satisfies PRJ-009 PRJ-011 REQ-029 REQ-030 REQ-032 REQ-035 REQ-047 REQ-048 REQ-051 REQ-052 REQ-053 REQ-056 DES-055 DES-062 DES-064 DES-073
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .catalog import RESOURCES_ROOT, SkillLayoutError, build_catalog
from .settings import load_config
from .targets import CliTarget, resolve_target


class InstallError(RuntimeError):
    """
    @brief Signal a manifest or packaged-resource installation failure.
    @details Raised when a manifest-listed source path is missing, duplicated,
             or otherwise not installable.
    @satisfies REQ-035
    """


@dataclass(frozen=True)
class InstallSummary:
    """
    @brief Summarize one CLI installation result.
    @details Carries the canonical CLI name, installed skill count, and sorted
             installed skill directory names for reporting.
    @satisfies REQ-030 REQ-057
    """

    ## @brief Canonical CLI name.
    cli: str
    ## @brief Number of installed skill directories.
    skills: int
    ## @brief Sorted installed skill directory names.
    skill_names: tuple[str, ...]


@dataclass(frozen=True)
class UninstallSummary:
    """
    @brief Summarize one CLI uninstallation result.
    @details Carries the canonical CLI name and processed manifest skill
             directory count. Missing destinations count as removed.
    @satisfies REQ-054
    """

    ## @brief Canonical CLI name.
    cli: str
    ## @brief Number of processed manifest skill directory names.
    skills: int


def _skill_directories(
    resources_root: Path,
    entries: Iterable[dict[str, str]],
) -> list[Path]:
    """
    @brief Resolve manifest skill entries to packaged skill directories.
    @details Validates each entry file path, deduplicates by directory name, and
             returns directories sorted by name.
    @param resources_root {Path} Resources root directory.
    @param entries {Iterable[dict[str, str]]} Manifest skill entries.
    @return {list[Path]} Sorted unique skill directories.
    @throws {InstallError} When a manifest-listed skill file or directory is
            missing.
    @satisfies DES-055 DES-062 REQ-035
    """
    directories: dict[str, Path] = {}
    for entry in entries:
        relative = entry.get("file")
        if not relative:
            raise InstallError("Skill manifest entry is missing a file path.")
        skill_file = resources_root / relative
        if not skill_file.is_file():
            raise InstallError(f"Missing skill file: {skill_file}")
        directory = skill_file.parent
        if not directory.is_dir():
            raise InstallError(f"Missing skill directory: {directory}")
        directories[directory.name] = directory
    return [directories[name] for name in sorted(directories)]


def install_target(
    target: CliTarget,
    catalog: dict[str, list[dict[str, str]]],
    resources_root: Path = RESOURCES_ROOT,
    home: Path | None = None,
) -> InstallSummary:
    """
    @brief Install manifest skills for one CLI target.
    @details Resolves manifest skill directories and delegates skill-tree
             synchronization to the adapter.
    @param target {CliTarget} CLI adapter to install.
    @param catalog {dict[str, list[dict[str, str]]]} Manifest catalog.
    @param resources_root {Path} Resources root directory.
    @param home {Path | None} Optional home-directory override.
    @return {InstallSummary} Installed skill count and names.
    @throws {InstallError} When a manifest-listed source path is missing.
    @throws {OSError} When copying, pruning, or directory creation fails.
    @satisfies REQ-029 REQ-030 REQ-057 DES-055 DES-056 DES-057 DES-062
    """
    skills = _skill_directories(resources_root, catalog.get("skills", []))
    skill_count = target.install_skills(skills, home)
    return InstallSummary(
        cli=target.name,
        skills=skill_count,
        skill_names=tuple(sorted(path.name for path in skills)),
    )


def install_enabled(
    home: Path | None = None,
) -> tuple[list[InstallSummary], list[str]]:
    """
    @brief Install bundled resources for every enabled CLI.
    @details Loads user configuration and builds the resource catalog once.
             Processes each enabled CLI independently and collects failures
             without stopping remaining CLI processing.
    @param home {Path | None} Optional home-directory override.
    @return {tuple[list[InstallSummary], list[str]]} Installation summaries and
            failure diagnostics; both empty when no CLI is enabled.
    @satisfies REQ-029 REQ-030 REQ-031 REQ-032 DES-064 DES-073
    """
    enabled = load_config(home)["enabled"]
    if not enabled:
        return [], []
    try:
        catalog = build_catalog()
    except (OSError, SkillLayoutError) as exc:
        return [], [f"catalog: {exc}"]
    summaries: list[InstallSummary] = []
    errors: list[str] = []
    for name in enabled:
        target = resolve_target(name)
        if target is None:
            errors.append(f"Unsupported CLI: {name}")
            continue
        try:
            summaries.append(install_target(target, catalog, home=home))
        except (InstallError, OSError) as exc:
            errors.append(f"{target.name}: {exc}")
    return summaries, errors


def uninstall_target(
    target: CliTarget,
    catalog: dict[str, list[dict[str, str]]],
    resources_root: Path = RESOURCES_ROOT,
    home: Path | None = None,
) -> UninstallSummary:
    """
    @brief Remove manifest skills for one CLI target.
    @details Resolves manifest skill directory names and delegates deletion to
             the adapter removal method. Missing destinations count as removed.
             Destination entries outside manifest skill names are preserved.
    @param target {CliTarget} CLI adapter to clean.
    @param catalog {dict[str, list[dict[str, str]]]} Manifest catalog.
    @param resources_root {Path} Resources root directory.
    @param home {Path | None} Optional home-directory override.
    @return {UninstallSummary} Removed skill count.
    @throws {InstallError} When a manifest-listed source path is missing.
    @throws {OSError} When destination deletion fails.
    @satisfies REQ-047 REQ-048 REQ-051 REQ-052
    """
    skills = _skill_directories(resources_root, catalog.get("skills", []))
    skill_names = sorted({path.name for path in skills})
    skill_count = target.remove_skills(skill_names, home)
    return UninstallSummary(
        cli=target.name,
        skills=skill_count,
    )


def uninstall_enabled(
    home: Path | None = None,
) -> tuple[list[UninstallSummary], list[str]]:
    """
    @brief Remove installed bundled resources for every enabled CLI.
    @details Loads user configuration and builds the resource catalog once.
             Processes each enabled CLI independently and collects failures
             without stopping remaining CLI processing.
    @param home {Path | None} Optional home-directory override.
    @return {tuple[list[UninstallSummary], list[str]]} Uninstallation summaries
            and failure diagnostics; both empty when no CLI is enabled.
    @satisfies REQ-047 REQ-053 REQ-056
    """
    enabled = load_config(home)["enabled"]
    if not enabled:
        return [], []
    try:
        catalog = build_catalog()
    except (OSError, SkillLayoutError) as exc:
        return [], [f"catalog: {exc}"]
    summaries: list[UninstallSummary] = []
    errors: list[str] = []
    for name in enabled:
        target = resolve_target(name)
        if target is None:
            errors.append(f"Unsupported CLI: {name}")
            continue
        try:
            summaries.append(uninstall_target(target, catalog, home=home))
        except (InstallError, OSError) as exc:
            errors.append(f"{target.name}: {exc}")
    return summaries, errors
