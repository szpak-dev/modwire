from ..support.service_test import ServiceTestCase


class ExtractionTestCase(ServiceTestCase):
    def extract(self, files: dict[str, str]):
        return self.application.generate_queryable_map("python", self.project(files), self.scan_policy())
