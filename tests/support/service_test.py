from collections.abc import Iterator
from contextlib import ExitStack
from types import ModuleType

import pytest
from wireup import create_sync_container

import modwire
from modwire.application import ModwireApplication

from .base_test import BaseTestCase


class ServiceTestCase(BaseTestCase):
    application: ModwireApplication
    _cleanup: ExitStack

    @pytest.fixture(autouse=True)
    def _service_lifecycle(self) -> Iterator[None]:
        with ExitStack() as cleanup:
            self._cleanup = cleanup
            self.application = self.consumer_service(ModwireApplication, ())
            yield

    def consumer_service[Service](self, interface: type[Service], consumers: tuple[ModuleType, ...]) -> Service:
        container = create_sync_container(injectables=[modwire, *consumers])
        self._cleanup.callback(container.close)
        return container.get(interface)

    def example_configuration(self):
        return self.application.configure({"shape": {"realms": [{"name": "example-source", "match": "src"}]}})
