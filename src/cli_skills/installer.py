"""
@file installer.py
@brief Orchestrate skill and prompt installation for enabled CLI targets.
@details Builds the bundled resource catalog, resolves manifest skill
         directories and prompt files, invokes the configured CLI adapters,
         updates prompt records, and aggregates per-CLI outcomes for
         installation and uninstallation. Rejects a non-canonical skill
         support layout through the catalog builder.
@satisfies PRJ-009 PRJ-011 REQ-029 REQ-030 REQ-032 REQ-035 REQ-047 REQ-048 REQ-049 REQ-050 REQ-051 REQ-052 REQ-053 REQ-056 DES-055 DES-059 DES-060 DES-061 DES-062 DES-064 DES-073
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .catalog import RESOURCES_ROOT, SkillLayoutError, build_catalog
from .settings import load_config, save_config
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
    @details Carries the canonical CLI name, installed skill count, sorted
             installed skill directory names, installed prompt count, and
             installed prompt filenames for persistence and reporting.
    @satisfies REQ-030 REQ-057 DES-060
    """

    ## @brief Canonical CLI name.
    cli: str
    ## @brief Number of installed skill directories.
    skills: int
    ## @brief Sorted installed skill directory names.
    skill_names: tuple[str, ...]
    ## @brief Number of installed prompt files.
    prompts: int
    ## @brief Sorted installed prompt filenames.
    prompt_files: tuple[str, ...]


@dataclass(frozen=True)
class UninstallSummary:
    """
    @brief Summarize one CLI uninstallation result.
    @details Carries the canonical CLI name, processed manifest skill
             directory count, and processed managed prompt filename count.
             Missing destinations count as removed.
    @satisfies REQ-054
    """

    ## @brief Canonical CLI name.
    cli: str
    ## @brief Number of processed manifest skill directory names.
    skills: int
    ## @brief Number of processed managed prompt filenames.
    prompts: int


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


def _prompt_files(
    resources_root: Path,
    entries: Iterable[dict[str, str]],
) -> list[Path]:
    """
    @brief Resolve manifest prompt entries to packaged prompt files.
    @details Validates each entry file path and rejects duplicate destination
             filenames that would overwrite each other.
    @param resources_root {Path} Resources root directory.
    @param entries {Iterable[dict[str, str]]} Manifest prompt entries.
    @return {list[Path]} Packaged prompt files sorted by relative path.
    @throws {InstallError} When a manifest-listed prompt file is missing or two
            entries share the same destination filename.
    @satisfies DES-059 DES-062 REQ-035
    """
    files: list[Path] = []
    names: set[str] = set()
    for entry in sorted(entries, key=lambda item: item.get("file", "")):
        relative = entry.get("file")
        if not relative:
            raise InstallError("Prompt manifest entry is missing a file path.")
        prompt_file = resources_root / relative
        if not prompt_file.is_file():
            raise InstallError(f"Missing prompt file: {prompt_file}")
        if prompt_file.name in names:
            raise InstallError(f"Duplicate prompt filename: {prompt_file.name}")
        names.add(prompt_file.name)
        files.append(prompt_file)
    return files


def install_target(
    target: CliTarget,
    catalog: dict[str, list[dict[str, str]]],
    previous_prompts: Iterable[str],
    resources_root: Path = RESOURCES_ROOT,
    home: Path | None = None,
) -> InstallSummary:
    """
    @brief Install manifest skills and prompts for one CLI target.
    @details Resolves manifest sources, delegates skill synchronization and
             prompt-file replacement to the adapter, and returns installed
             counts and prompt filenames.
    @param target {CliTarget} CLI adapter to install.
    @param catalog {dict[str, list[dict[str, str]]]} Manifest catalog.
    @param previous_prompts {Iterable[str]} Previously installed prompt filenames.
    @param resources_root {Path} Resources root directory.
    @param home {Path | None} Optional home-directory override.
    @return {InstallSummary} Installed skill and prompt counts.
    @throws {InstallError} When a manifest-listed source path is missing.
    @throws {OSError} When copying, pruning, or directory creation fails.
    @satisfies REQ-029 REQ-030 REQ-057 DES-055 DES-056 DES-057 DES-059 DES-061 DES-062
    """
    skills = _skill_directories(resources_root, catalog.get("skills", []))
    prompts = _prompt_files(resources_root, catalog.get("prompts", []))
    skill_count = target.install_skills(skills, home)
    prompt_files = target.install_prompts(prompts, previous_prompts, home)
    return InstallSummary(
        cli=target.name,
        skills=skill_count,
        skill_names=tuple(sorted(path.name for path in skills)),
        prompts=len(prompt_files),
        prompt_files=tuple(prompt_files),
    )


def install_enabled(
    home: Path | None = None,
) -> tuple[list[InstallSummary], list[str]]:
    """
    @brief Install bundled resources for every enabled CLI.
    @details Loads user configuration and builds the resource catalog once.
             Processes each enabled CLI independently, persists prompt records
             after each successful CLI, and collects failures without stopping
             remaining CLI processing.
    @param home {Path | None} Optional home-directory override.
    @return {tuple[list[InstallSummary], list[str]]} Installation summaries and
            failure diagnostics; both empty when no CLI is enabled.
    @satisfies REQ-029 REQ-030 REQ-031 REQ-032 DES-064 DES-073
    """
    config = load_config(home)
    enabled = config["enabled"]
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
        previous = config["prompts"].get(target.name, [])
        try:
            summary = install_target(target, catalog, previous, home=home)
        except (InstallError, OSError) as exc:
            errors.append(f"{target.name}: {exc}")
            continue
        config["prompts"][target.name] = list(summary.prompt_files)
        try:
            save_config(config, home)
        except OSError as exc:
            errors.append(f"{target.name}: configuration write failed: {exc}")
        summaries.append(summary)
    return summaries, errors


def uninstall_target(
    target: CliTarget,
    catalog: dict[str, list[dict[str, str]]],
    recorded_prompts: Iterable[str],
    resources_root: Path = RESOURCES_ROOT,
    home: Path | None = None,
) -> UninstallSummary:
    """
    @brief Remove manifest skills and installed prompts for one CLI target.
    @details Resolves manifest skill directory names and the union of
             manifest prompt filenames with previously recorded prompt
             filenames, then delegates deletion to the adapter removal
             methods. Missing destinations count as removed. Destination
             entries outside manifest skill names and managed prompt names
             are preserved.
    @param target {CliTarget} CLI adapter to clean.
    @param catalog {dict[str, list[dict[str, str]]]} Manifest catalog.
    @param recorded_prompts {Iterable[str]} Previously recorded prompt
            filenames for this CLI.
    @param resources_root {Path} Resources root directory.
    @param home {Path | None} Optional home-directory override.
    @return {UninstallSummary} Removed skill and prompt counts.
    @throws {InstallError} When a manifest-listed source path is missing.
    @throws {OSError} When destination deletion fails.
    @satisfies REQ-047 REQ-048 REQ-049 REQ-051 REQ-052
    """
    skills = _skill_directories(resources_root, catalog.get("skills", []))
    prompts = _prompt_files(resources_root, catalog.get("prompts", []))
    skill_names = sorted({path.name for path in skills})
    prompt_names = sorted({path.name for path in prompts} | set(recorded_prompts))
    skill_count = target.remove_skills(skill_names, home)
    prompt_count = target.remove_prompts(prompt_names, home)
    return UninstallSummary(
        cli=target.name,
        skills=skill_count,
        prompts=prompt_count,
    )


def uninstall_enabled(
    home: Path | None = None,
) -> tuple[list[UninstallSummary], list[str]]:
    """
    @brief Remove installed bundled resources for every enabled CLI.
    @details Loads user configuration and builds the resource catalog once.
             Processes each enabled CLI independently, clears recorded prompt
             filenames after each successful CLI, and collects failures
             without stopping remaining CLI processing.
    @param home {Path | None} Optional home-directory override.
    @return {tuple[list[UninstallSummary], list[str]]} Uninstallation summaries
            and failure diagnostics; both empty when no CLI is enabled.
    @satisfies REQ-047 REQ-050 REQ-053 REQ-056
    """
    config = load_config(home)
    enabled = config["enabled"]
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
        recorded = config["prompts"].get(target.name, [])
        try:
            summary = uninstall_target(target, catalog, recorded, home=home)
        except (InstallError, OSError) as exc:
            errors.append(f"{target.name}: {exc}")
            continue
        config["prompts"][target.name] = []
        try:
            save_config(config, home)
        except OSError as exc:
            errors.append(f"{target.name}: configuration write failed: {exc}")
        summaries.append(summary)
    return summaries, errors
