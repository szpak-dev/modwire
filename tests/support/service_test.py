from collections.abc import Iterator

import pytest

from modwire.application import ModwireApplication

from .base_test import BaseTestCase


class ServiceTestCase(BaseTestCase):
    application: ModwireApplication

    @pytest.fixture(autouse=True)
    def _service_lifecycle(self) -> Iterator[None]:
        self.application = ModwireApplication.create()
        yield

    def example_configuration(self):
        return self.application.configure({"shape": {"realms": [{"name": "example-source", "match": "src"}]}})
