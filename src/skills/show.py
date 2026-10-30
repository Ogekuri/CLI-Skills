"""
@file show.py
@brief Render packaged resource inventory, CLI configuration, and installation status.
@details Builds three deterministic ASCII tables: bundled skills and prompts from
         the manifest, every supported CLI with enabled state and destination
         paths, and a per-resource per-CLI installation status derived from
         destination-directory scans.
@satisfies DES-065 DES-066 REQ-037 REQ-038 REQ-039 REQ-040 REQ-041
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Sequence

from .catalog import RESOURCES_ROOT, build_catalog
from .settings import load_config
from .targets import TARGETS

## @brief Maximum rendered width of one table cell in characters.
MAX_CELL_WIDTH = 48
## @brief Status value for a resource whose destination files match the package.
STATUS_OK = "OK"
## @brief Status value for a resource with missing destination directories or files.
STATUS_MISSING = "MISSING"
## @brief Status value for a resource whose destination files differ from the package.
STATUS_STALE = "STALE"
## @brief Status value for prompt installation on a CLI without prompts support.
STATUS_UNSUPPORTED = "UNSUPPORTED"


def _wrap(text: str, width: int) -> list[str]:
    """
    @brief Wrap one cell value into fixed-width lines on word boundaries.
    @details Collapses whitespace, splits overlong tokens into `width`-sized
             chunks, and greedily packs words without exceeding `width`.
    @param text {str} Cell value to wrap.
    @param width {int} Maximum line width in characters; MUST be positive.
    @return {list[str]} Rendered lines; `[""]` for an empty value.
    @satisfies DES-066
    """
    normalized = " ".join(str(text).split())
    if not normalized:
        return [""]
    lines: list[str] = []
    current = ""
    for word in normalized.split(" "):
        while len(word) > width:
            if current:
                lines.append(current)
                current = ""
            lines.append(word[:width])
            word = word[width:]
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= width:
            current = f"{current} {word}"
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def render_table(
    headers: Sequence[str],
    rows: Iterable[Sequence[str]],
    max_width: int = MAX_CELL_WIDTH,
) -> str:
    """
    @brief Render an ASCII grid table with aligned and wrapped cells.
    @details Column widths are the longest cell capped by `max_width`; every
             row is emitted between `+---+` borders and multi-line cells are
             padded to the row height.
    @param headers {Sequence[str]} Column header labels.
    @param rows {Iterable[Sequence[str]]} Row cell values; short rows are padded.
    @param max_width {int} Maximum column width in characters.
    @return {str} Rendered table text without trailing newline.
    @satisfies DES-066
    """
    data = [[str(cell) for cell in row] for row in rows]
    columns = len(headers)
    widths = []
    for index in range(columns):
        lengths = [len(str(headers[index]))]
        lengths.extend(len(row[index]) for row in data if index < len(row))
        widths.append(max(1, min(max(lengths), max(1, max_width))))
    border = "+" + "+".join("-" * (width + 2) for width in widths) + "+"

    def render(cells: Sequence[str]) -> list[str]:
        wrapped = [
            _wrap(cells[index] if index < len(cells) else "", widths[index])
            for index in range(columns)
        ]
        height = max(len(part) for part in wrapped)
        lines: list[str] = []
        for line_index in range(height):
            parts = [
                wrapped[index][line_index] if line_index < len(wrapped[index]) else ""
                for index in range(columns)
            ]
            lines.append(
                "| "
                + " | ".join(part.ljust(widths[index]) for index, part in enumerate(parts))
                + " |"
            )
        return lines

    lines = [border, *render(list(headers)), border]
    for row in data:
        lines.extend(render(row))
        lines.append(border)
    return "\n".join(lines)


def _resource_rows(
    catalog: dict[str, list[dict[str, str]]],
) -> list[tuple[str, str, str, str]]:
    """
    @brief Build inventory rows from manifest catalog entries.
    @details Emits skills before prompts, preserving manifest entry order.
    @param catalog {dict[str, list[dict[str, str]]]} Manifest catalog.
    @return {list[tuple[str, str, str, str]]} `(type, name, file, description)` rows.
    @satisfies REQ-037
    """
    rows: list[tuple[str, str, str, str]] = []
    for kind, key in (("Skill", "skills"), ("Prompt", "prompts")):
        for entry in catalog.get(key, []):
            rows.append(
                (
                    kind,
                    entry.get("name", ""),
                    entry.get("file", ""),
                    entry.get("description", ""),
                )
            )
    return rows


def _cli_rows(
    config: dict[str, Any],
    home: Path | None,
) -> list[tuple[str, str, str, str]]:
    """
    @brief Build CLI configuration rows from the adapter registry.
    @details Reports registry order, enabled state, skills destination, and
             prompts destination or `UNSUPPORTED` for prompt-less adapters.
    @param config {dict[str, object]} Normalized user configuration.
    @param home {Path | None} Optional home-directory override.
    @return {list[tuple[str, str, str, str]]} `(cli, enabled, skills path,
            prompts path)` rows.
    @satisfies REQ-038
    """
    enabled = set(config.get("enabled", []))
    rows: list[tuple[str, str, str, str]] = []
    for name, target in TARGETS.items():
        prompts = target.prompts_dir(home)
        rows.append(
            (
                name,
                "yes" if name in enabled else "no",
                str(target.skills_dir(home)),
                str(prompts) if prompts is not None else STATUS_UNSUPPORTED,
            )
        )
    return rows


def _files_match(source: Path, destination: Path) -> str:
    """
    @brief Compare one packaged file with its installed destination file.
    @param source {Path} Packaged file path.
    @param destination {Path} Installed destination file path.
    @return {str} `OK` for identical bytes, `MISSING` for absent destination,
            `STALE` for differing bytes or unreadable content.
    @satisfies REQ-040
    """
    try:
        if not destination.is_file():
            return STATUS_MISSING
        if source.read_bytes() != destination.read_bytes():
            return STATUS_STALE
    except OSError:
        return STATUS_STALE
    return STATUS_OK


def _skill_status(source: Path, destination: Path) -> str:
    """
    @brief Compare a packaged skill directory with its installed copy.
    @details Every packaged regular file must exist in the destination with
             identical bytes.
    @param source {Path} Packaged skill directory.
    @param destination {Path} Installed skill destination directory.
    @return {str} `OK` when all files match; `MISSING` when the package or a
            destination file is absent; `STALE` on content mismatch.
    @satisfies REQ-040
    """
    if not source.is_dir() or not destination.is_dir():
        return STATUS_MISSING
    found = False
    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        found = True
        status = _files_match(path, destination / path.relative_to(source))
        if status != STATUS_OK:
            return status
    return STATUS_OK if found else STATUS_MISSING


def _install_rows(
    catalog: dict[str, list[dict[str, str]]],
    config: dict[str, Any],
    home: Path | None,
) -> list[tuple[str, str, str, str, str]]:
    """
    @brief Build per-resource per-CLI installation status rows.
    @details Scans adapter destination directories for each manifest skill or
             prompt and reports the enabled state of the owning CLI.
    @param catalog {dict[str, list[dict[str, str]]]} Manifest catalog.
    @param config {dict[str, object]} Normalized user configuration.
    @param home {Path | None} Optional home-directory override.
    @return {list[tuple[str, str, str, str, str]]} `(type, name, cli, enabled,
            installed)` rows.
    @satisfies REQ-039 REQ-040 REQ-041
    """
    enabled = set(config.get("enabled", []))
    rows: list[tuple[str, str, str, str, str]] = []
    for kind, key in (("Skill", "skills"), ("Prompt", "prompts")):
        for entry in catalog.get(key, []):
            relative = entry.get("file", "")
            source = RESOURCES_ROOT / relative
            for name, target in TARGETS.items():
                if kind == "Skill":
                    status = _skill_status(
                        source.parent,
                        target.skills_dir(home) / source.parent.name,
                    )
                else:
                    prompts = target.prompts_dir(home)
                    status = (
                        STATUS_UNSUPPORTED
                        if prompts is None
                        else _files_match(source, prompts / source.name)
                    )
                rows.append(
                    (
                        kind,
                        entry.get("name", ""),
                        name,
                        "yes" if name in enabled else "no",
                        status,
                    )
                )
    return rows


def build_show(home: Path | None = None) -> str:
    """
    @brief Build the complete `show` report text.
    @details Renders the packaged-resource inventory, CLI configuration, and
             installation status tables in this order.
    @param home {Path | None} Optional home-directory override for deterministic
            destination resolution.
    @return {str} Report text with three titled tables separated by blank lines.
    @throws {OSError} When the manifest or bundled resources cannot be read.
    @satisfies DES-065 REQ-037 REQ-038 REQ-039 REQ-042
    """
    catalog = build_catalog()
    config = load_config(home)
    return "\n".join(
        [
            "Packaged Resources",
            render_table(
                ("Type", "Name", "File", "Description"),
                _resource_rows(catalog),
            ),
            "",
            "CLI Configuration",
            render_table(
                ("CLI", "Enabled", "Skills Path", "Prompts Path"),
                _cli_rows(config, home),
            ),
            "",
            "Installation Status",
            render_table(
                ("Type", "Name", "CLI", "Enabled", "Installed"),
                _install_rows(catalog, config, home),
            ),
        ]
    )
