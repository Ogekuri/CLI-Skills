"""Release workflow action-runtime and artifact-reuse conformance tests.

@file test_release_workflow.py
@brief Verify the release workflow pins Node24 actions and reuses provided artifacts.
@details HDT Level 0 static conformance suite. The UUTs are the `uses:` references
         and the job/step structure of `.github/workflows/release-pypi.yml`,
         validated against the CTN-010 minimum-version policy, the resolvability
         of every `astral-sh/setup-uv` reference, the absence of transient Node20
         fallback workarounds, the release-workflow artifact-reuse contract, and
         the prohibition of build, build-preparatory, and pre-release-check
         steps. External dependency: one deterministic read of the tracked
         workflow file plus static fixtures recording verified upstream tag
         evidence; no network, clock, filesystem writes, or randomness are
         involved at test runtime.
@satisfies CTN-010 DES-077 DES-189 DES-190 DES-191 DES-192 DES-193 PRJ-022 PRJ-023
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
##          `astral-sh/setup-uv` v7.0.0 (upstream `action.yml` `runs.using`
##          evidence: v6.8.0 declares node20, v7.0.0 declares node24),
##          `actions/attest-build-provenance`
##          v4.2.2 (composite delegating to `actions/attest` v4.2.1, node24),
##          `mikepenz/release-changelog-builder-action` v6.5,
##          `softprops/action-gh-release` v3.0.4, and
##          `pypa/gh-action-pypi-publish` v1.14.3 (composite with
##          `actions/setup-python` v6.2.0 plus shell and docker steps). Higher
##          versions remain compliant because CTN-010 constrains Node24 or later.
NODE24_MINIMUM_VERSION = {
    "actions/checkout": (5, 0),
    "actions/setup-python": (6, 0),
    "astral-sh/setup-uv": (7, 0),
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

## @brief Floating major tags published by the upstream `astral-sh/setup-uv` repository.
## @details Fixture verified via `git ls-remote --tags
##          https://github.com/astral-sh/setup-uv`: majors 1-7 publish resolvable
##          floating major tags; majors 8-9 publish full-semver release tags only;
##          no `v10` ref exists in any form, so any `@v10` reference fails GitHub
##          Actions resolution with `unable to find version v10`.
SETUP_UV_FLOATING_MAJOR_TAGS = frozenset({1, 2, 3, 4, 5, 6, 7})

## @brief Published minor versions of `astral-sh/setup-uv` majors lacking a floating major tag.
## @details Fixture verified via `git ls-remote --tags
##          https://github.com/astral-sh/setup-uv`: major 8 releases v8.0.0
##          through v8.3.2; major 9 releases v9.0.0. A reference to one of these
##          majors resolves only when pinned as `v<major>.<minor>[.<patch>]`
##          whose minor matches a published release.
SETUP_UV_SEMVER_ONLY_PUBLISHED_MINORS = {
    8: frozenset({0, 1, 2, 3}),
    9: frozenset({0}),
}

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

    def test_every_setup_uv_reference_resolves_to_a_published_version(self):
        """
        @brief Check every setup-uv pin and the policy minimum are published versions.
        @details Reproducer for the unresolvable `astral-sh/setup-uv@v10` release
                 pin: asserts each `astral-sh/setup-uv` workflow reference
                 resolves against the upstream published tag set (floating major
                 tag, or full-semver ref whose minor is published), and asserts
                 the CTN-010 policy minimum itself denotes a published version so
                 fabricated version data cannot re-enter the policy table.
        @return {None}
        @expected_output No assertion failure when every `astral-sh/setup-uv`
                         reference and the CTN-010 policy minimum resolve to a
                         published upstream version.
        @satisfies CTN-010 DES-077
        """
        references = USES_PATTERN.findall(self.workflow_text)
        for reference in references:
            match = REFERENCE_PATTERN.match(reference)
            if match is None:
                self.fail(f"unsupported action reference format: {reference}")
            if match.group("slug") != "astral-sh/setup-uv":
                continue
            major = int(match.group("major"))
            minor = int(match.group("minor") or 0)
            if major in SETUP_UV_FLOATING_MAJOR_TAGS:
                continue
            published_minors = SETUP_UV_SEMVER_ONLY_PUBLISHED_MINORS.get(
                major, frozenset()
            )
            self.assertNotEqual(
                published_minors,
                frozenset(),
                f"astral-sh/setup-uv major v{major} is not published upstream; "
                "the workflow reference cannot resolve",
            )
            self.assertIn(
                minor,
                published_minors,
                f"astral-sh/setup-uv v{major}.{minor} is not a published release; "
                "the workflow reference cannot resolve",
            )
        policy_major, policy_minor = NODE24_MINIMUM_VERSION["astral-sh/setup-uv"]
        policy_published = policy_major in SETUP_UV_FLOATING_MAJOR_TAGS or (
            policy_minor
            in SETUP_UV_SEMVER_ONLY_PUBLISHED_MINORS.get(policy_major, frozenset())
        )
        self.assertTrue(
            policy_published,
            f"policy minimum v{policy_major}.{policy_minor} is not a published "
            "astral-sh/setup-uv version",
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

class ReleaseWorkflowCommittedArtifactTests(unittest.TestCase):
    """Level 0: artifact reuse and build-free automation conformance."""

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

    def test_workflow_executes_no_build_or_release_check(self):
        """
        @brief Check the workflow never builds or runs the release gate.
        @details Asserts the absence of every build command, of
                 `scripts/build.sh`, and of `scripts/pre-release-check.sh`.
        @return {None}
        @expected_output No assertion failure when the workflow only consumes
                         provided artifacts.
        @satisfies DES-189 DES-190
        """
        for forbidden in (
            "python -m build",
            "uv build",
            "uv run --frozen --with build",
            "scripts/build.sh",
            "scripts/pre-release-check.sh",
        ):
            self.assertNotIn(forbidden, self.workflow_text)

    def test_workflow_has_no_build_preparatory_steps(self):
        """
        @brief Check the workflow performs no build-preparatory checks.
        @details Asserts the absence of a unit-test job, Python and uv toolchain
                 setup, unit-test execution, and lockfile validation.
        @return {None}
        @expected_output No assertion failure when no build-preparatory step
                         remains in the automation.
        @satisfies DES-191
        """
        for forbidden in (
            "unit-tests:",
            "actions/setup-python",
            "astral-sh/setup-uv",
            "uv run python -m unittest",
            "uv lock --check",
        ):
            self.assertNotIn(forbidden, self.workflow_text)

    def test_release_publishes_only_workspace_artifacts(self):
        """
        @brief Check attestation, release assets, and PyPI reuse `dist/`.
        @details Asserts the attestation subject path, the GitHub release asset
                 glob, the PyPI packages directory, and the release job
                 dependency on the branch check only.
        @return {None}
        @expected_output No assertion failure when every publication step reads
                         the workspace `dist/` artifact set.
        @satisfies PRJ-022 PRJ-023 DES-079
        """
        self.assertIn("subject-path: dist/*", self.workflow_text)
        self.assertIn("files: dist/**/*", self.workflow_text)
        self.assertIn("packages-dir: dist/", self.workflow_text)
        self.assertRegex(
            self.workflow_text,
            r"(?m)^  release:\n    needs: \[check-branch\]$",
        )

    def test_workflow_verifies_artifact_versions(self):
        """
        @brief Check the workflow verifies sdist and wheel versions.
        @details Asserts a verification step derives `project.version` from
                 `pyproject.toml`, requires the matching sdist, and requires
                 exactly one matching wheel before publication.
        @return {None}
        @expected_output No assertion failure when the workspace artifact set is
                         validated against the project version.
        @satisfies DES-192
        """
        self.assertIn("Verify distribution artifacts", self.workflow_text)
        self.assertIn('dist/cli_skills-$version.tar.gz', self.workflow_text)
        self.assertIn('dist/cli_skills-"$version"-*.whl', self.workflow_text)
        self.assertIn('"${#wheels[@]}" -eq 1', self.workflow_text)


if __name__ == "__main__":
    unittest.main()
