"""PyPI trove classifier conformance tests.

@file test_pyproject_classifiers.py
@brief Verify every `pyproject.toml` classifier is an official trove classifier.
@details HDT Level 0 static conformance suite. The UUT is the `classifiers`
         array of `pyproject.toml`. Each entry is validated against a static
         snapshot fixture of the official PyPI trove classifier list, so the
         suite reproduces upload-time `400 ... is not a valid classifier`
         rejections locally without network access. External dependency: one
         deterministic read of the tracked `pyproject.toml`; no network,
         clock, filesystem writes, or randomness are involved.
@satisfies DES-080 PRJ-012 DES-079
"""

import unittest
from pathlib import Path
from tomllib import loads

## @brief Path of the project metadata file under test.
## @details Resolved relative to this test module so the suite stays
##          independent of the process working directory.
PYPROJECT_PATH = Path(__file__).resolve().parents[1] / "pyproject.toml"

## @brief Snapshot of official PyPI trove classifiers permitted in project metadata.
## @details Fixture verified against https://pypi.org/classifiers/ on
##          2026-11-08. `Topic :: Software Development :: Configuration
##          Management` is absent from the official list (0 occurrences) and
##          caused the PyPI upload rejection `400 ... is not a valid
##          classifier`; `Topic :: Software Development` is its valid direct
##          parent. Update this fixture only from a fresh official list.
VALID_TROVE_CLASSIFIERS = frozenset(
    {
        "Development Status :: 3 - Alpha",
        "Development Status :: 4 - Beta",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Utilities",
    }
)


class PyprojectClassifierTests(unittest.TestCase):
    """Level 0: project metadata trove-classifier policy conformance."""

    def setUp(self):
        """
        @brief Load the deterministic metadata fixture for one test.
        @details Parses the tracked `pyproject.toml`; fails immediately with a
                 diagnostic when the file is missing.
        @return {None}
        """
        if not PYPROJECT_PATH.is_file():
            self.fail(f"Missing project metadata file: {PYPROJECT_PATH}")
        self.classifiers = loads(PYPROJECT_PATH.read_text(encoding="utf-8"))["project"][
            "classifiers"
        ]

    def test_every_declared_classifier_is_official(self):
        """
        @brief Check each declared classifier against the official snapshot.
        @details Arranges the parsed `classifiers` array, asserts it is
                 non-empty, then asserts per entry membership in the official
                 trove snapshot so PyPI upload cannot reject project metadata.
        @return {None}
        @expected_output No assertion failure when every declared classifier is
                         an official trove classifier.
        @satisfies DES-080 PRJ-012 DES-079
        """
        self.assertTrue(self.classifiers, "expected at least one declared classifier")
        for classifier in self.classifiers:
            self.assertIn(
                classifier,
                VALID_TROVE_CLASSIFIERS,
                f"{classifier} is not an official PyPI trove classifier; "
                "PyPI upload rejects it with HTTP 400",
            )


if __name__ == "__main__":
    unittest.main()
