"""Requirement-citation traceability tests.

@file test_requirements_traceability.py
@brief Verify that every requirement ID cited by `src` and `tests` Python sources is declared in the SRS.
@details HDT Level 0 static conformance suite. The UUT is the ordered
         requirement-line set of `usereq/docs/REQUIREMENTS.md`. The suite
         asserts that every requirement identifier cited by a Python source
         under `src/` or `tests/` resolves to a declared requirement, so
         retired identifiers cannot survive in code or test documentation.
         External dependency: deterministic reads of tracked files; no
         subprocess, network, clock, randomness, or filesystem writes are
         involved.
@satisfies DOC-003 DOC-004
"""

import re
import unittest
from pathlib import Path

## @brief Repository root resolved relative to this test module.
## @details Keeps the suite independent of the process working directory.
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

## @brief Requirement document declaring every canonical requirement ID.
REQUIREMENTS_PATH = REPOSITORY_ROOT / "usereq" / "docs" / "REQUIREMENTS.md"

## @brief Source trees scanned for requirement citations.
## @details Only Python sources are scanned; generated reference documents and
##          release history are out of scope.
CITATION_ROOTS = ("src", "tests")

## @brief Canonical requirement-line declaration pattern.
DECLARATION_PATTERN = re.compile(
    r"^- \*\*((?:DOC|PRJ|CTN|DES|REQ)-\d{3})\*\*:", re.MULTILINE
)

## @brief Requirement identifier citation pattern.
CITATION_PATTERN = re.compile(r"\b((?:PRJ|CTN|DES|REQ)-\d{3})\b")


class RequirementCitationTraceabilityTests(unittest.TestCase):
    """Level 0: requirement citations in Python sources resolve to declared IDs."""

    def setUp(self):
        """
        @brief Load the declared requirement IDs and the citation map.
        @details Reads the SRS once, then scans every Python file under
                 `CITATION_ROOTS` and records each cited ID with its citing
                 repository-relative file paths.
        @return {None}
        """
        if not REQUIREMENTS_PATH.is_file():
            self.fail(f"Missing requirements document: {REQUIREMENTS_PATH}")
        self.declared = set(
            DECLARATION_PATTERN.findall(REQUIREMENTS_PATH.read_text(encoding="utf-8"))
        )
        self.citations = {}
        for root in CITATION_ROOTS:
            for path in sorted((REPOSITORY_ROOT / root).rglob("*.py")):
                text = path.read_text(encoding="utf-8")
                for requirement_id in CITATION_PATTERN.findall(text):
                    self.citations.setdefault(requirement_id, set()).add(
                        path.relative_to(REPOSITORY_ROOT).as_posix()
                    )

    def test_cited_requirement_ids_are_declared(self):
        """
        @brief Verify every cited requirement ID is declared in the SRS.
        @details Subtracts the declared ID set from the cited ID set and asserts
                 the difference is empty, reporting every dangling citation
                 together with its citing files.
        @return {None}
        @expected_output No assertion failure when every cited requirement ID
                         is declared in `usereq/docs/REQUIREMENTS.md`.
        @satisfies DOC-003 DOC-004
        """
        dangling = {
            requirement_id: sorted(files)
            for requirement_id, files in self.citations.items()
            if requirement_id not in self.declared
        }
        self.assertEqual({}, dangling, f"dangling requirement citations: {dangling}")


if __name__ == "__main__":
    unittest.main()
