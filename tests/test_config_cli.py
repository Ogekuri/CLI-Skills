"""
@file test_config_cli.py
@brief Golden, structural, table, and command-behavior tests for the configuration subsystem.
@details Level 0 tests exercise the deterministic renderer in isolation. Level 1
         tests exercise schema resolution and validation. Level 2 tests exercise
         validated configuration operations and the `--print`/`--info` node
         builders. Level 3 tests exercise CLI dispatch, stream separation, exit
         codes, and failure atomicity. Every test is deterministic and isolated:
         configuration paths are redirected into a temporary directory and
         network access is never performed.
@satisfies REQ-072 REQ-073 REQ-074 REQ-075 REQ-076
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import shlex
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cli_skills import configops, configview, core, render, schema, settings


SEGMENTS = (render.CONTINUE, render.INDENT)
TABLE_START = ("┌", "├", "└", "│")


def split_line(line: str) -> tuple[list[str], str | None, str]:
    """
    @brief Split one rendered line into ancestor segments, marker, and content.
    @param line {str} One physical output line.
    @return {tuple[list[str], str | None, str]} `(segments, marker, content)`.
    """
    segments: list[str] = []
    rest = line
    while rest[:4] in SEGMENTS:
        segments.append(rest[:4])
        rest = rest[4:]
    for marker in (render.BRANCH, render.LAST):
        if rest.startswith(marker):
            return segments, marker, rest[len(marker):]
    return segments, None, rest


def parse_tree(text: str) -> dict[str, object]:
    """
    @brief Parse rendered text into a node tree of real nodes and detail lines.
    @details Raises `AssertionError` when a detail line has no owning node.
    @param text {str} Rendered tree text.
    @return {dict[str, object]} Root node mapping with `details` and `children`.
    """
    lines = text.split("\n")
    root: dict[str, object] = {"label": lines[0], "details": [], "children": [], "segments": [], "marker": None}
    stack: list[tuple[int, dict[str, object]]] = [(-1, root)]
    for line in lines[1:]:
        segments, marker, content = split_line(line)
        if marker is None:
            assert len(segments) >= 1, f"detail line without owner prefix: {line!r}"
            depth = len(segments) - 1
            owners = [node for level, node in reversed(stack) if level == depth]
            owner = owners[0] if owners else root
            details = owner["details"]
            assert isinstance(details, list)
            details.append("".join(segments) + content)
            continue
        depth = len(segments)
        parent = next(node for level, node in reversed(stack) if level == depth - 1)
        node: dict[str, object] = {
            "label": content,
            "details": [],
            "children": [],
            "segments": segments,
            "marker": marker,
        }
        children = parent["children"]
        assert isinstance(children, list)
        children.append(node)
        while stack and stack[-1][0] >= depth:
            stack.pop()
        stack.append((depth, node))
    return root


def walk_tree(node: dict[str, object], prefix: str) -> list[str]:
    """
    @brief Validate markers, ancestor prefixes, and detail prefixes recursively.
    @param node {dict[str, object]} Node whose children are validated.
    @param prefix {str} Expected ancestor prefix of the node's children.
    @return {list[str]} Heading labels in canonical order.
    """
    labels = [str(node["label"])]
    children = node["children"]
    assert isinstance(children, list)
    for index, child in enumerate(children):
        last = index == len(children) - 1
        assert child["segments"] == [prefix[start:start + 4] for start in range(0, len(prefix), 4)], child
        assert child["marker"] == (render.LAST if last else render.BRANCH), child
        detail_prefix = prefix + (render.INDENT if last else render.CONTINUE)
        details = child["details"]
        assert isinstance(details, list)
        for detail in details:
            assert detail.startswith(detail_prefix), detail
            remainder = detail[len(detail_prefix):]
            assert not remainder.startswith((render.BRANCH, render.LAST)), detail
        labels.extend(walk_tree(child, detail_prefix))
    return labels


def stripped_details(text: str) -> list[str]:
    """
    @brief Return every detail line without its owning tree prefix.
    @details Removes only the four-character ancestor and detail segments so
             table validators can inspect the raw box-drawing content.
    @param text {str} Rendered tree text.
    @return {list[str]} Detail lines without structural prefixes.
    """
    result: list[str] = []
    for detail in tree_details(text):
        while detail[:4] in SEGMENTS:
            detail = detail[4:]
        result.append(detail)
    return result


def tree_details(text: str) -> list[str]:
    """
    @brief Return every detail line of a rendered tree including its prefix.
    @param text {str} Rendered tree text.
    @return {list[str]} Detail lines with their owning prefix.
    """
    details: list[str] = []

    def collect(node: dict[str, object]) -> None:
        stored = node["details"]
        assert isinstance(stored, list)
        details.extend(stored)
        children = node["children"]
        assert isinstance(children, list)
        for child in children:
            collect(child)

    collect(parse_tree(text))
    return details


def char_columns(text: str) -> dict[str, list[int]]:
    """
    @brief Map every box-drawing character to its display column positions.
    @param text {str} Rendered table line.
    @return {dict[str, list[int]]} Display column positions per character.
    """
    positions: dict[str, list[int]] = {}
    column = 0
    for char in text:
        if char in "┌┬┐├┼┤└┴┘│─":
            positions.setdefault(char, []).append(column)
        column += render.display_width(char)
    return positions


def validate_tables(lines: list[str]) -> int:
    """
    @brief Validate every table found inside rendered detail lines.
    @details Checks rectangularity, aligned separators, and shared column
             boundaries. Returns the number of validated tables.
    @param lines {list[str]} Detail lines without owning prefixes.
    @return {int} Number of validated tables.
    """
    groups: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line[:1] in TABLE_START:
            current.append(line)
        elif current:
            groups.append(current)
            current = []
    if current:
        groups.append(current)
    for table in groups:
        top = table[0]
        bottom = table[-1]
        columns = char_columns(top)
        boundaries = columns.get("┬", [])
        total = render.display_width(top)
        widths = {render.display_width(line) for line in table}
        assert widths == {total}, table
        assert top[0] == "┌" and top[-1] == "┐", table
        assert bottom[0] == "└" and bottom[-1] == "┘", table
        assert columns.get("┌") == [0] and columns.get("┐") == [total - 1], table
        assert char_columns(bottom).get("┴") == boundaries, table
        for line in table[1:-1]:
            if line[0] == "├":
                assert char_columns(line).get("┼") == boundaries, table
            else:
                assert line[0] == "│", table
                assert char_columns(line).get("│") == sorted([0, total - 1, *boundaries]), table
    return len(groups)


class RenderTests(unittest.TestCase):
    """Level 0: deterministic renderer in isolation."""

    def test_single_root_child_has_last_marker(self):
        """
        @brief Verify one root child uses the last-sibling marker.
        @expected_output Exact two-line tree with a `└── ` root child.
        @satisfies REQ-072 DES-118
        """
        tree = render.Node("Root", (), (render.Node("only"),))
        self.assertEqual(render.render_tree(tree), "Root\n└── only")

    def test_two_root_siblings(self):
        """
        @brief Verify two root siblings use branch then last markers.
        @expected_output Exact three-line tree with `├── ` then `└── `.
        @satisfies REQ-072 DES-118
        """
        tree = render.Node("Root", (), (render.Node("first"), render.Node("second")))
        self.assertEqual(render.render_tree(tree), "Root\n├── first\n└── second")

    def test_nested_first_middle_last_siblings(self):
        """
        @brief Verify nested first, middle, and last siblings.
        @details The first branch keeps a `│   ` continuation for its last
                 child, the middle branch does not, and the last branch indents.
        @expected_output Exact nested tree preserving ancestor continuations.
        @satisfies REQ-073 DES-118 DES-119
        """
        tree = render.Node(
            "Root",
            (),
            (
                render.Node("alpha", (), (render.Node("alpha-last"),)),
                render.Node("beta", (), (render.Node("beta-last"),)),
                render.Node("gamma", (), (render.Node("gamma-last"),)),
            ),
        )
        self.assertEqual(
            render.render_tree(tree),
            "Root\n"
            "├── alpha\n"
            "│   └── alpha-last\n"
            "├── beta\n"
            "│   └── beta-last\n"
            "└── gamma\n"
            "    └── gamma-last",
        )

    def test_non_last_parameter_with_details(self):
        """
        @brief Verify a non-last node with several details keeps one continuation.
        @expected_output Every detail line prefixed with `│   `.
        @satisfies REQ-073 DES-119
        """
        tree = render.Node(
            "Root",
            (),
            (render.Node("first", ("one", "two")), render.Node("second")),
        )
        self.assertEqual(
            render.render_tree(tree),
            "Root\n├── first\n│   one\n│   two\n└── second",
        )

    def test_last_parameter_with_details(self):
        """
        @brief Verify a last node with several details indents every detail line.
        @expected_output Every detail line prefixed with four spaces.
        @satisfies REQ-073 DES-119
        """
        tree = render.Node("Root", (), (render.Node("only", ("one", "two")),))
        self.assertEqual(render.render_tree(tree), "Root\n└── only\n    one\n    two")

    def test_branch_with_details_and_children(self):
        """
        @brief Verify a branch keeps detail prefixes independent of child depth.
        @expected_output Branch details use `│   ` and children start one level down.
        @satisfies REQ-073 DES-119
        """
        tree = render.Node(
            "Root",
            (),
            (
                render.Node("branch", ("meta",), (render.Node("leaf", ("detail",)),)),
                render.Node("other"),
            ),
        )
        self.assertEqual(
            render.render_tree(tree),
            "Root\n"
            "├── branch\n"
            "│   meta\n"
            "│   └── leaf\n"
            "│       detail\n"
            "└── other",
        )

    def test_root_details_use_four_space_indent(self):
        """
        @brief Verify display-root details never gain a synthetic tree level.
        @expected_output Root detail indented by exactly four spaces.
        @satisfies REQ-073 DES-127
        """
        tree = render.Node("Root", ("attached",), (render.Node("child"),))
        self.assertEqual(render.render_tree(tree), "Root\n    attached\n└── child")

    def test_detail_lines_reject_control_characters(self):
        """
        @brief Verify details must stay single physical lines.
        @expected_exception ValueError
        @satisfies REQ-074 DES-119
        """
        for detail in ("broken\nline", "tab\there", "carriage\rreturn"):
            with self.subTest(detail=detail), self.assertRaises(ValueError):
                render.render_tree(render.Node("Root", (detail,)))

    def test_table_rectangular_with_wide_characters(self):
        """
        @brief Verify the table formatter aligns borders with wide characters.
        @details Column widths use display width, so a wide-character cell does
                 not shift any border character.
        @expected_output Equal display widths and aligned separators.
        @satisfies REQ-074 DES-120
        """
        table = render.render_table(("Key", "値"), (("a", "日本語"), ("b", "x")))
        self.assertEqual(validate_tables(table), 1)
        self.assertEqual(render.display_width("日本語"), 6)

    def test_table_rejects_ragged_rows(self):
        """
        @brief Verify a row with the wrong cell count is rejected.
        @expected_exception ValueError
        @satisfies REQ-074 DES-120
        """
        with self.assertRaises(ValueError):
            render.render_table(("A", "B"), (("only-one",),))

    def test_display_width_ignores_combining_marks(self):
        """
        @brief Verify combining marks add no display width.
        @expected_output Width 1 for `e` plus a combining accent.
        @satisfies REQ-074 DES-120
        """
        self.assertEqual(render.display_width("e\u0301"), 1)


class SchemaTests(unittest.TestCase):
    """Level 1: canonical schema resolution and typed validation."""

    def test_default_configuration_matches_schema(self):
        """
        @brief Verify the on-disk default equals the schema defaults.
        @expected_output `{"enabled": []}`.
        @satisfies REQ-073 DES-108 DES-111
        """
        self.assertEqual(schema.default_config(), {"enabled": []})

    def test_parse_path_accepts_canonical_paths(self):
        """
        @brief Verify every documented canonical path form resolves.
        @details Section, key, index, insert, append, and plus forms all resolve
                 to the declared schema node.
        @expected_output Resolved display tokens equal the input path text.
        @satisfies REQ-076 DES-107 DES-109 DES-110
        """
        cases = {
            "Global": schema.GLOBAL,
            "Global:enabled": schema.ENABLED,
            "Global:enabled:0": schema.ENABLED_ITEM,
            "Global:enabled:12": schema.ENABLED_ITEM,
            "Global:enabled:append": schema.ENABLED_ITEM,
            "Global:enabled:+": schema.ENABLED_ITEM,
            "Global:enabled:insert:0": schema.ENABLED_ITEM,
        }
        for text, expected in cases.items():
            with self.subTest(path=text):
                parsed = schema.parse_path(text)
                self.assertEqual(parsed.node, expected)
                self.assertEqual(parsed.display, text)

    def test_parse_path_rejects_invalid_paths(self):
        """
        @brief Verify unknown, case-mismatched, and malformed paths are rejected.
        @expected_exception SchemaError
        @satisfies REQ-073 DES-109 DES-134
        """
        for text in ("", "global", "Global:unknown", "Global:enabled:-1", "Global:enabled:x", "Global:enabled:insert", "Global:enabled:0:field", "Global:enabled:append:x"):
            with self.subTest(path=text), self.assertRaises(schema.SchemaError):
                schema.parse_path(text)

    def test_validate_config_rejects_invalid_payloads(self):
        """
        @brief Verify strict whole-configuration validation.
        @expected_exception SchemaError
        @satisfies REQ-073 DES-112
        """
        for payload in ([], {"enabled": "claude"}, {"enabled": ["bogus"]}, {"enabled": ["pi", "pi"]}, {"enabled": [], "extra": 1}):
            with self.subTest(payload=payload), self.assertRaises(schema.SchemaError):
                schema.validate_config(payload)

    def test_validate_config_fills_declared_defaults(self):
        """
        @brief Verify a missing key is filled from the schema default.
        @expected_output `{"enabled": []}`.
        @satisfies REQ-073 DES-112
        """
        self.assertEqual(schema.validate_config({}), {"enabled": []})

    def test_coerce_value_parses_types(self):
        """
        @brief Verify literal string parsing and strict JSON array parsing.
        @details Selection arguments stay literal text while array arguments
                 require JSON, so numbers and booleans never become strings.
        @expected_output Parsed values match the schema types.
        @satisfies REQ-075 DES-112 DES-129
        """
        self.assertEqual(schema.coerce_value(schema.ENABLED_ITEM, "claude", "Global:enabled:+"), "claude")
        self.assertEqual(schema.coerce_value(schema.ENABLED, '["claude"]', "Global:enabled"), ["claude"])
        for text in ("claude", '["bogus"]', "[]"):
            with self.subTest(text=text):
                if text == "[]":
                    self.assertEqual(schema.coerce_value(schema.ENABLED, text, "Global:enabled"), [])
                    continue
                with self.assertRaises(schema.SchemaError):
                    schema.coerce_value(schema.ENABLED, text, "Global:enabled")


class ConfigOperationsTests(unittest.TestCase):
    """Level 2: validated operations and atomic persistence."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / ".config" / "cli-skills" / "config.json"
        patcher = patch.object(settings, "config_path", side_effect=lambda home=None: self.path)
        patcher.start()
        self.addCleanup(patcher.stop)

    def read(self) -> dict[str, object]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def test_bootstrap_creates_defaults_and_preserves_existing(self):
        """
        @brief Verify lazy initialization creates defaults once.
        @expected_output Default file created, then existing content preserved.
        @satisfies REQ-075 DES-111
        """
        configops.ensure_initialized()
        self.assertEqual(self.read(), {"enabled": []})
        self.path.write_text('{"enabled": ["pi"]}', encoding="utf-8")
        configops.ensure_initialized()
        self.assertEqual(self.read(), {"enabled": ["pi"]})

    def test_array_operations_round_trip(self):
        """
        @brief Verify append, insert, replace, delete, and reset semantics.
        @details Indices stay contiguous and zero-based after every mutation.
        @expected_output Each step yields the documented array state.
        @satisfies REQ-075 DES-110 DES-135
        """
        configops.set_path("Global:enabled:+", "claude")
        configops.set_path("Global:enabled:append", "pi")
        self.assertEqual(self.read(), {"enabled": ["claude", "pi"]})
        configops.set_path("Global:enabled:insert:0", "codex")
        self.assertEqual(self.read(), {"enabled": ["codex", "claude", "pi"]})
        configops.set_path("Global:enabled:1", "copilot")
        self.assertEqual(self.read(), {"enabled": ["codex", "copilot", "pi"]})
        configops.unset_path("Global:enabled:0")
        self.assertEqual(self.read(), {"enabled": ["copilot", "pi"]})
        configops.unset_path("Global:enabled")
        self.assertEqual(self.read(), {"enabled": []})
        configops.set_path("Global", '{"enabled": ["pi"]}')
        self.assertEqual(self.read(), {"enabled": ["pi"]})
        configops.unset_path("Global")
        self.assertEqual(self.read(), {"enabled": []})

    def test_get_value_returns_addressed_json(self):
        """
        @brief Verify `--get` values for section, array, and item paths.
        @expected_output Nested mapping, list, and scalar values.
        @satisfies REQ-075 DES-115
        """
        configops.set_path("Global:enabled:+", "pi")
        config = configops.read_config()
        self.assertEqual(configops.get_value(config, schema.parse_path("Global")), {"enabled": ["pi"]})
        self.assertEqual(configops.get_value(config, schema.parse_path("Global:enabled")), ["pi"])
        self.assertEqual(configops.get_value(config, schema.parse_path("Global:enabled:0")), "pi")
        with self.assertRaises(configops.ConfigError):
            configops.get_value(config, schema.parse_path("Global:enabled:append"))

    def test_out_of_range_index_preserves_file(self):
        """
        @brief Verify index bounds diagnostics and failure atomicity.
        @details The diagnostic names the path, the rejected index, the valid
                 range, and the append option; the file stays unchanged.
        @expected_exception ConfigError
        @satisfies REQ-075 DES-114 DES-134
        """
        configops.set_path("Global:enabled:+", "pi")
        before = self.path.read_bytes()
        with self.assertRaises(configops.ConfigError) as caught:
            configops.set_path("Global:enabled:5", "pi")
        message = str(caught.exception)
        self.assertIn("Global:enabled:5", message)
        self.assertIn("0..0", message)
        self.assertIn(":append", message)
        self.assertEqual(self.path.read_bytes(), before)
        with self.assertRaises(configops.ConfigError) as insert:
            configops.set_path("Global:enabled:insert:4", "pi")
        self.assertIn("valid insert range is 0..1", str(insert.exception))
        self.assertEqual(self.path.read_bytes(), before)

    def test_empty_array_index_diagnostic_mentions_append(self):
        """
        @brief Verify an index error on an empty array suggests the append form.
        @expected_exception ConfigError
        @satisfies REQ-075 DES-134
        """
        configops.ensure_initialized()
        with self.assertRaises(configops.ConfigError) as caught:
            configops.unset_path("Global:enabled:0")
        self.assertIn("the array is empty", str(caught.exception))
        self.assertIn("--set Global:enabled:+ <value>", str(caught.exception))

    def test_invalid_values_preserve_file(self):
        """
        @brief Verify schema-invalid writes never mutate the file.
        @expected_exception ConfigError
        @satisfies REQ-075 DES-112 DES-114
        """
        configops.set_path("Global:enabled:+", "pi")
        before = self.path.read_bytes()
        for path_text, value in (
            ("Global:enabled:+", "bogus"),
            ("Global:enabled", "claude"),
            ("Global:enabled", '["pi","pi"]'),
            ("Global", '{"unknown": []}'),
            ("Global", "not-json"),
        ):
            with self.subTest(path=path_text, value=value), self.assertRaises(configops.ConfigError):
                configops.set_path(path_text, value)
            self.assertEqual(self.path.read_bytes(), before)

    def test_unknown_key_preserves_file(self):
        """
        @brief Verify unknown keys are rejected without mutation.
        @expected_exception ConfigError
        @satisfies REQ-075 DES-109 DES-114
        """
        configops.ensure_initialized()
        before = self.path.read_bytes()
        with self.assertRaises(configops.ConfigError):
            configops.set_path("Global:missing", "x")
        self.assertEqual(self.path.read_bytes(), before)

    def test_malformed_stored_configuration_rejected(self):
        """
        @brief Verify a malformed stored configuration blocks mutation.
        @expected_exception ConfigError
        @satisfies REQ-075 DES-112 DES-114
        """
        self.path.parent.mkdir(parents=True)
        self.path.write_text("{not json", encoding="utf-8")
        before = self.path.read_bytes()
        with self.assertRaises(configops.ConfigError):
            configops.set_path("Global:enabled:+", "pi")
        self.assertEqual(self.path.read_bytes(), before)

    def test_file_mode_is_preserved(self):
        """
        @brief Verify atomic replacement preserves the existing file mode.
        @expected_output Mode stays `0o600` after a write.
        @satisfies REQ-075 DES-113
        """
        configops.ensure_initialized()
        os.chmod(self.path, 0o600)
        configops.set_path("Global:enabled:+", "pi")
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)

    def test_failed_replace_preserves_original_and_cleans_temp(self):
        """
        @brief Verify an atomic-write failure leaves the original file intact.
        @expected_exception ConfigError
        @satisfies REQ-075 DES-113 DES-114
        """
        configops.set_path("Global:enabled:+", "pi")
        before = self.path.read_bytes()
        with patch.object(settings.os, "replace", side_effect=OSError("disk failure")):
            with self.assertRaises(configops.ConfigError):
                configops.set_path("Global:enabled:+", "claude")
        self.assertEqual(self.path.read_bytes(), before)
        leftovers = [entry.name for entry in self.path.parent.iterdir() if entry.name != "config.json"]
        self.assertEqual(leftovers, [])

    def test_print_raw_returns_stored_bytes(self):
        """
        @brief Verify raw reads bypass any rebuilding or reformatting.
        @expected_output Byte-identical content including compact formatting.
        @satisfies REQ-075 DES-116
        """
        self.path.parent.mkdir(parents=True)
        payload = b'{"enabled":["pi"]}'
        self.path.write_bytes(payload)
        self.assertEqual(configops.read_raw(), payload)


class ConfigViewTests(unittest.TestCase):
    """Level 2: `--print` and `--info` node builders and golden output."""

    def test_full_print_empty_configuration(self):
        """
        @brief Verify the complete `--print` output for an empty configuration.
        @expected_output Exact tree with a schema-valid empty-list hint.
        @satisfies REQ-072 REQ-073 DES-121 DES-122
        """
        self.assertEqual(
            configview.render_print({"enabled": []}),
            "Application_Configuration - Current configuration\n"
            "└── Global - [Path: Global] Global user configuration file\n"
            "    └── enabled = (empty list | add: --set Global:enabled:+ antigravity)",
        )

    def test_full_print_with_values(self):
        """
        @brief Verify the complete `--print` output with array rows.
        @expected_output Exact tree with an attached `Idx | Value` table.
        @satisfies REQ-072 REQ-073 DES-123
        """
        self.assertEqual(
            configview.render_print({"enabled": ["claude", "pi"]}),
            "Application_Configuration - Current configuration\n"
            "└── Global - [Path: Global] Global user configuration file\n"
            "    └── enabled = (2 items | row target: Global:enabled:<Idx> | add: Global:enabled:+)\n"
            "        ┌─────┬──────────┐\n"
            "        │ Idx │ Value    │\n"
            "        ├─────┼──────────┤\n"
            '        │ 0   │ "claude" │\n'
            '        │ 1   │ "pi"     │\n'
            "        └─────┴──────────┘",
        )

    def test_full_info(self):
        """
        @brief Verify the complete `--info` output.
        @expected_output Exact schema tree with commands and allowed values.
        @satisfies REQ-072 REQ-073 REQ-074 DES-125 DES-126
        """
        self.assertEqual(
            configview.render_info(),
            "Application_Configuration - Configuration schema reference\n"
            "└── Global - [Path: Global] Global user configuration file\n"
            "    Reset block : --unset Global\n"
            "    └── enabled - [Array[Selection]: unique supported CLI names] Enabled CLI targets for skill installation\n"
            "        Default : [] (restored via: --unset Global:enabled)\n"
            "        Full overwrite : --set Global:enabled '[\"antigravity\"]'\n"
            "        Add item : --set Global:enabled:+ antigravity\n"
            "        Insert item : --set Global:enabled:insert:0 antigravity\n"
            "        Replace item : --set Global:enabled:0 antigravity\n"
            "        Delete item : --unset Global:enabled:0\n"
            "        Reset array : --unset Global:enabled\n"
            "        Allowed Values:\n"
            "        ┌─────────────┬─────────┬──────────────────────────┐\n"
            "        │ Value       │ Default │ Meaning                  │\n"
            "        ├─────────────┼─────────┼──────────────────────────┤\n"
            "        │ antigravity │ no      │ Google Antigravity       │\n"
            "        │ claude      │ no      │ Claude Code CLI          │\n"
            "        │ codex       │ no      │ OpenAI Codex CLI         │\n"
            "        │ copilot     │ no      │ GitHub Copilot CLI       │\n"
            "        │ openclaw    │ no      │ OpenClaw agent workspace │\n"
            "        │ opencode    │ no      │ OpenCode CLI             │\n"
            "        │ pi          │ no      │ Pi coding agent          │\n"
            "        └─────────────┴─────────┴──────────────────────────┘",
        )

    def test_print_subtree_is_unconnected_root(self):
        """
        @brief Verify a requested subtree starts without fake ancestors.
        @expected_output `enabled` as the marker-free root with four-space details.
        @satisfies REQ-072 REQ-073 DES-127
        """
        self.assertEqual(
            configview.render_print({"enabled": ["claude", "pi"]}, "Global:enabled"),
            "enabled = (2 items | row target: Global:enabled:<Idx> | add: Global:enabled:+)\n"
            "    ┌─────┬──────────┐\n"
            "    │ Idx │ Value    │\n"
            "    ├─────┼──────────┤\n"
            '    │ 0   │ "claude" │\n'
            '    │ 1   │ "pi"     │\n'
            "    └─────┴──────────┘",
        )

    def test_info_subtree_is_unconnected_root(self):
        """
        @brief Verify a requested schema subtree starts without fake ancestors.
        @expected_output `enabled` schema documentation as the marker-free root.
        @satisfies REQ-073 DES-127
        """
        lines = configview.render_info("Global:enabled").split("\n")
        self.assertTrue(lines[0].startswith("enabled - [Array[Selection]: "))
        self.assertEqual(lines[1], "    Default : [] (restored via: --unset Global:enabled)")
        self.assertEqual(validate_tables(stripped_details(configview.render_info("Global:enabled"))), 1)

    def test_print_indexed_parameter_selection_table(self):
        """
        @brief Verify an indexed parameter renders exactly one active selection row.
        @expected_output A `Sel | Value` table with one `[*]` row.
        @satisfies REQ-072 REQ-073 DES-124
        """
        text = configview.render_print({"enabled": ["claude"]}, "Global:enabled:0")
        lines = text.split("\n")
        self.assertEqual(lines[0], 'Global:enabled:0 = "claude"')
        active = [line for line in lines if "[*]" in line]
        self.assertEqual(len(active), 1)
        self.assertIn('"claude"', active[0])
        self.assertEqual(validate_tables(stripped_details(text)), 1)

    def test_structural_validator_accepts_real_commands(self):
        """
        @brief Verify real output topology through the structural validator.
        @details Every marker matches sibling order, every detail prefix matches
                 its owner, and every section badge resolves to its canonical path.
        @expected_output Validated topology for print and info output.
        @satisfies REQ-073 DES-118 DES-119 DES-126 DES-127
        """
        documents = (
            configview.render_print({"enabled": []}),
            configview.render_print({"enabled": ["claude", "pi"]}),
            configview.render_print({"enabled": ["claude"]}, "Global:enabled"),
            configview.render_print({"enabled": ["claude"]}, "Global:enabled:0"),
            configview.render_info(),
            configview.render_info("Global:enabled"),
        )
        for document in documents:
            with self.subTest(document=document.split("\n")[0]):
                root = parse_tree(document)
                self.assertFalse(str(root["label"]).startswith((render.BRANCH, render.LAST)))
                labels = walk_tree(root, "")
                for label in labels:
                    if "[Path: " not in label:
                        continue
                    path = label.split("[Path: ", 1)[1].split("]", 1)[0]
                    self.assertEqual(schema.parse_path(path).display, path)

    def test_table_validator_accepts_real_commands(self):
        """
        @brief Verify every emitted table is rectangular and correctly anchored.
        @expected_output At least two validated tables with aligned borders.
        @satisfies REQ-074 DES-120
        """
        tables: list[str] = []
        for document in (configview.render_print({"enabled": ["claude", "pi"]}), configview.render_info()):
            tables.extend(stripped_details(document))
        self.assertGreaterEqual(validate_tables(tables), 2)

    def test_metadata_never_uses_structural_markers(self):
        """
        @brief Verify detail lines never carry a tree marker.
        @expected_output No detail line starts with `├── ` or `└── `.
        @satisfies REQ-073 DES-119
        """
        for document in (configview.render_print({"enabled": ["claude"]}), configview.render_info()):
            for detail in tree_details(document):
                while detail[:4] in SEGMENTS:
                    detail = detail[4:]
                self.assertFalse(detail.startswith((render.BRANCH, render.LAST)))

    def test_global_and_last_leaf_detail_prefixes(self):
        """
        @brief Verify the observed regression pattern for detail prefixes.
        @details `Global` is a last root child so its metadata uses four spaces;
                 its last leaf metadata uses eight spaces.
        @expected_output Section detail prefixed `    ` and leaf detail `        `.
        @satisfies REQ-073 DES-119
        """
        lines = configview.render_info().split("\n")
        self.assertEqual(lines[2], "    Reset block : --unset Global")
        leaf_default = next(line for line in lines if "Default : []" in line)
        self.assertTrue(leaf_default.startswith("        Default : "))

    def test_published_commands_are_shell_parseable_and_valid(self):
        """
        @brief Verify every published command parses and executes against the schema.
        @details Each example is shell-split, its path must resolve, and applying
                 it to a schema-valid configuration must succeed.
        @expected_output All examples execute without a schema error.
        @satisfies REQ-076 DES-129
        """
        documents = (
            configview.render_info(),
            configview.render_info("Global:enabled:0"),
            configview.render_print({"enabled": []}),
        )
        commands: list[str] = []
        for document in documents:
            for line in document.split("\n"):
                for marker in ("--set ", "--unset "):
                    position = line.find(marker)
                    if position >= 0:
                        command = line[position:].strip()
                        if command.endswith(")"):
                            command = command[:-1].strip()
                        commands.append(command)
                        break
        self.assertGreaterEqual(len(commands), 7)
        ready = configops.apply_set(schema.default_config(), schema.parse_path("Global:enabled:+"), "claude")
        for command in commands:
            with self.subTest(command=command):
                argv = shlex.split(command)
                self.assertIn(argv[0], ("--set", "--unset"))
                path = schema.parse_path(argv[1])
                if argv[0] == "--set":
                    self.assertEqual(len(argv), 3)
                    configops.apply_set(ready, path, argv[2])
                else:
                    self.assertEqual(len(argv), 2)
                    configops.apply_unset(ready, path)


class ConfigurationCliTests(unittest.TestCase):
    """Level 3: CLI dispatch, streams, exit codes, and failure atomicity."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / ".config" / "cli-skills" / "config.json"
        patcher = patch.object(settings, "config_path", side_effect=lambda home=None: self.path)
        patcher.start()
        self.addCleanup(patcher.stop)
        check = patch.object(core, "check_version")
        check.start()
        self.addCleanup(check.stop)

    def run_cli(self, *args: str) -> tuple[int, str, str]:
        """
        @brief Run `core.main` with captured stdout and stderr.
        @param args {tuple[str, ...]} CLI arguments.
        @return {tuple[int, str, str]} Exit code, stdout text, and stderr text.
        """
        out = io.StringIO()
        err = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = core.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_get_emits_json_only(self):
        """
        @brief Verify `--get` output is bare JSON on stdout.
        @expected_output `[]` then `"claude"` with empty stderr and exit 0.
        @satisfies REQ-075 DES-115 DES-117
        """
        code, out, err = self.run_cli("--get", "Global:enabled")
        self.assertEqual((code, out, err), (0, "[]\n", ""))
        self.run_cli("--set", "Global:enabled:+", "claude")
        code, out, err = self.run_cli("--get", "Global:enabled:0")
        self.assertEqual((code, out, err), (0, '"claude"\n', ""))
        self.assertEqual(json.loads(out), "claude")

    def test_set_and_unset_confirmations(self):
        """
        @brief Verify mutation confirmations go to stdout with exit 0.
        @expected_output `Set`/`Unset` confirmations and no stderr output.
        @satisfies REQ-075 DES-117 DES-133
        """
        self.assertEqual(self.run_cli("--set", "Global:enabled:+", "pi"), (0, "Set Global:enabled:+.\n", ""))
        self.assertEqual(self.run_cli("--unset", "Global:enabled:0"), (0, "Unset Global:enabled:0.\n", ""))
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8")), {"enabled": []})

    def test_print_and_info_exit_zero(self):
        """
        @brief Verify display commands bootstrap the file and exit 0.
        @expected_output Created default file plus tree output on stdout.
        @satisfies REQ-075 DES-111 DES-117
        """
        code, out, err = self.run_cli("--print")
        self.assertEqual(code, 0)
        self.assertIn("Application_Configuration - Current configuration", out)
        self.assertEqual(err, "")
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8")), {"enabled": []})
        code, out, err = self.run_cli("--info")
        self.assertEqual(code, 0)
        self.assertIn("Application_Configuration - Configuration schema reference", out)
        self.assertEqual(err, "")

    def test_print_raw_is_byte_identical(self):
        """
        @brief Verify `--print-raw` reproduces the stored bytes exactly.
        @expected_output Compact JSON without a trailing newline.
        @satisfies REQ-075 DES-116
        """
        self.path.parent.mkdir(parents=True)
        self.path.write_bytes(b'{"enabled":["pi"]}')
        code, out, err = self.run_cli("--print-raw")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out, '{"enabled":["pi"]}')

    def test_invalid_path_reports_error_without_mutation(self):
        """
        @brief Verify invalid paths fail on stderr with exit 1 and no write.
        @expected_output Error diagnostic on stderr, empty stdout, file unchanged.
        @satisfies REQ-075 DES-109 DES-114 DES-117
        """
        self.run_cli("--set", "Global:enabled:+", "pi")
        before = self.path.read_bytes()
        for args in (
            ("--get", "Global:enabled:append"),
            ("--get", "Global:unknown"),
            ("--set", "Global:enabled:7", "pi"),
            ("--set", "Global:enabled:+", "bogus"),
            ("--unset", "Global:enabled:9"),
            ("--print", "global"),
            ("--info", "Global:enabled:0:field"),
        ):
            with self.subTest(args=args):
                code, out, err = self.run_cli(*args)
                self.assertEqual(code, 1)
                self.assertEqual(out, "")
                self.assertTrue(err.startswith("Error: "))
                self.assertEqual(self.path.read_bytes(), before)

    def test_usage_errors_exit_one(self):
        """
        @brief Verify arity errors for configuration commands exit 1.
        @expected_output Usage diagnostics on stderr only.
        @satisfies REQ-075 DES-117
        """
        for args in (("--set", "Global:enabled"), ("--get",), ("--unset",), ("--print-raw", "extra")):
            with self.subTest(args=args):
                code, out, err = self.run_cli(*args)
                self.assertEqual(code, 1)
                self.assertEqual(out, "")
                self.assertIn("Usage:", err)

    def test_help_lists_configuration_commands(self):
        """
        @brief Verify the full help template documents every configuration command.
        @expected_output All six command names present in the help template.
        @satisfies REQ-075 DES-130
        """
        self.assertIn("Configuration Commands:", core.HELP)
        for command in core.CONFIG_COMMANDS:
            with self.subTest(command=command):
                self.assertIn(command, core.HELP)

    def test_command_specific_help(self):
        """
        @brief Verify `<command> --help` prints one English description line.
        @expected_output Exit 0 with the command description and no usage error.
        @satisfies REQ-075 DES-130 DES-133
        """
        for command in core.CONFIG_COMMANDS:
            with self.subTest(command=command):
                code, out, err = self.run_cli(command, "--help")
                self.assertEqual(code, 0)
                self.assertTrue(out.startswith(f"{command} - "))
                self.assertEqual(err, "")


if __name__ == "__main__":
    unittest.main()
