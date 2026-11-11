"""Release clean script artifact contract conformance tests.

@file test_clean_script.py
@brief Verify `scripts/clean.sh` removal patterns, scope, ordering, and argument parser.
@details HDT Level 0 static conformance suite. The UUTs are the bash functions
         `parse_arguments`, `remove_release_outputs`, `remove_build_outputs`,
         and `main` of `scripts/clean.sh`, located by their function headers.
         The suite asserts the argument contract, the generated-output patterns,
         the build/ and egg-info scope, and the symbolic-link refusal ordering.
         External dependency: one deterministic read of the tracked
         `scripts/clean.sh`; no subprocess, network, clock, randomness, or
         filesystem writes are involved.
@satisfies PRJ-020 DES-176 DES-177 DES-178 DES-179 DES-181 DES-182 DES-185
"""

import unittest
from pathlib import Path

## @brief Path of the release clean script under test.
## @details Resolved relative to this test module so the suite stays
##          independent of the process working directory.
CLEAN_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "clean.sh"


class CleanScriptContractTests(unittest.TestCase):
    """Level 0: artifact removal and argument contract of the clean script."""

    def setUp(self):
        """
        @brief Load the tracked clean script text for one test.
        @details Reads `scripts/clean.sh` once per test and fails immediately when
                 the script is missing. No subprocess or filesystem write is performed.
        @return {None}
        """
        if not CLEAN_SCRIPT_PATH.is_file():
            self.fail(f"Missing clean script: {CLEAN_SCRIPT_PATH}")
        self.script_text = CLEAN_SCRIPT_PATH.read_text(encoding="utf-8")

    def _function_body(self, name):
        """
        @brief Extract the body of one top-level bash function.
        @details Collects the lines after `<name>() {` up to the first line equal
                 to `}`. Fails when the function header or its closing brace is absent.
        @param name {str} Bash function name without parentheses.
        @return {str} Newline-joined function body lines.
        """
        lines = self.script_text.splitlines()
        header = f"{name}() {{"
        if header not in lines:
            self.fail(f"missing function header: {header}")
        start = lines.index(header) + 1
        for end in range(start, len(lines)):
            if lines[end] == "}":
                return "\n".join(lines[start:end])
        self.fail(f"missing closing brace of function: {name}")

    def test_parse_arguments_declares_single_output_dir_option(self):
        """
        @brief Check the argument parser declares exactly one `--output-dir` branch.
        @details Arranges the `parse_arguments` body, then asserts exactly one case
                 label `--output-dir)` exists and a guard rejects a missing value
                 through the `$# < 2` condition.
        @return {None}
        @expected_output No assertion failure when the parser accepts
                         `--output-dir <path>` and rejects a missing value.
        @satisfies DES-177 DES-182
        """
        body = self._function_body("parse_arguments")
        labels = [line.strip() for line in body.splitlines() if line.strip() == "--output-dir)"]
        self.assertEqual(
            len(labels),
            1,
            f"expected exactly one --output-dir case label, found {len(labels)}",
        )
        self.assertIn("$# < 2", body)

    def test_parse_arguments_rejects_relative_output_dir(self):
        """
        @brief Check a relative `--output-dir` path leads to the usage diagnostic.
        @details Arranges the `parse_arguments` body, then asserts the absolute-path
                 guard `[[ $output != /* ]]` exists and that the first `fi` after the
                 guard follows a `usage` call.
        @return {None}
        @expected_output No assertion failure when every non-absolute path
                         terminates through `usage` with exit status 2.
        @satisfies DES-177 DES-182
        """
        body = self._function_body("parse_arguments")
        self.assertIn("[[ $output != /* ]]", body)
        guarded = body.split("[[ $output != /* ]]", 1)[1].split("fi", 1)[0]
        self.assertIn("usage", guarded)

    def test_release_output_patterns_match_generated_outputs(self):
        """
        @brief Check the release output removal covers every generated-output pattern.
        @details Arranges the `remove_release_outputs` body, then asserts the sdist,
                 wheel, staging, and checksum patterns are all present.
        @return {None}
        @expected_output No assertion failure when every DES-139 and DES-142 pattern
                         is removed by `remove_release_outputs`.
        @satisfies DES-178
        """
        body = self._function_body("remove_release_outputs")
        for pattern in (
            '$DIST_PREFIX"-*.tar.gz',
            '$DIST_PREFIX"-*.whl',
            '.cli-skills-build.*',
            'SHA256SUMS',
        ):
            self.assertIn(pattern, body, f"missing removal pattern: {pattern}")

    def test_build_scope_removes_build_entry_and_src_egg_info(self):
        """
        @brief Check the build outputs removal targets build/ and src egg-info only.
        @details Arranges the `remove_build_outputs` body, then asserts the build/
                 entry removal, the `src` search root, the `*.egg-info` name pattern,
                 and the absence of a depth limit.
        @return {None}
        @expected_output No assertion failure when build/ and every *.egg-info
                         directory under src/ are removed without a depth limit.
        @satisfies DES-179
        """
        body = self._function_body("remove_build_outputs")
        self.assertIn('remove_entry "$PROJECT_ROOT/build"', body)
        self.assertIn('"$PROJECT_ROOT/src"', body)
        self.assertIn("-name '*.egg-info'", body)
        self.assertNotIn("-maxdepth", body)

    def test_symbolic_link_refusal_precedes_every_removal(self):
        """
        @brief Check the release output state check runs before any removal in `main`.
        @details Arranges the `main` body, then asserts `check_output_directory` is
                 invoked before both `remove_release_outputs` and `remove_build_outputs`.
        @return {None}
        @expected_output No assertion failure when the refusal precedes removal.
        @satisfies DES-181
        """
        body = self._function_body("main")
        check_index = body.index("check_output_directory")
        self.assertLess(check_index, body.index("remove_release_outputs"))
        self.assertLess(check_index, body.index("remove_build_outputs"))

    def test_default_release_output_directory_is_dist(self):
        """
        @brief Check the default release output directory remains `dist/`.
        @details Asserts the exact default assignment `DIST_DIRECTORY=$PROJECT_ROOT/dist`
                 appears exactly once in the script text.
        @return {None}
        @expected_output No assertion failure when the default is `$PROJECT_ROOT/dist`.
        @satisfies DES-177
        """
        assignments = [
            line
            for line in self.script_text.splitlines()
            if line.strip() == "DIST_DIRECTORY=$PROJECT_ROOT/dist"
        ]
        self.assertEqual(len(assignments), 1)


if __name__ == "__main__":
    unittest.main()
