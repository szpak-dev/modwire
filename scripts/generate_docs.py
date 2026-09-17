import sys
from pathlib import Path

from modwire.application import ModwireApplication

if __name__ == "__main__":
    raise SystemExit(ModwireApplication.create().generate_documentation(Path("README.md"), "--check" in sys.argv))
