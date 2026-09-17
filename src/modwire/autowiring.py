import sys

import wireup

import modwire

from .application import ModwireApplication


def main() -> int:
    """Run the installed Modwire command."""
    try:
        return container.get(ModwireApplication).run(sys.argv[1:])
    finally:
        container.close()


def parser_main(language: str) -> int:
    """Run a bundled extractor command."""
    try:
        return container.get(ModwireApplication).run_extractor(language)
    finally:
        container.close()


container = wireup.create_sync_container(injectables=[modwire])
