"""Release build script egg-info cleanup conformance tests.

@file test_build_script.py
@brief Verify `scripts/build.sh` removes every `*.egg-info` directory under `src/`.
@details HDT Level 0 static conformance suite. The UUT is the egg-info cleanup
         `find` command of `scripts/build.sh`, located by its unique egg-info
         pattern. The suite asserts that the command searches `src/` without a
         depth limit, so nested egg-info directories are removed as DES-147
         requires. External dependency: one deterministic read of the tracked
         `scripts/build.sh`; no subprocess, network, clock, randomness, or
         filesystem writes are involved.
@satisfies DES-147
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


if __name__ == "__main__":
    unittest.main()
