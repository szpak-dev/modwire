from ..support.code_map import CodeMapFactory
from ..support.service_test import ServiceTestCase


class ArchitectureTestCase(ServiceTestCase):
    def report(self, report_id, config, code_map):
        return next(item for item in self.application.analyze(code_map, config) if item.metadata.id == report_id)

    def source_file(self, file_id: str) -> dict[str, object]:
        return {}

    def queryable_map(self, paths: tuple[str, ...], edges: tuple[tuple[str, str | None, str, str], ...]):
        return CodeMapFactory.queryable({path: self.source_file(path) for path in paths}, edges)
