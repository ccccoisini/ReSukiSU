import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import repack_apk_multi


class RepackBatchExitStatusTests(unittest.TestCase):
    def run_batch(self, outcomes):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            apk_dir = root / "manager/app/build/outputs/apk/release"
            apk_dir.mkdir(parents=True)
            for arch in ("arm64-v8a", "x86_64"):
                (apk_dir / f"manager-{arch}.apk").touch()

            with (
                patch.object(sys, "argv", ["repack_apk_multi.py", "repack", "-b", "release"]),
                patch.object(repack_apk_multi.repack, "workspace_root", return_value=root),
                patch.object(repack_apk_multi, "load_config_and_merge"),
                patch.object(repack_apk_multi, "process_single_apk", side_effect=outcomes) as process,
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                result = repack_apk_multi.main()

            self.assertEqual(process.call_count, 2)
            return result

    def test_all_apks_succeed(self):
        self.assertEqual(self.run_batch([Path("arm64.apk"), Path("x86_64.apk")]), 0)

    def test_partial_failure_is_an_error(self):
        self.assertEqual(
            self.run_batch([Path("arm64.apk"), RuntimeError("ksud binary not found")]), 1
        )

    def test_all_apks_fail(self):
        self.assertEqual(
            self.run_batch([RuntimeError("missing arm64 ksud"), RuntimeError("missing x86_64 ksud")]),
            1,
        )


if __name__ == "__main__":
    unittest.main()
