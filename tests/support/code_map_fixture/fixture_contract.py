from pathlib import Path

from modwire.application import CodeMap


class PolyglotFixtureContract:
    def languages(self, root: Path) -> tuple[str, ...]:
        return tuple(sorted(path.name for path in root.iterdir() if path.is_dir()))

    def source_paths(self, root: Path) -> tuple[str, ...]:
        return tuple(sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()))

    def projected_model_fields(self, code_map: CodeMap) -> dict[str, frozenset[str]]:
        source_file = next(iter(code_map.extraction.files.values()))
        declaration = source_file.declarations[0]
        method = declaration.methods[0]
        artifact = code_map.extraction.manifest.sources[0]
        node = next(iter(code_map.dependency_graph.nodes.values()))
        edge = code_map.dependency_graph.edges[0]
        models = (
            code_map,
            code_map.producer,
            code_map.producer.extractor,
            code_map.extraction,
            source_file,
            declaration,
            method,
            code_map.extraction.manifest,
            code_map.extraction.manifest.runtime,
            artifact,
            code_map.dependency_graph,
            node,
            edge,
        )
        return {type(model).__name__: frozenset(type(model).model_fields) for model in models}
