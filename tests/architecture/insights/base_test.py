from ...support.code_map import CodeMapFactory
from ..base_test import ArchitectureTestCase


class InsightTestCase(ArchitectureTestCase):
    def insight(
        self,
        files: dict[str, dict[str, object]],
        edges: tuple[tuple[str, str | None, str, str], ...],
    ):
        code_map = CodeMapFactory().queryable(files, edges)
        return self.report("architecture.insights", self.example_configuration(), code_map)
