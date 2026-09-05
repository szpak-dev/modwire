from pathlib import Path

from wireup import create_sync_container

import modwire
from modwire.cli.facade import CliFacade

if __name__ == "__main__":
    container = create_sync_container(injectables=[modwire], config={"source_root": Path.cwd(), "architecture": None})
    try:
        raise SystemExit(container.get(CliFacade).parse_python_command())
    finally:
        container.close()
