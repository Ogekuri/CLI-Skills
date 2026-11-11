"""
@file configview.py
@brief Build `--print` and `--info` node trees from the canonical schema.
@details Both commands render the same real configuration nodes through
         `render.render_tree`; only heading and detail formatters differ.
         Every command example is built from schema example values and
         shell-quoted so it stays copy/pasteable and type-valid.
@satisfies DES-118 DES-119 DES-121 DES-122 DES-123 DES-124 DES-125 DES-126 DES-129 DES-133
"""

from __future__ import annotations

import json
import shlex
from typing import Any

from . import configops, schema
from .render import Node, render_table, render_tree

## @brief Heading of the `--print` display root.
PRINT_ROOT = f"{schema.ROOT_LABEL} - Current configuration"
## @brief Heading of the `--info` display root.
INFO_ROOT = f"{schema.ROOT_LABEL} - Configuration schema reference"

## @brief Headers of the selection state table rendered by `--print`.
SELECTION_HEADERS: tuple[str, ...] = ("Sel", "Value")
## @brief Headers of the array index table rendered by `--print`.
ARRAY_HEADERS: tuple[str, ...] = ("Idx", "Value")
## @brief Headers of the allowed-values table rendered by `--info`.
ALLOWED_HEADERS: tuple[str, ...] = ("Value", "Default", "Meaning")


def render_print(config: dict[str, Any], path_text: str | None = None) -> str:
    """
    @brief Render the `--print` tree for the whole configuration or one subtree.
    @details Builds the node tree with `build_print` and renders it with the
             shared deterministic renderer.
    @param config {dict[str, Any]} Configuration object to display.
    @param path_text {str | None} Optional canonical path limiting the output.
    @return {str} Rendered tree text without trailing newline.
    @throws {schema.SchemaError} When the path cannot be resolved.
    @throws {configops.ConfigError} When the addressed value is unreadable.
    @satisfies DES-118 DES-122 DES-123 DES-127
    """
    return render_tree(build_print(config, path_text))


def build_print(config: dict[str, Any], path_text: str | None = None) -> Node:
    """
    @brief Build the `--print` node tree for the whole configuration or one subtree.
    @details Without a path the display root carries every section; with a path
             the requested node becomes the marker-free display root.
    @param config {dict[str, Any]} Configuration object to display.
    @param path_text {str | None} Optional canonical path limiting the output.
    @return {Node} Display root node.
    @throws {schema.SchemaError} When the path cannot be resolved.
    @throws {configops.ConfigError} When the addressed value is unreadable.
    @satisfies DES-118 DES-122 DES-127
    """
    if path_text is None:
        children = tuple(_print_section(section, (section.token,), config) for section in schema.SECTIONS)
        return Node(PRINT_ROOT, (), children)
    path = schema.parse_path(path_text)
    if path.node.kind == schema.KIND_SECTION:
        return _print_section(path.node, path.tokens, config)
    return _print_leaf(path.node, path.tokens, configops.get_value(config, path))


def render_info(path_text: str | None = None) -> str:
    """
    @brief Render the `--info` tree for the whole schema or one subtree.
    @details Uses the same renderer and node topology as `--print`, with schema
             headings, defaults, and command examples as attached details.
    @param path_text {str | None} Optional canonical path limiting the output.
    @return {str} Rendered tree text without trailing newline.
    @throws {schema.SchemaError} When the path cannot be resolved.
    @satisfies DES-118 DES-125 DES-126 DES-127
    """
    return render_tree(build_info(path_text))


def build_info(path_text: str | None = None) -> Node:
    """
    @brief Build the `--info` node tree for the whole schema or one subtree.
    @details Schema documentation needs no stored configuration, so the tree is
             derived from the canonical schema alone.
    @param path_text {str | None} Optional canonical path limiting the output.
    @return {Node} Display root node.
    @throws {schema.SchemaError} When the path cannot be resolved.
    @satisfies DES-118 DES-125 DES-126 DES-127
    """
    if path_text is None:
        children = tuple(_info_section(section, (section.token,)) for section in schema.SECTIONS)
        return Node(INFO_ROOT, (), children)
    path = schema.parse_path(path_text)
    if path.node.kind == schema.KIND_SECTION:
        return _info_section(path.node, path.tokens)
    return _info_leaf(path.node, path.tokens)


def _print_section(node: schema.Node, tokens: tuple[str, ...], value: Any) -> Node:
    """
    @brief Build one `--print` section node with its real children.
    @details The heading carries the exact token, the canonical path badge, and
             the English description; children keep canonical schema order.
    @param node {schema.Node} Section node to render.
    @param tokens {tuple[str, ...]} Canonical tokens of the section.
    @param value {Any} Stored value of the section mapping.
    @return {Node} Render node for the section.
    @satisfies DES-119 DES-126 DES-127
    """
    heading = f"{node.token} - [Path: {':'.join(tokens)}] {node.description}"
    mapping = value if isinstance(value, dict) else {}
    children = tuple(
        _print_child(
            child,
            tokens + (child.token,),
            mapping[child.token] if child.token in mapping else schema.default_value(child),
        )
        for child in node.children
    )
    return Node(heading, (), children)


def _print_child(node: schema.Node, tokens: tuple[str, ...], value: Any) -> Node:
    """
    @brief Build one `--print` child node, dispatching sections and parameters.
    @param node {schema.Node} Child schema node.
    @param tokens {tuple[str, ...]} Canonical tokens of the child.
    @param value {Any} Stored value of the child.
    @return {Node} Render node for the child.
    @satisfies DES-122 DES-123 DES-124
    """
    if node.kind == schema.KIND_SECTION:
        return _print_section(node, tokens, value)
    return _print_leaf(node, tokens, value)


def _print_leaf(node: schema.Node, tokens: tuple[str, ...], value: Any) -> Node:
    """
    @brief Build one `--print` parameter node with its attached detail lines.
    @details Scalar values render as JSON with a default/custom marker;
             selections attach a `Sel | Value` table; non-empty arrays attach an
             `Idx | Value` table; empty arrays attach a complete `--set` hint.
    @param node {schema.Node} Parameter schema node.
    @param tokens {tuple[str, ...]} Canonical tokens of the parameter.
    @param value {Any} Stored value of the parameter.
    @return {Node} Render node for the parameter.
    @satisfies DES-121 DES-122 DES-123 DES-124
    """
    display = ":".join(tokens)
    label = node.token if tokens and tokens[-1] == node.token else display
    if node.kind == schema.KIND_ARRAY:
        return _print_array(node, label, display, value)
    rendered = _json(value)
    details: tuple[str, ...] = ()
    if node.kind == schema.KIND_SELECTION:
        details = tuple(render_table(SELECTION_HEADERS, _selection_rows(node, value)))
    if not schema.has_default(node):
        return Node(f"{label} = {rendered}", details)
    default = schema.default_value(node)
    status = "(default)" if value == default else f"(custom | default: {_json(default)})"
    return Node(f"{label} = {rendered} {status}", details)


def _print_array(node: schema.Node, label: str, display: str, value: Any) -> Node:
    """
    @brief Build one `--print` array parameter node.
    @details Non-empty arrays expose the row target and an `Idx | Value` table
             with contiguous zero-based indices; empty arrays expose a complete,
             schema-valid `--set` hint without any table.
    @param node {schema.Node} Array schema node.
    @param label {str} Rendered parameter label.
    @param display {str} Canonical path of the array parameter.
    @param value {Any} Stored array value.
    @return {Node} Render node for the array parameter.
    @satisfies DES-121 DES-123
    """
    items = value if isinstance(value, list) else []
    if not items:
        item = _require_item(node)
        hint = _argument(item, schema.example_value(item))
        return Node(f"{label} = (empty list | add: --set {display}:+ {hint})")
    summary = f"({len(items)} items | row target: {display}:<Idx> | add: {display}:+)"

    rows = [(str(index), _json(item)) for index, item in enumerate(items)]
    return Node(f"{label} = {summary}", tuple(render_table(ARRAY_HEADERS, rows)))


def _info_section(node: schema.Node, tokens: tuple[str, ...]) -> Node:
    """
    @brief Build one `--info` section node with its real children.
    @details The section badge precedes the `Reset block` detail; branch
             metadata is emitted before the real children.
    @param node {schema.Node} Section node to document.
    @param tokens {tuple[str, ...]} Canonical tokens of the section.
    @return {Node} Render node for the section.
    @satisfies DES-125 DES-126
    """
    display = ":".join(tokens)
    details = (f"Reset block : --unset {display}",)
    children = tuple(_info_child(child, tokens + (child.token,)) for child in node.children)
    return Node(f"{node.token} - [Path: {display}] {node.description}", details, children)


def _info_child(node: schema.Node, tokens: tuple[str, ...]) -> Node:
    """
    @brief Build one `--info` child node, dispatching sections and parameters.
    @param node {schema.Node} Child schema node.
    @param tokens {tuple[str, ...]} Canonical tokens of the child.
    @return {Node} Render node for the child.
    @satisfies DES-125
    """
    if node.kind == schema.KIND_SECTION:
        return _info_section(node, tokens)
    return _info_leaf(node, tokens)


def _info_leaf(node: schema.Node, tokens: tuple[str, ...]) -> Node:
    """
    @brief Build one `--info` parameter node with attached schema details.
    @details Emits the declared default with its reset command, full command
             examples for the addressed value, and the allowed-value table for
             selections. Required values without defaults never advertise reset.
    @param node {schema.Node} Parameter schema node.
    @param tokens {tuple[str, ...]} Canonical tokens of the parameter.
    @return {Node} Render node for the parameter.
    @satisfies DES-125 DES-128 DES-129
    """
    display = ":".join(tokens)
    label = node.token if tokens and tokens[-1] == node.token else display
    heading = f"{label} - [{_type_text(node)}] {node.description}"
    details: list[str] = []
    if schema.has_default(node):
        details.append(f"Default : {_json(schema.default_value(node))} (restored via: --unset {display})")
    if node.kind == schema.KIND_ARRAY:
        item = _require_item(node)
        argument = _argument(item, schema.example_value(item))
        details.append(f"Full overwrite : --set {display} {_argument(node, schema.example_value(node))}")
        details.append(f"Add item : --set {display}:+ {argument}")
        details.append(f"Insert item : --set {display}:insert:0 {argument}")
        details.append(f"Replace item : --set {display}:0 {argument}")
        details.append(f"Delete item : --unset {display}:0")
        if schema.has_default(node):
            details.append(f"Reset array : --unset {display}")
        if item.kind == schema.KIND_SELECTION:
            details.append("Allowed Values:")
            details.extend(render_table(ALLOWED_HEADERS, _allowed_rows(item, schema.NO_DEFAULT)))
        else:
            details.append(f"Item type : {_type_text(item)}")
        return Node(heading, tuple(details))
    details.append(f"Set cmd : --set {display} {_argument(node, schema.example_value(node))}")
    if schema.has_default(node):
        details.append(f"Reset cmd : --unset {display}")
    if node.kind == schema.KIND_SELECTION:
        current = schema.default_value(node) if schema.has_default(node) else schema.NO_DEFAULT
        details.append("Allowed Values:")
        details.extend(render_table(ALLOWED_HEADERS, _allowed_rows(node, current)))
    return Node(heading, tuple(details))


def _selection_rows(node: schema.Node, current: Any) -> list[tuple[str, str]]:
    """
    @brief Build `Sel | Value` rows with exactly one active selection row.
    @details Every declared choice produces one row; a stored value outside the
             declared choices is appended so exactly one row stays active.
    @param node {schema.Node} Selection schema node.
    @param current {Any} Stored value of the selection.
    @return {list[tuple[str, str]]} `(marker, JSON value)` rows.
    @satisfies DES-124
    """
    values = list(node.choices)
    if isinstance(current, str) and current not in values:
        values.append(current)
    return [("[*]" if value == current else "[ ]", _json(value)) for value in values]


def _allowed_rows(node: schema.Node, default: Any) -> list[tuple[str, str, str]]:
    """
    @brief Build `Value | Default | Meaning` rows for one selection node.
    @details The default column reports whether a row equals the declared
             default; an array item without a default reports `no` everywhere.
    @param node {schema.Node} Selection schema node.
    @param default {Any} Declared default value or `schema.NO_DEFAULT`.
    @return {list[tuple[str, str, str]]} Allowed-value table rows.
    @satisfies DES-125
    """
    meanings = dict(node.meanings)
    return [
        (value, "yes" if default is not schema.NO_DEFAULT and value == default else "no", meanings.get(value, ""))
        for value in node.choices
    ]


def _type_text(node: schema.Node) -> str:
    """
    @brief Format the bracketed schema type and constraint text of one node.
    @param node {schema.Node} Schema node to describe.
    @return {str} `type: constraints` or just `type`.
    @satisfies DES-125
    """
    if node.constraints:
        return f"{node.type_label}: {node.constraints}"
    return node.type_label


def _argument(node: schema.Node, value: Any) -> str:
    """
    @brief Format one command-line argument as a shell-safe literal.
    @details String and selection values pass as literal text; every other type
             is JSON-encoded so arrays, objects, numbers, and booleans keep
             their schema type. Values are single-quoted only when required.
    @param node {schema.Node} Schema node typing the value.
    @param value {Any} Value to render.
    @return {str} Shell-safe argument text.
    @satisfies DES-129
    """
    if node.kind in (schema.KIND_STRING, schema.KIND_SELECTION):
        return shlex.quote(str(value))
    return shlex.quote(json.dumps(value, ensure_ascii=False))


def _json(value: Any) -> str:
    """
    @brief Encode one value as a single-line JSON literal.
    @details Newlines and control characters become visible JSON escapes so a
             value never breaks a structural output line.
    @param value {Any} Value to encode.
    @return {str} JSON text without ASCII escaping.
    @satisfies DES-122 DES-132
    """
    return json.dumps(value, ensure_ascii=False)


def _require_item(node: schema.Node) -> schema.Node:
    """
    @brief Return the declared item schema of an array node.
    @param node {schema.Node} Array schema node.
    @return {schema.Node} Declared item schema.
    @throws {schema.SchemaError} When the array declares no item schema.
    @satisfies DES-123
    """
    if node.item is None:
        raise schema.SchemaError(f"Schema array '{node.token}' declares no item type.")
    return node.item
