"""BCS-ARCH-001 clean-break contract: old --preset is gone (LC)."""
from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path


TEST_PDF = Path(r"C:\Users\Rowdy Payton\Desktop\PDFTest Files\1015 - Rev 0.pdf")


class TestCleanBreak(unittest.TestCase):
    """``--preset`` must have been deleted per BCS-ARCH-001 -- no shim."""

    @unittest.skipUnless(TEST_PDF.is_file(), f"Test PDF not available: {TEST_PDF}")
    def test_old_preset_flag_errors_out(self) -> None:
        cmd = [
            sys.executable,
            "-m",
            "librecad_pdf_importer.cli",
            str(TEST_PDF),
            "--preset",
            "shop",
        ]
        result = subprocess.run(
            cmd,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(
            result.returncode,
            0,
            msg="--preset should be rejected; it was accepted instead",
        )
        combined = (result.stdout + result.stderr).lower()
        self.assertTrue(
            "unrecognized arguments" in combined or "--preset" in combined,
            msg=f"Unexpected error output: {combined!r}",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
