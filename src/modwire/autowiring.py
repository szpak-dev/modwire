import sys

import wireup

import modwire

from .cli.facade import CliFacade


def main() -> int:
    container = wireup.create_sync_container(injectables=[modwire])
    try:
        return container.get(CliFacade).run(sys.argv[1:])
    finally:
        container.close()


def run_extractor(language: str) -> int:
    container = wireup.create_sync_container(injectables=[modwire])
    try:
        return container.get(CliFacade).run_extractor(language)
    finally:
        container.close()
