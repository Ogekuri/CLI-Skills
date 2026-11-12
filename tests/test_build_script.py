"""Release build script cleanup conformance tests.

@file test_build_script.py
@brief Verify `scripts/build.sh` cleanup scope, cleanup ordering, and `--output-dir` argument contract.
@details HDT Level 0 static conformance suite. The UUTs are the cleanup helpers
         of `scripts/build.sh` and its argument parser, located by their function
         headers. The suite asserts that the pre-build phase removes every
         previous build artifact, that the post-build phase removes every
         intermediate artifact, and that the release output cleanup removes
         archives of every distribution name and version. External dependency:
         deterministic reads of the tracked `scripts/build.sh` and of the
         repository scripts directory; no subprocess, network, clock,
         randomness, or filesystem writes are involved.
@satisfies DES-142 DES-147 DES-171 DES-172 DES-175 DES-186 DES-187 DES-188
"""

import unittest
from pathlib import Path

## @brief Path of the release build script under test.
## @details Resolved relative to this test module so the suite stays
##          independent of the process working directory.
BUILD_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "build.sh"


class BuildScriptEggInfoCleanupTests(unittest.TestCase):
    """Level 0: egg-info cleanup scope of the release build script."""

    def setUp(self):
        """
        @brief Collect the egg-info cleanup command candidates for one test.
        @details Reads the tracked `scripts/build.sh` and keeps every line that
                 contains both the `find` keyword and the `'*.egg-info'` pattern.
                 Fails immediately with a diagnostic when the script is missing.
        @return {None}
        """
        if not BUILD_SCRIPT_PATH.is_file():
            self.fail(f"Missing build script: {BUILD_SCRIPT_PATH}")
        self.candidates = [
            line.strip()
            for line in BUILD_SCRIPT_PATH.read_text(encoding="utf-8").splitlines()
            if "find" in line and "'*.egg-info'" in line
        ]

    def test_egg_info_cleanup_searches_src_without_depth_limit(self):
        """
        @brief Check the egg-info cleanup `find` searches `src/` recursively.
        @details Arranges exactly one egg-info cleanup command, then asserts it
                 is scoped to `"$PROJECT_ROOT/src"`, matches `-name '*.egg-info'`,
                 and carries no `-maxdepth` restriction that would leave nested
                 egg-info directories behind.
        @return {None}
        @expected_output No assertion failure when the cleanup command removes
                         every `*.egg-info` directory under `src/`.
        @satisfies DES-147
        """
        self.assertEqual(
            len(self.candidates),
            1,
            f"expected exactly one egg-info cleanup command, found {self.candidates}",
        )
        command = self.candidates[0]
        self.assertIn('"$PROJECT_ROOT/src"', command)
        self.assertIn("-name '*.egg-info'", command)
        self.assertNotIn(
            "-maxdepth",
            command,
            "depth-limited cleanup leaves nested *.egg-info under src/",
        )


class BuildScriptOutputDirectoryTests(unittest.TestCase):
    """Level 0: `--output-dir` argument contract of the release build script."""

    def setUp(self):
        """
        @brief Load the tracked release build script text for one test.
        @details Reads `scripts/build.sh` once per test and fails immediately
                 when the script is missing. No subprocess or filesystem write
                 is performed.
        @return {None}
        """
        if not BUILD_SCRIPT_PATH.is_file():
            self.fail(f"Missing build script: {BUILD_SCRIPT_PATH}")
        self.script_text = BUILD_SCRIPT_PATH.read_text(encoding="utf-8")

    def _function_body(self, name):
        """
        @brief Extract the body of one top-level bash function.
        @details Collects the lines after `<name>() {` up to the first line
                 equal to `}`. Fails when the function header or its closing
                 brace is absent.
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

    def test_parse_arguments_declares_output_dir_option(self):
        """
        @brief Check the argument parser declares exactly one `--output-dir` branch.
        @details Arranges the `parse_arguments` body, then asserts one case label
                 `--output-dir)` exists and a guard rejects a missing value through
                 the `$# < 2` condition.
        @return {None}
        @expected_output No assertion failure when the parser accepts
                         `--output-dir <path>` and rejects a missing value.
        @satisfies DES-171 DES-172
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
                 guard is preceded by a `usage` call.
        @return {None}
        @expected_output No assertion failure when every non-absolute path
                         terminates through `usage` with exit status 2.
        @satisfies DES-172
        """
        body = self._function_body("parse_arguments")
        self.assertIn("[[ $output != /* ]]", body)
        guarded = body.split("[[ $output != /* ]]", 1)[1].split("fi", 1)[0]
        self.assertIn("usage", guarded)

    def test_default_release_output_directory_is_dist(self):
        """
        @brief Check the default release output directory remains `dist/`.
        @details Asserts the exact default assignment `DIST_DIRECTORY=$PROJECT_ROOT/dist`
                 appears exactly once in the script text.
        @return {None}
        @expected_output No assertion failure when the default is `$PROJECT_ROOT/dist`.
        @satisfies DES-171
        """
        assignments = [
            line
            for line in self.script_text.splitlines()
            if line.strip() == "DIST_DIRECTORY=$PROJECT_ROOT/dist"
        ]
        self.assertEqual(len(assignments), 1)


class BuildScriptCleanupTests(unittest.TestCase):
    """Level 0: pre-build and post-build cleanup scope of the release build script."""

    def setUp(self):
        """
        @brief Load the tracked release build script text for one test.
        @details Reads `scripts/build.sh` once per test and fails immediately
                 when the script is missing.
        @return {None}
        """
        if not BUILD_SCRIPT_PATH.is_file():
            self.fail(f"Missing build script: {BUILD_SCRIPT_PATH}")
        self.script_text = BUILD_SCRIPT_PATH.read_text(encoding="utf-8")

    def _function_body(self, name):
        """
        @brief Extract the body of one top-level bash function.
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

    def test_release_output_cleanup_matches_every_build(self):
        """
        @brief Check the release output cleanup ignores distribution name and version.
        @details Arranges the `remove_generated_archives` body, then asserts the
                 `*.tar.gz` and `*.whl` patterns exist and that no
                 `$DIST_PREFIX` restriction narrows the selection.
        @return {None}
        @expected_output No assertion failure when every archive of every
                         previous build is removed.
        @satisfies DES-142
        """
        body = self._function_body("remove_generated_archives")
        self.assertIn("*.tar.gz", body)
        self.assertIn("*.whl", body)
        self.assertNotIn("DIST_PREFIX", body)

    def test_pre_build_cleanup_precedes_the_build_phase(self):
        """
        @brief Check previous build artifacts are removed before the build starts.
        @details Arranges the `run_build` body, then asserts the cleanup phase
                 invokes `remove_generated_outputs` and `remove_build_intermediates`
                 before `build_into_staging`.
        @return {None}
        @expected_output No assertion failure when cleanup precedes the build phase.
        @satisfies PRJ-021 DES-186
        """
        body = self._function_body("run_build")
        self.assertLess(body.index("remove_generated_outputs"), body.index("build_into_staging"))
        self.assertLess(body.index("remove_build_intermediates"), body.index("build_into_staging"))

    def test_intermediate_cleanup_covers_build_egg_info_and_pycache(self):
        """
        @brief Check the intermediate cleanup covers every build artifact class.
        @details Arranges the `remove_build_intermediates` body, then asserts the
                 repository `build/` entry, the `src` egg-info pattern, and the
                 `src` plus `tests` `__pycache__` pattern are all present.
        @return {None}
        @expected_output No assertion failure when every intermediate artifact is
                         removed at the start and at the end of the build.
        @satisfies DES-147 DES-186
        """
        body = self._function_body("remove_build_intermediates")
        self.assertIn('"$PROJECT_ROOT/build"', body)
        self.assertIn("-name '*.egg-info'", body)
        self.assertIn("-name '__pycache__'", body)
        self.assertIn('"$PROJECT_ROOT/src" "$PROJECT_ROOT/tests"', body)

    def test_exit_cleanup_removes_intermediate_artifacts(self):
        """
        @brief Check the EXIT-trap cleanup removes intermediates on every exit path.
        @details Arranges the `cleanup_owned_outputs` body, then asserts the shared
                 intermediate cleanup helper runs when cleanup is enabled.
        @return {None}
        @expected_output No assertion failure when a successful build leaves no
                         intermediate artifact behind.
        @satisfies DES-147 DES-187
        """
        body = self._function_body("cleanup_owned_outputs")
        self.assertIn("CLEANUP_ENABLED", body)
        self.assertIn("remove_build_intermediates", body)

    def test_clean_script_is_absent(self):
        """
        @brief Check the removed standalone clean script stays removed.
        @details Asserts `scripts/clean.sh` does not exist in the repository.
        @return {None}
        @expected_output No assertion failure when cleanup lives only in
                         `scripts/build.sh`.
        @satisfies PRJ-021
        """
        self.assertFalse((BUILD_SCRIPT_PATH.parent / "clean.sh").exists())


if __name__ == "__main__":
    unittest.main()
