from ..support.service_test import ServiceTestCase


class ArchitectureTestCase(ServiceTestCase):
    def report(self, report_id, config, code_map):
        return next(item for item in self.application.analyze(code_map, config) if item.metadata.id == report_id)

    def source_file(self, file_id: str) -> str:
        return "class ExampleSource:\n    pass\n"

    def queryable_map(self, paths: tuple[str, ...], edges: tuple[tuple[str, str | None, str, str], ...]):
        sources = {path: self.source_file(path) for path in paths}
        for source, target, resolution, specifier in edges:
            if target is not None:
                module = target.removesuffix(".py").replace("/", ".")
                statement = f"from {module} import ExampleSource\n"
            elif resolution == "external":
                statement = f"import {specifier}\n"
            else:
                statement = "from .example_missing import ExampleSource\n"
            sources[source] = statement + sources[source]
        return self.application.generate_queryable_map("python", self.project(sources), ())
