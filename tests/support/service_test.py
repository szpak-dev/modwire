from collections.abc import Iterator
from contextlib import ExitStack
from types import ModuleType

import pytest
from wireup import create_sync_container

import modwire
from modwire.architecture import ArchitectureConfig

from .base_test import BaseTestCase


class ServiceTestCase(BaseTestCase):
    _cleanup: ExitStack

    @pytest.fixture(autouse=True)
    def _service_lifecycle(self) -> Iterator[None]:
        with ExitStack() as cleanup:
            self._cleanup = cleanup
            yield

    def service[Service](self, interface: type[Service], configuration: ArchitectureConfig) -> Service:
        return self.consumer_service(interface, configuration, ())

    def consumer_service[Service](
        self, interface: type[Service], configuration: ArchitectureConfig, consumers: tuple[ModuleType, ...]
    ) -> Service:
        container = create_sync_container(
            injectables=[modwire, *consumers],
            config={"architecture": configuration},
        )
        self._cleanup.callback(container.close)
        return container.get(interface)

    def example_configuration(self) -> ArchitectureConfig:
        return ArchitectureConfig.model_validate(
            {"shape": {"realms": [{"name": "example-source", "match": "src"}]}},
        )
