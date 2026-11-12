"""Pre-release check script dist/ independence conformance tests.

@file test_prerelease_check_script.py
@brief Verify `scripts/pre-release-check.sh` builds into a temporary directory
       outside the repository tree and performs no `dist/` operation.
@details HDT Level 0 static conformance suite. UUTs are the `main` function, the
         executable code lines, and the temporary-directory contract of
         `scripts/pre-release-check.sh`. The suite asserts that the release
         output directory is created through `mktemp -d`, that a containment
         guard rejects a temporary path inside the repository tree, that the
         single `scripts/build.sh` invocation receives that temporary directory,
         and that no executable code line names a `dist/` entry.
         External dependency: deterministic reads of the tracked
         `scripts/pre-release-check.sh`; no subprocess, network, clock,
         randomness, or filesystem write is involved.
@satisfies DES-084 DES-173 DES-198
"""

import re
import unittest
from pathlib import Path

## @brief Path of the pre-release check script under test.
## @details Resolved relative to this test module so the suite stays independent
##          of the process working directory.
PRERELEASE_SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "pre-release-check.sh"
)

## @brief Pattern matching a standalone `dist` token inside one code line.
## @details Matches `dist`, `dist/`, and `$PROJECT_ROOT/dist`. The surrounding
##          identifier guards keep `distribution`, `DIST_PREFIX`, and wheel
##          metadata paths such as `.dist-info` unmatched.
DIST_TOKEN = re.compile(r"(?<![A-Za-z0-9_.-])dist(?![A-Za-z0-9_-])")

## @brief Exact shell fragment creating the temporary check directory.
## @details The fragment is asserted verbatim so the release output directory
##          always derives from a `mktemp` directory.
MKTEMP_FRAGMENT = 'CHECK_DIRECTORY=$(mktemp -d "${TMPDIR:-/tmp}/cli-skills-pre-release.XXXXXX")'


class _ScriptTextCase(unittest.TestCase):
    """Level 0 base: tracked script text and executable-code extraction."""

    def setUp(self):
        """
        @brief Load the tracked pre-release check script text.
        @details Reads `scripts/pre-release-check.sh` once per test and fails
                 immediately when the script is missing. No subprocess or
                 filesystem write is performed.
        @return {None}
        """
        if not PRERELEASE_SCRIPT_PATH.is_file():
            self.fail(f"Missing pre-release check script: {PRERELEASE_SCRIPT_PATH}")
        self.script_text = PRERELEASE_SCRIPT_PATH.read_text(encoding="utf-8")

    def _code_lines(self):
        """
        @brief Collect the executable code lines of the script.
        @details Drops blank lines and full-line `#` comments so documentation
                 and Doxygen blocks cannot satisfy or defeat an assertion.
        @return {list[str]} Stripped, non-comment, non-empty lines in file order.
        """
        return [
            line.strip()
            for line in self.script_text.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]

    def _function_body(self, name):
        """
        @brief Extract the body of one top-level bash function.
        @details Collects the lines after `<name>() {` up to the first line equal
                 to `}`. Fails when the function header or its closing brace is
                 absent.
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


class PreReleaseCheckTemporaryOutputTests(_ScriptTextCase):
    """Level 0: temporary release output directory of the pre-release gate."""

    def test_release_output_directory_is_a_temporary_directory(self):
        """
        @brief Check the release output directory derives from `mktemp -d`.
        @details Arranges the executable script lines, then asserts the exact
                 `mktemp` fragment appears once and that the release output
                 directory is the `release` child of that temporary directory.
        @return {None}
        @expected_output No assertion failure when the build output directory is
                         a freshly created temporary directory.
        @satisfies DES-084 DES-198
        """
        code_lines = self._code_lines()
        self.assertEqual(
            code_lines.count(MKTEMP_FRAGMENT),
            1,
            "expected exactly one mktemp-based temporary check directory",
        )
        self.assertEqual(
            code_lines.count("RELEASE_DIRECTORY=$CHECK_DIRECTORY/release"),
            1,
            "release output directory must be a child of the temporary directory",
        )

    def test_temporary_output_directory_inside_repository_is_rejected(self):
        """
        @brief Check a temporary path inside the repository tree aborts the run.
        @details Arranges the `main` body, then asserts the containment guard
                 matches `"$PROJECT_ROOT"/*` and terminates through `fail` before
                 the environment export and the build phase.
        @return {None}
        @expected_output No assertion failure when a repository-internal
                         temporary directory is rejected.
        @satisfies DES-084 DES-198
        """
        body = self._function_body("main")
        self.assertIn('"$PROJECT_ROOT"/*', body)
        guard = body.split('"$PROJECT_ROOT"/*', 1)[1].split("esac", 1)[0]
        self.assertIn("fail", guard)
        self.assertLess(
            body.index('"$PROJECT_ROOT"/*'),
            body.index("export UV_PROJECT_ENVIRONMENT"),
        )
        self.assertLess(
            body.index('"$PROJECT_ROOT"/*'),
            body.index("scripts/build.sh"),
        )

    def test_build_invocation_uses_the_temporary_output_directory(self):
        """
        @brief Check `scripts/build.sh` receives the temporary output directory.
        @details Arranges the executable script lines, then asserts exactly one
                 `scripts/build.sh` invocation exists and that it passes
                 `--output-dir "$RELEASE_DIRECTORY"` without any literal `dist`
                 path.
        @return {None}
        @expected_output No assertion failure when the test build runs outside
                         `dist/`.
        @satisfies DES-084 DES-198
        """
        invocations = [
            line
            for line in self._code_lines()
            if "scripts/build.sh" in line and "--output-dir" in line
        ]
        self.assertEqual(
            len(invocations),
            1,
            f"expected exactly one build invocation, found {invocations}",
        )
        self.assertIn('--output-dir "$RELEASE_DIRECTORY"', invocations[0])


class PreReleaseCheckDistIndependenceTests(_ScriptTextCase):
    """Level 0: absence of `dist/` operations in the pre-release gate."""

    def test_executable_code_references_no_dist_entry(self):
        """
        @brief Check no executable code line names a `dist/` entry.
        @details Arranges the executable code lines with comments removed, then
                 asserts none matches the standalone `dist` token. Documentation
                 may describe the independence; only code is constrained.
        @return {None}
        @expected_output No assertion failure when the script neither reads,
                         verifies, creates, modifies, nor removes `dist/`.
        @satisfies DES-173 DES-198
        """
        offenders = [
            line for line in self._code_lines() if DIST_TOKEN.search(line)
        ]
        self.assertEqual(
            offenders,
            [],
            f"pre-release-check.sh must not operate on dist/: {offenders}",
        )

    def test_no_dist_directory_variable_is_declared(self):
        """
        @brief Check the script declares no `dist/` directory variable.
        @details Arranges the executable code lines, then asserts the
                 `DIST_DIRECTORY` identifier used by the build cleanup helpers is
                 absent, so no removal or validation path can target `dist/`.
        @return {None}
        @expected_output No assertion failure when no `dist/`-targeting variable
                         exists in the pre-release gate.
        @satisfies DES-173 DES-198
        """
        offenders = [
            line for line in self._code_lines() if "DIST_DIRECTORY" in line
        ]
        self.assertEqual(
            offenders,
            [],
            f"pre-release-check.sh must not declare a dist directory: {offenders}",
        )


if __name__ == "__main__":
    unittest.main()
