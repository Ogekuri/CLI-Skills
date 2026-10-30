import contextlib
from email.message import Message
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from skills import core


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

    @patch("skills.core.time.time", return_value=1000)
    def test_new_version_and_cached_check(self, clock):
        with patch("skills.core.urlopen", return_value=self.release("v1.2.3")) as request:
            core.check_version()
            core.check_version()
        self.assertEqual(request.call_count, 1)
        self.assertEqual(request.call_args.kwargs["timeout"], 2)
        data = json.loads(self.path.read_text())
        self.assertEqual(data["last_success_epoch"], 1000)
        self.assertEqual(data["idle_time_epoch"], 4600)
        self.assertIn("\x1b[92m", self.err.getvalue())

    @patch("skills.core.time.time", return_value=1000)
    def test_failure_preserves_success_and_backs_off(self, clock):
        self.path.write_text(json.dumps({"last_success_epoch": 500, "idle_time_epoch": 999}))
        error = HTTPError(core.ENDPOINT, 429, "Too Many Requests", Message(), None)
        with patch("skills.core.urlopen", side_effect=error):
            core.check_version()
        data = json.loads(self.path.read_text())
        self.assertEqual(data["last_success_epoch"], 500)
        self.assertEqual(data["idle_time_epoch"], 87400)
        self.assertIn("429", self.err.getvalue())
        self.assertIn("\x1b[91m", self.err.getvalue())

    @patch("skills.core.time.time", return_value=1000)
    def test_no_newer_release_is_negative(self, clock):
        with patch("skills.core.urlopen", return_value=self.release("v0.0.0")):
            core.check_version()
        data = json.loads(self.path.read_text())
        self.assertEqual(data["last_success_epoch"], 1000)
        self.assertEqual(data["idle_time_epoch"], 87400)

    def test_version_forces_check_and_help_output(self):
        with patch.object(core, "check_version") as check, contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(core.main(["--version"]), 0)
            self.assertEqual(output.getvalue(), core.__version__ + "\n")
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
            self.assertIn("uv tool uninstall skills", output.getvalue())


if __name__ == "__main__":
    unittest.main()
