"""
@file render.py
@brief Deterministic tree and table rendering primitives shared by every hierarchical command.
@details The renderer is data driven: a `Node` tree of real configuration nodes
         carries headings, attached detail lines, and real children. Structural
         prefixes depend only on real siblings, never on column widths, text
         length, or detail counts. Attached detail lines reuse the owning node
         continuation prefix and never carry structural markers.
@satisfies DES-118 DES-119 DES-120 DES-127
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Iterable, Sequence

## @brief Structural marker of a node with a later real sibling.
BRANCH = "├── "
## @brief Structural marker of the final real sibling.
LAST = "└── "
## @brief Ancestor segment of a level without later real siblings.
INDENT = "    "
## @brief Ancestor segment of a level with later real siblings.
CONTINUE = "│   "
## @brief Detail indentation below an unconnected display root.
ROOT_DETAIL_INDENT = "    "


@dataclass(frozen=True)
class Node:
    """
    @brief One real configuration node with attached details and real children.
    @details `details` holds zero or more single-line logical detail strings
             such as metadata, commands, and rendered table rows. Details never
             become tree levels and never receive structural markers.
    @param heading {str} Single-line node heading without any tree marker.
    @param details {tuple[str, ...]} Attached single-line detail strings.
    @param children {tuple[Node, ...]} Real child nodes in canonical order.
    @satisfies DES-118 DES-119
    """

    heading: str
    details: tuple[str, ...] = ()
    children: tuple[Node, ...] = ()


def render_tree(root: Node) -> str:
    """
    @brief Render one configuration tree exactly as required by the prefix algorithm.
    @details Emits the marker-free root heading, its details under a four-space
             indent, then every real child through `_emit_node`. Complexity
             O(N) over emitted lines.
    @param root {Node} Unconnected display root.
    @return {str} Rendered tree text without trailing newline.
    @throws {ValueError} When a heading or detail is not a single physical line.
    @satisfies DES-118 DES-119 DES-127
    """
    lines = [_check_line(root.heading, "heading")]
    for detail in root.details:
        lines.append(ROOT_DETAIL_INDENT + _check_line(detail, "detail"))
    total = len(root.children)
    for index, child in enumerate(root.children):
        _emit_node(child, (), index == total - 1, lines)
    return "\n".join(lines)


def display_width(text: str) -> int:
    """
    @brief Measure the terminal display width of one text value.
    @details Combining marks and format characters count as zero width; East
             Asian wide and fullwidth characters count as two columns.
    @param text {str} Text to measure.
    @return {int} Display width in terminal columns.
    @satisfies DES-120
    """
    width = 0
    for char in text:
        if unicodedata.combining(char) or unicodedata.category(char) in ("Mn", "Me", "Cf"):
            continue
        width += 2 if unicodedata.east_asian_width(char) in ("W", "F") else 1
    return width


def render_table(headers: Sequence[str], rows: Iterable[Sequence[str]]) -> list[str]:
    """
    @brief Render one rectangular box-drawing table with measured column widths.
    @details Column widths derive from the maximum display width of the header
             and every cell, with one padding space per side. Border characters
             `┌ ┬ ┐ ├ ┼ ┤ └ ┴ ┘ ─ │` align on shared column boundaries. Cells are
             never truncated; every row MUST supply exactly one cell per column.
    @param headers {Sequence[str]} Column header labels.
    @param rows {Iterable[Sequence[str]]} Row cell values.
    @return {list[str]} Rendered table lines without prefixes and without newlines.
    @throws {ValueError} When no column is declared, a row has the wrong cell
             count, or a cell is not a single physical line.
    @satisfies DES-120 DES-121 DES-123
    """
    labels = [_check_line(str(header), "table header") for header in headers]
    if not labels:
        raise ValueError("A table requires at least one column.")
    data: list[list[str]] = []
    for row in rows:
        cells = [_check_line(str(cell), "table cell") for cell in row]
        if len(cells) != len(labels):
            raise ValueError(f"Table row has {len(cells)} cells; expected {len(labels)}.")
        data.append(cells)
    widths = [max(display_width(cells[column]) for cells in [labels, *data]) for column in range(len(labels))]
    lines = [_border(widths, "┌", "┬", "┐")]
    lines.extend(_row(labels, widths))
    lines.append(_border(widths, "├", "┼", "┤"))
    for cells in data:
        lines.extend(_row(cells, widths))
    lines.append(_border(widths, "└", "┴", "┘"))
    return lines


def _emit_node(node: Node, ancestors: tuple[bool, ...], is_last: bool, lines: list[str]) -> None:
    """
    @brief Emit one real node, its attached details, and its real children.
    @details The ancestor tuple records only whether each real ancestor has a
             later real sibling. Detail lines reuse that prefix plus exactly one
             own continuation segment and never carry tree markers.
    @param node {Node} Real node to emit.
    @param ancestors {tuple[bool, ...]} Later-sibling flags of real ancestors.
    @param is_last {bool} Whether `node` is the final real sibling.
    @param lines {list[str]} Accumulated output lines.
    @return {None}
    @throws {ValueError} When a heading or detail is not a single physical line.
    @satisfies DES-118 DES-119
    """
    prefix = "".join(CONTINUE if later else INDENT for later in ancestors)
    lines.append(prefix + (LAST if is_last else BRANCH) + _check_line(node.heading, "heading"))
    detail_prefix = prefix + (INDENT if is_last else CONTINUE)
    for detail in node.details:
        lines.append(detail_prefix + _check_line(detail, "detail"))
    total = len(node.children)
    for index, child in enumerate(node.children):
        _emit_node(child, ancestors + (not is_last,), index == total - 1, lines)


def _border(widths: Sequence[int], left: str, middle: str, right: str) -> str:
    """
    @brief Build one table border line aligned with the measured column widths.
    @param widths {Sequence[int]} Content width of every column.
    @param left {str} Left border character.
    @param middle {str} Column separator character.
    @param right {str} Right border character.
    @return {str} Border line.
    @satisfies DES-120
    """
    return left + middle.join("─" * (width + 2) for width in widths) + right


def _row(cells: Sequence[str], widths: Sequence[int]) -> list[str]:
    """
    @brief Build one padded table row.
    @param cells {Sequence[str]} Cell values matching the declared columns.
    @param widths {Sequence[int]} Content width of every column.
    @return {list[str]} Single rendered row line.
    @satisfies DES-120
    """
    padded = [
        cell + " " * (width - display_width(cell))
        for cell, width in zip(cells, widths)
    ]
    return ["│ " + " │ ".join(padded) + " │"]


def _check_line(text: str, role: str) -> str:
    """
    @brief Enforce the single-physical-line invariant for one rendered string.
    @details Rejects embedded newlines, carriage returns, tabs, and other
             control characters so one logical line stays one output line.
    @param text {str} Candidate heading, detail, or cell.
    @param role {str} Human-readable role used in the diagnostic.
    @return {str} The unchanged text when valid.
    @throws {ValueError} When the text contains a control character.
    @satisfies DES-118 DES-119
    """
    for char in text:
        if char in "\n\r\t" or unicodedata.category(char) == "Cc":
            raise ValueError(f"Rendered {role} MUST be a single line without control characters: {text!r}")
    return text
