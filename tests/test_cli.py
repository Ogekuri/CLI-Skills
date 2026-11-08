import contextlib
from email.message import Message
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from cli_skills import core


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "cache.json"
        patcher = patch.object(core, "cache_path", return_value=self.path)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.err = io.StringIO()
        self.redirect = contextlib.redirect_stderr(self.err)
        self.redirect.__enter__()
        self.addCleanup(self.redirect.__exit__, None, None, None)

    def release(self, tag):
        return io.BytesIO(json.dumps({"tag_name": tag}).encode())

    def pypi_release(self, version):
        return io.BytesIO(json.dumps({"info": {"version": version}}).encode())

    @patch("cli_skills.core.time.time", return_value=1000)
    def test_new_version_and_cached_check(self, clock):
        with patch("cli_skills.core.urlopen", return_value=self.pypi_release("1.2.3")) as request:
            core.check_version()
            core.check_version()
        self.assertEqual(request.call_count, 1)
        self.assertEqual(request.call_args.kwargs["timeout"], 2)
        self.assertIn("pypi.org/pypi/cli-skills/json", request.call_args.args[0].full_url)
        data = json.loads(self.path.read_text())
        self.assertEqual(data["last_success_epoch"], 1000)
        self.assertEqual(data["idle_time_epoch"], 4600)
        self.assertIn("\x1b[92m", self.err.getvalue())

    @patch("cli_skills.core.time.time", return_value=1000)
    def test_failure_preserves_success_and_backs_off(self, clock):
        self.path.write_text(json.dumps({"last_success_epoch": 500, "idle_time_epoch": 999}))
        error = HTTPError(core.ENDPOINT, 429, "Too Many Requests", Message(), None)
        with patch("cli_skills.core.urlopen", side_effect=error):
            core.check_version()
        data = json.loads(self.path.read_text())
        self.assertEqual(data["last_success_epoch"], 500)
        self.assertEqual(data["idle_time_epoch"], 87400)
        self.assertIn("429", self.err.getvalue())
        self.assertIn("\x1b[91m", self.err.getvalue())

    @patch("cli_skills.core.time.time", return_value=1000)
    def test_no_newer_release_is_negative(self, clock):
        with patch("cli_skills.core.urlopen", return_value=self.pypi_release("0.0.0")):
            core.check_version()
        data = json.loads(self.path.read_text())
        self.assertEqual(data["last_success_epoch"], 1000)
        self.assertEqual(data["idle_time_epoch"], 87400)

    def test_version_forces_check_and_help_output(self):
        with patch.object(core, "check_version") as check, patch.object(core, "fetch_pypi_latest", return_value="9.9.9"), patch.object(core, "fetch_github_latest", return_value="8.8.8"), contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(core.main(["--version"]), 0)
            self.assertEqual(
                output.getvalue(),
                core.__version__ + "\nPyPI latest: 9.9.9\nGitHub latest: 8.8.8\n",
            )
            check.assert_called_once_with(force=True)
        with patch.object(core, "check_version"), contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(core.main([]), 0)
            self.assertEqual(output.getvalue(), core.HELP + "\n")

    def test_management_platforms(self):
        with patch.object(core, "check_version"), patch.object(core.sys, "platform", "linux"), patch.object(core.subprocess, "run") as run:
            run.return_value.returncode = 0
            self.assertEqual(core.main(["--upgrade"]), 0)
            run.assert_called_once_with(core.UPGRADE, check=False)
        with patch.object(core, "check_version"), patch.object(core.sys, "platform", "darwin"), patch.object(core.subprocess, "run") as run, contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(core.main(["--uninstall"]), 0)
            run.assert_not_called()
            self.assertIn("uv tool uninstall cli-skills", output.getvalue())

    @patch.object(core, "_post_upgrade_install", return_value=7)
    def test_upgrade_develop_installs_from_github(self, chained):
        """
        @brief Verify `--upgrade --dev` installs the latest GitHub release.
        @details Patches the platform to Linux and the chained install; expects
                 both `--upgrade --dev` and `--develop --upgrade` argument
                 orders to execute `UPGRADE_DEVELOP` and to chain the
                 post-upgrade install, returning its exit code.
        @param chained {MagicMock} Replacement for `_post_upgrade_install`.
        @return {None}
        @expected_output Exit code 7 from the chained install and
                 `subprocess.run` called with `UPGRADE_DEVELOP`.
        @satisfies REQ-063 REQ-043 REQ-046
        """
        with patch.object(core, "check_version"), patch.object(core.sys, "platform", "linux"), patch.object(core.subprocess, "run") as run:
            run.return_value.returncode = 0
            self.assertEqual(core.main(["--upgrade", "--dev"]), 7)
            self.assertEqual(core.main(["--develop", "--upgrade"]), 7)
        self.assertEqual(run.call_args.args[0], core.UPGRADE_DEVELOP)
        chained.assert_called_with()

    def test_develop_without_upgrade_is_usage_error(self):
        """
        @brief Verify `--dev`/`--develop` without `--upgrade` is a usage error.
        @details Patches the release check; expects exit code 2 for both
                 spellings invoked alone.
        @return {None}
        @expected_output Exit code 2 for `--dev` and `--develop` alone.
        @satisfies REQ-064
        """
        with patch.object(core, "check_version"), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(core.main(["--dev"]), 2)
            self.assertEqual(core.main(["--develop"]), 2)


if __name__ == "__main__":
    unittest.main()
