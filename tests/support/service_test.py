from collections.abc import Iterator

import pytest

from modwire.application import ModwireApplication, ScanPolicy

from .base_test import BaseTestCase


class ServiceTestCase(BaseTestCase):
    application: ModwireApplication

    @pytest.fixture(autouse=True)
    def _service_lifecycle(self) -> Iterator[None]:
        self.application = ModwireApplication.create()
        yield

    def example_configuration(self):
        return self.application.configure({"shape": {"realms": [{"name": "example-source", "match": "src"}]}})

    def scan_policy(self) -> ScanPolicy:
        return ScanPolicy()

    def configured_scan_policy(self, excluded_patterns: tuple[str, ...], follow_symlinks: bool) -> ScanPolicy:
        return ScanPolicy(excluded_patterns=excluded_patterns, follow_symlinks=follow_symlinks)
