"""Release workflow Node24 action-runtime conformance tests.

@file test_release_workflow.py
@brief Verify the release workflow pins only Node24-or-later action versions.
@details HDT Level 0 static conformance suite. The UUT is the set of `uses:`
         references in `.github/workflows/release-pypi.yml`, validated against
         the CTN-010 minimum-version policy and against the absence of the
         transient Node20 fallback environment workarounds described in the
         GitHub Actions Node20 deprecation communication. External dependency:
         one deterministic read of the tracked workflow file; no network,
         clock, filesystem writes, or randomness are involved.
@satisfies CTN-010 DES-077
"""

import re
import unittest
from pathlib import Path

## @brief Path of the release workflow file under test.
## @details Resolved relative to this test module so the suite stays
##          independent of the process working directory.
WORKFLOW_PATH = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "release-pypi.yml"

## @brief Minimum action version whose Node execution is Node24 or later, keyed by action slug.
## @details Values derive from the `runs.using` fields of each action's verified
##          release tag and, for composite actions, from their inner Node-based
##          steps: `actions/checkout` v5.0.0, `actions/setup-python` v6.0.0,
##          `astral-sh/setup-uv` v10.3.3, `actions/attest-build-provenance`
##          v4.2.2 (composite delegating to `actions/attest` v4.2.1, node24),
##          `mikepenz/release-changelog-builder-action` v6.5,
##          `softprops/action-gh-release` v3.0.4, and
##          `pypa/gh-action-pypi-publish` v1.14.3 (composite with
##          `actions/setup-python` v6.2.0 plus shell and docker steps). Higher
##          versions remain compliant because CTN-010 constrains Node24 or later.
NODE24_MINIMUM_VERSION = {
    "actions/checkout": (5, 0),
    "actions/setup-python": (6, 0),
    "astral-sh/setup-uv": (10, 0),
    "actions/attest-build-provenance": (4, 0),
    "mikepenz/release-changelog-builder-action": (6, 0),
    "softprops/action-gh-release": (3, 0),
    "pypa/gh-action-pypi-publish": (1, 14),
}

## @brief Transient Node20 fallback environment variable names from the deprecation communication.
## @details `ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION` opted runners back into
##          Node20 after the June 2026 default switch; `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24`
##          was the pre-migration forward-forcing toggle. Both are transitional
##          workarounds and MUST NOT appear in the migrated workflow.
NODE20_FALLBACK_ENVIRONMENTS = (
    "ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION",
    "FORCE_JAVASCRIPT_ACTIONS_TO_NODE24",
)

## @brief Regex extracting every `uses:` action reference line from workflow text.
## @details Captures the full `owner/repo@ref` token; anchored per line to avoid
##          matching substrings inside run scripts or descriptions.
USES_PATTERN = re.compile(r"^[ \t]*uses:[ \t]*(\S+)[ \t]*$", re.MULTILINE)

## @brief Regex splitting one pinned action reference into slug and version parts.
## @details Accepts versioned refs of the form `owner/repo@v<major>[.<minor>[.<patch>]]`;
##          missing components default to zero. Floating-commit or
##          digest refs fail the conformance check by design.
REFERENCE_PATTERN = re.compile(r"^(?P<slug>[^@]+)@v(?P<major>\d+)(?:\.(?P<minor>\d+))?(?:\.(?P<patch>\d+))?$")


class ReleaseWorkflowNode24Tests(unittest.TestCase):
    """Level 0: release workflow action-runtime policy conformance."""

    def setUp(self):
        """
        @brief Load the deterministic workflow fixture for one test.
        @details Reads the tracked workflow file into `self.workflow_text`;
                 fails immediately with a diagnostic when the file is missing.
        @return {None}
        """
        if not WORKFLOW_PATH.is_file():
            self.fail(f"Missing release workflow file: {WORKFLOW_PATH}")
        self.workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")

    def test_every_action_reference_is_node24_or_later(self):
        """
        @brief Check every pinned action version against the CTN-010 policy.
        @details Arranges the `uses:` reference list, asserts the list is
                 non-empty, then asserts per reference: parseable
                 `owner/repo@v<major>[.<minor>[.<patch>]]` format, known slug, and
                 version greater than or equal to the first Node24 runtime
                 version for that action.
        @return {None}
        @expected_output No assertion failure when every reference satisfies
                         the Node24-or-later minimum-version policy.
        @satisfies CTN-010 DES-077
        """
        references = USES_PATTERN.findall(self.workflow_text)
        self.assertTrue(references, "expected at least one 'uses:' action reference")
        for reference in references:
            match = REFERENCE_PATTERN.match(reference)
            if match is None:
                self.fail(f"unsupported action reference format: {reference}")
            slug = match.group("slug")
            version = (int(match.group("major")), int(match.group("minor") or 0))
            self.assertIn(slug, NODE24_MINIMUM_VERSION, f"unknown action slug: {slug}")
            minimum = NODE24_MINIMUM_VERSION[slug]
            self.assertGreaterEqual(
                version,
                minimum,
                f"{slug}@v{version[0]}.{version[1]} predates the first Node24 runtime "
                f"version v{minimum[0]}.{minimum[1]}",
            )

    def test_workflow_has_no_node20_fallback_workaround_environments(self):
        """
        @brief Check the workflow contains no transient Node20 fallback toggles.
        @details Asserts the absence of both deprecation-communication
                 workaround environment variable names anywhere in the
                 workflow text.
        @return {None}
        @expected_output No assertion failure when no workaround name occurs.
        @satisfies CTN-010
        """
        for name in NODE20_FALLBACK_ENVIRONMENTS:
            self.assertNotIn(
                name,
                self.workflow_text,
                f"transient Node20 fallback workaround present: {name}",
            )

    def test_release_gates_artifacts_and_publish_on_unit_tests(self):
        """
        @brief Check the release workflow gates builds and publish on tests.
        @details Asserts that a dedicated `unit-tests` job exists and runs the
                 project-defined test command, and that `build-release`
                 declares a job dependency on it, so failing tests skip
                 artifact creation, the GitHub release, and the PyPI publish.
        @return {None}
        @expected_output No assertion failure when the gating structure is
                         present in the workflow.
        @satisfies PRJ-015 PRJ-016 DES-088
        """
        self.assertIn("unit-tests:", self.workflow_text)
        self.assertIn("run: uv run python -m unittest discover -s tests", self.workflow_text)
        self.assertRegex(
            self.workflow_text,
            r"(?m)^  build-release:\n    needs: \[check-branch, unit-tests\]$",
        )


if __name__ == "__main__":
    unittest.main()
