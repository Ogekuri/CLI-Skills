"""Pre-release check script release-artifact removal conformance tests.

@file test_prerelease_check_script.py
@brief Verify the pre-existing release artifact removal and its verification in `scripts/pre-release-check.sh`.
@details HDT Level 0 static conformance suite (Generator mode). UUTs: the removal
         helpers `check_dist_state`, `remove_generated_outputs`,
         `remove_staging_leftovers`, and `remove_generated_archives` of
         `scripts/pre-release-check.sh`, plus the verification helper
         `verify_dist_clean` and the `main` phase ordering. Call graph: `main` ->
         removal helpers -> `verify_dist_clean` -> `capture_snapshot`. External
         dependencies isolated: deterministic reads of the tracked
         `scripts/pre-release-check.sh` and `scripts/build.sh`; no subprocess,
         network, clock, randomness, or filesystem writes are involved.
@satisfies DES-143 DES-194 DES-195 DES-196 DES-197
"""

import unittest
from pathlib import Path

## @brief Repository scripts directory resolved relative to this test module.
## @details Keeps the suite independent of the process working directory.
SCRIPTS_DIRECTORY = Path(__file__).resolve().parents[1] / "scripts"

## @brief Path of the release gate script under test.
PRERELEASE_SCRIPT_PATH = SCRIPTS_DIRECTORY / "pre-release-check.sh"

## @brief Path of the release build script providing the reference removal implementation.
BUILD_SCRIPT_PATH = SCRIPTS_DIRECTORY / "build.sh"

## @brief Removal and guard helpers that MUST stay identical to `scripts/build.sh`.
SHARED_HELPERS = (
    "check_dist_state",
    "remove_generated_outputs",
    "remove_staging_leftovers",
    "remove_generated_archives",
)


def _function_body(script_text, name):
    """
    @brief Extract the body of one top-level bash function.
    @details Collects the lines after `<name>() {` up to the first line equal to
             `}`. Returns `None` when the header or the closing brace is absent,
             so callers report a single actionable failure.
    @param script_text {str} Full bash script text.
    @param name {str} Bash function name without parentheses.
    @return {str | None} Newline-joined body lines, or `None` when absent.
    """
    lines = script_text.splitlines()
    header = f"{name}() {{"
    if header not in lines:
        return None
    start = lines.index(header) + 1
    for end in range(start, len(lines)):
        if lines[end] == "}":
            return "\n".join(lines[start:end])
    return None


class PreReleaseArtifactRemovalFixture(unittest.TestCase):
    """Level 0: shared fixture for the release gate script text."""

    def setUp(self):
        """
        @brief Load both tracked scripts for one test.
        @details Reads the release gate and the release build script once per
                 test and fails immediately with a diagnostic when a script is
                 missing. No subprocess or filesystem write is performed.
        @return {None}
        """
        for path in (PRERELEASE_SCRIPT_PATH, BUILD_SCRIPT_PATH):
            if not path.is_file():
                self.fail(f"Missing script: {path}")
        self.prerelease_text = PRERELEASE_SCRIPT_PATH.read_text(encoding="utf-8")
        self.build_text = BUILD_SCRIPT_PATH.read_text(encoding="utf-8")

    def _prerelease_body(self, name):
        """
        @brief Extract one helper body from the release gate script.
        @param name {str} Bash function name without parentheses.
        @return {str} Newline-joined function body lines.
        """
        body = _function_body(self.prerelease_text, name)
        if body is None:
            self.fail(f"missing function in scripts/pre-release-check.sh: {name}")
        return body


class PreReleaseRemovalImplementationTests(PreReleaseArtifactRemovalFixture):
    """Level 0: `dist/` removal implementation of the release gate script."""

    def test_removal_helpers_match_build_script_bootstrap(self):
        """
        @brief Check every removal helper equals its `scripts/build.sh` counterpart.
        @details Arranges the `check_dist_state`, `remove_generated_outputs`,
                 `remove_staging_leftovers`, and `remove_generated_archives`
                 bodies of both scripts, then asserts byte-identical bodies so
                 the release gate executes the same removal operations as the
                 build bootstrap.
        @return {None}
        @expected_output No assertion failure when both scripts share one removal
                         implementation.
        @satisfies DES-196
        """
        for name in SHARED_HELPERS:
            with self.subTest(helper=name):
                build_body = _function_body(self.build_text, name)
                self.assertIsNotNone(
                    build_body,
                    f"missing reference function in scripts/build.sh: {name}",
                )
                self.assertEqual(
                    self._prerelease_body(name),
                    build_body,
                    f"{name} diverges from the scripts/build.sh implementation",
                )

    def test_removal_matches_every_distribution_name_and_version(self):
        """
        @brief Check the removal patterns ignore distribution name and version.
        @details Arranges the `remove_generated_archives` and
                 `remove_staging_leftovers` bodies, then asserts the `*.tar.gz`,
                 `*.whl`, and `.cli-skills-build.*` patterns exist and that no
                 `$DIST_PREFIX` restriction narrows the selection.
        @return {None}
        @expected_output No assertion failure when every previous artifact of
                         every name and version is removed.
        @satisfies DES-142 DES-194
        """
        archives = self._prerelease_body("remove_generated_archives")
        staging = self._prerelease_body("remove_staging_leftovers")
        self.assertIn("*.tar.gz", archives)
        self.assertIn("*.whl", archives)
        self.assertIn(".cli-skills-build.*", staging)
        self.assertNotIn("DIST_PREFIX", archives)
        self.assertNotIn("DIST_PREFIX", staging)

    def test_default_dist_directory_is_repository_dist(self):
        """
        @brief Check the removal target stays the repository `dist/` directory.
        @details Asserts the exact assignment `DIST_DIRECTORY=$PROJECT_ROOT/dist`
                 appears exactly once in the release gate script text.
        @return {None}
        @expected_output No assertion failure when the removal targets
                         `$PROJECT_ROOT/dist`.
        @satisfies DES-194
        """
        assignments = [
            line
            for line in self.prerelease_text.splitlines()
            if line.strip() == "DIST_DIRECTORY=$PROJECT_ROOT/dist"
        ]
        self.assertEqual(len(assignments), 1)

    def test_removal_preserves_unmatched_dist_entries(self):
        """
        @brief Check the removal never deletes the `dist/` directory itself.
        @details Arranges every removal helper body, then asserts no helper
                 deletes the release output directory root, so entries outside
                 the generated-output patterns survive.
        @return {None}
        @expected_output No assertion failure when only matched entries are
                         removed.
        @satisfies DES-143
        """
        for name in ("remove_generated_outputs", "remove_staging_leftovers", "remove_generated_archives"):
            with self.subTest(helper=name):
                body = self._prerelease_body(name)
                self.assertNotIn('rm -rf -- "$DIST_DIRECTORY"', body)


class PreReleaseRemovalVerificationTests(PreReleaseArtifactRemovalFixture):
    """Level 0: post-removal verification and phase ordering."""

    def test_verification_rejects_residual_generated_entries(self):
        """
        @brief Check the post-removal verification fails on any residual entry.
        @details Arranges the `verify_dist_clean` body, then asserts it
                 re-enumerates the archive and staging patterns, guards on a
                 non-zero match count, and terminates through `fail`.
        @return {None}
        @expected_output No assertion failure when a residual generated entry
                         aborts the gate with status 1.
        @satisfies DES-195
        """
        body = self._prerelease_body("verify_dist_clean")
        for pattern in ('*.tar.gz', '*.whl', '.cli-skills-build.*'):
            self.assertIn(pattern, body)
        self.assertIn("${#matches[@]} > 0", body)
        self.assertIn("fail ", body)

    def test_removal_and_verification_precede_the_presnapshot(self):
        """
        @brief Check removal and verification run before the pre-run Git snapshot.
        @details Arranges the `main` body, then asserts the removal phase invokes
                 `remove_generated_outputs` and `verify_dist_clean` before
                 `capture_snapshot before`, so the snapshot records the cleaned
                 repository and later comparison stays consistent.
        @return {None}
        @expected_output No assertion failure when cleanup precedes the snapshot.
        @satisfies DES-162 DES-194 DES-197
        """
        body = self._prerelease_body("main")
        snapshot = body.index("capture_snapshot before")
        self.assertLess(body.index("remove_generated_outputs"), snapshot)
        self.assertLess(body.index("verify_dist_clean"), snapshot)
        self.assertLess(body.index("check_dist_state"), snapshot)

    def test_removal_helper_set_is_complete(self):
        """
        @brief Check the gate script defines the full shared removal helper set.
        @details Asserts every helper named in `SHARED_HELPERS` has a function
                 header in the release gate script text.
        @return {None}
        @expected_output No assertion failure when the whole helper set exists.
        @satisfies DES-196
        """
        for name in SHARED_HELPERS:
            with self.subTest(helper=name):
                self.assertIn(f"{name}() {{", self.prerelease_text)


if __name__ == "__main__":
    unittest.main()
