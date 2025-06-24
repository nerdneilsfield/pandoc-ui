#!/usr/bin/env python3
"""
Windows pandoc detection debugging script.
Run this on Windows if pandoc is not being detected properly.
"""

import os
import platform
import shutil
from pathlib import Path


def main():
    """Debug pandoc detection on Windows."""
    print("🔧 Windows Pandoc Detection Debug")
    print("=" * 40)

    if platform.system().lower() != "windows":
        print("ℹ️  This script is for Windows. Current OS:", platform.system())
        return

    # Test shutil.which
    print("1. Testing shutil.which:")
    for cmd in ["pandoc", "pandoc.exe"]:
        result = shutil.which(cmd)
        print(f"   {cmd}: {'✅ ' + result if result else '❌ Not found'}")

    # Check common locations
    print("\n2. Checking common installation locations:")
    locations = [
        Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "Pandoc" / "pandoc.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"))
        / "Pandoc"
        / "pandoc.exe",
        Path("C:\\ProgramData\\chocolatey\\bin\\pandoc.exe"),
    ]

    if "USERPROFILE" in os.environ:
        userprofile = Path(os.environ["USERPROFILE"])
        locations.append(userprofile / "scoop" / "shims" / "pandoc.exe")

    for location in locations:
        status = "✅ Found" if location.exists() else "❌ Not found"
        print(f"   {status}: {location}")

    # Test our detection
    print("\n3. Testing pandoc-ui detection:")
    try:
        from pandoc_ui.infra.pandoc_detector import PandocDetector

        detector = PandocDetector()
        result = detector.detect()

        print(f"   Path: {result.path}")
        print(f"   Version: {result.version}")
        print(f"   Available: {'✅ Yes' if result.available else '❌ No'}")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n💡 If pandoc is not found:")
    print("   1. Install from: https://pandoc.org/installing.html")
    print("   2. Restart your terminal after installation")
    print("   3. Verify with: pandoc --version")


if __name__ == "__main__":
    main()
