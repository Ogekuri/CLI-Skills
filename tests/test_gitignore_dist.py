"""Repository .gitignore dist/ re-inclusion conformance tests.

@file test_gitignore_dist.py
@brief Verify the `.gitignore` dist/ re-inclusion rules and the absence of dist/-targeting exclusion rules.
@details HDT Level 0 static conformance suite. The UUT is the ordered rule list
         of the tracked `.gitignore`. The suite asserts that the re-inclusion
         rules `!dist/` and `!dist/**/*` follow every general exclusion rule and
         that no later rule explicitly targets `dist/` or its entries. External
         dependency: one deterministic read of the tracked `.gitignore`; no
         subprocess, network, clock, randomness, or filesystem writes are involved.
@satisfies DES-168 DES-170 DES-174
"""

import unittest
from pathlib import Path

## @brief Path of the repository ignore file under test.
## @details Resolved relative to this test module so the suite stays
##          independent of the process working directory.
GITIGNORE_PATH = Path(__file__).resolve().parents[1] / ".gitignore"

## @brief General exclusion rules that MUST precede the dist/ re-inclusion.
## @details Mirrors DES-170 general rules `/*`, `*.*`, and `*/**`.
GENERAL_EXCLUSION_RULES = ("/*", "*.*", "*/**")


class GitignoreDistRulesTests(unittest.TestCase):
    """Level 0: dist/ re-inclusion rules of the repository `.gitignore`."""

    def setUp(self):
        """
        @brief Load the ordered `.gitignore` physical lines for one test.
        @details Reads `.gitignore` once per test and fails immediately when the
                 file is missing. Lines keep their original order in `self.lines`.
        @return {None}
        """
        if not GITIGNORE_PATH.is_file():
            self.fail(f"Missing .gitignore: {GITIGNORE_PATH}")
        self.lines = GITIGNORE_PATH.read_text(encoding="utf-8").splitlines()

    def test_dist_reinclusion_follows_general_exclusion_rules(self):
        """
        @brief Check `!dist/` and `!dist/**/*` follow every general exclusion rule.
        @details Arranges the first index of each general exclusion rule and of
                 both re-inclusion rules. Asserts each general rule precedes `!dist/`
                 and that `!dist/` precedes `!dist/**/*`.
        @return {None}
        @expected_output No assertion failure when the re-inclusion rules are
                         ordered after the general exclusion rules.
        @satisfies DES-168 DES-170
        """
        index = {}
        for rule in (*GENERAL_EXCLUSION_RULES, "!dist/", "!dist/**/*"):
            self.assertIn(rule, self.lines, f"missing .gitignore rule: {rule}")
            index[rule] = self.lines.index(rule)
        for rule in GENERAL_EXCLUSION_RULES:
            self.assertLess(
                index[rule],
                index["!dist/"],
                f"general rule {rule} must precede !dist/",
            )
        self.assertLess(index["!dist/"], index["!dist/**/*"])

    def test_no_rule_targets_dist_after_reinclusion(self):
        """
        @brief Check no exclusion rule explicitly targets `dist/` after re-inclusion.
        @details Arranges the lines after `!dist/**/*`, drops blank, comment, and
                 negated lines, strips a leading `/`, and collects every remaining
                 rule equal to `dist` or starting with `dist/`. Asserts the collected
                 list is empty.
        @return {None}
        @expected_output No assertion failure when no dist/-targeting exclusion
                         rule follows the re-inclusion rules.
        @satisfies DES-168 DES-174
        """
        start = self.lines.index("!dist/**/*") + 1
        offending = []
        for line in self.lines[start:]:
            rule = line.strip()
            if not rule or rule.startswith("#") or rule.startswith("!"):
                continue
            normalized = rule.lstrip("/")
            if normalized == "dist" or normalized.startswith("dist/"):
                offending.append(rule)
        self.assertEqual(offending, [], "dist/-targeting rules follow the re-inclusion")


if __name__ == "__main__":
    unittest.main()
