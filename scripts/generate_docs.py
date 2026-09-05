import sys
from pathlib import Path

from modwire.application import ModwireApplication
from modwire.autowiring import container

if __name__ == "__main__":
    try:
        raise SystemExit(
            container.get(ModwireApplication).generate_documentation(Path("README.md"), "--check" in sys.argv)
        )
    finally:
        container.close()
