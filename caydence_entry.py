"""
Standalone executable entrypoint for Caydence Windows binary.
"""
import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from modules.cli import main

if __name__ == "__main__":
    main()
