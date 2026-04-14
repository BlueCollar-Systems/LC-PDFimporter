"""Locate and launch LibreCAD for generated DXF files."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
from typing import Optional, Tuple


def find_librecad_executable() -> Optional[str]:
    candidates = []

    if os.name == "nt":
        candidates.extend([
            r"C:\Program Files\LibreCAD\librecad.exe",
            r"C:\Program Files (x86)\LibreCAD\librecad.exe",
        ])
    else:
        candidates.extend([
            "/usr/bin/librecad",
            "/usr/local/bin/librecad",
            "/Applications/LibreCAD.app/Contents/MacOS/LibreCAD",
        ])

    for candidate in candidates:
        if Path(candidate).is_file():
            return candidate
    return None


def launch_librecad(dxf_path: str, executable: Optional[str] = None) -> Tuple[bool, str]:
    exe = executable or find_librecad_executable()
    if not exe:
        return False, "LibreCAD executable not found."

    dxf = str(Path(dxf_path).expanduser().resolve())

    # Kill any existing LibreCAD instances first — if LC is already running,
    # passing a file arg to a new process often fails silently (the new process
    # exits and tries IPC to the existing instance, which may not work).
    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/f", "/im", "librecad.exe"],
                capture_output=True, timeout=5
            )
        except Exception:
            pass
    import time
    time.sleep(0.5)

    try:
        subprocess.Popen([exe, dxf])
        return True, f"Launched LibreCAD: {exe}"
    except (OSError, ValueError) as exc:
        return False, f"Failed to launch LibreCAD: {exc}"
