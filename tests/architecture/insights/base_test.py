from ..base_test import ArchitectureTestCase


class InsightTestCase(ArchitectureTestCase):
    def insight(self, sources: dict[str, str]):
        code_map = self.application.generate_queryable_map("python", self.project(sources), self.scan_policy())
        return self.report("architecture.insights", self.example_configuration(), code_map)
