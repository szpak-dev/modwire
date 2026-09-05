from modwire.architecture import ArchitectureConfig, ArchitectureFacade, ReportNode
from modwire.shared import CodeMap, QueryableCodeMap
from tests.support.service_test import ServiceTestCase


class ArchitectureTestCase(ServiceTestCase):
    def analyze(self, config: ArchitectureConfig, code_map: QueryableCodeMap) -> tuple[ReportNode, ...]:
        return self.service(ArchitectureFacade, config).analyze(code_map)

    def report[Report: ReportNode](
        self, report_type: type[Report], config: ArchitectureConfig, code_map: QueryableCodeMap
    ) -> Report:
        return next(report for report in self.analyze(config, code_map) if isinstance(report, report_type))

    def source_file(self, file_id: str) -> dict[str, object]:
        return {
            "file_id": file_id,
            "module_id": file_id.rsplit(".", 1)[0],
            "imports": [],
            "classes": [],
            "functions": [],
            "line_count": 1,
            "code_line_count": 1,
            "public_symbol_count": 0,
        }

    def queryable_map(
        self, paths: tuple[str, ...], edges: tuple[tuple[str, str | None, str, str], ...]
    ) -> QueryableCodeMap:
        files = {path: self.source_file(path) for path in paths}
        return QueryableCodeMap(
            code_map=CodeMap.model_validate(
                {
                    "language": "python",
                    "extraction": {
                        "files": files,
                        "modules": {path.rsplit(".", 1)[0]: path for path in paths},
                        "files_found": len(paths),
                        "files_excluded": 0,
                    },
                    "dependency_graph": {
                        "nodes": {path: {"id": path, "kind": "file"} for path in paths},
                        "edges": [
                            {"from_id": source, "to_id": target, "specifier": specifier,
                             "resolution": resolution, "kind": "import"}
                            for source, target, resolution, specifier in edges
                        ],
                    },
                }
            )
        )
