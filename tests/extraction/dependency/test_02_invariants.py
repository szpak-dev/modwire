import re

import pytest

from ..base_test import ExtractionTestCase


class TestDependencyInvariants(ExtractionTestCase):
    @pytest.mark.parametrize("language", ("python", "typescript", "php"))
    def test_indexed_resolution_matches_complete_scans_for_every_language(self, language: str) -> None:
        def normalize(value: str) -> str:
            parts = str(value).replace("\\", "/").strip("/").split("/")
            return "/".join(re.sub("[^a-z0-9]", "", part.casefold()) for part in parts)

        def same_suffix(left: str, right: str) -> bool:
            if not left or not right:
                return left == right
            left_parts = left.split("/")
            right_parts = right.split("/")
            shared = 0
            for left_part, right_part in zip(reversed(left_parts), reversed(right_parts)):
                if left_part != right_part:
                    break
                shared += 1
            return shared == min(len(left_parts), len(right_parts)) or shared >= 2

        root = self.repository / "tests/fixtures/syntax" / language
        request = self.application.extraction.request(language, str(root))
        extraction = self.application.cli.extract(request, self.scan_policy())
        result = self.application.extraction.generate_map(language, extraction)
        modules = [(normalize(source.module_id), file_id) for file_id, source in extraction.files.items()]
        symbols = [
            (module.rsplit("/", 1)[0] if "/" in module else "", exported.name.casefold(), file_id)
            for file_id, source in extraction.files.items()
            for module in (normalize(source.module_id),)
            for exported in source.exports
        ]
        for file_id, source in extraction.files.items():
            for actual, imported in zip(result.extraction.files[file_id].imports, source.imports, strict=True):
                specifier = normalize(imported.normalized_path)
                candidates = {target for module, target in modules if same_suffix(module, specifier)}
                if imported.crossing_type == "symbol" and imported.imported_symbols:
                    names = {symbol.name.casefold() for symbol in imported.imported_symbols}
                    parent = normalize(imported.join_key)
                    candidates.update(
                        target
                        for module_parent, symbol_name, target in symbols
                        if symbol_name in names and same_suffix(module_parent, parent)
                    )
                expected_target = next(iter(candidates)) if len(candidates) == 1 else None
                expected_resolution = (
                    "resolved"
                    if expected_target is not None
                    else "unresolved"
                    if candidates or imported.is_relative
                    else "external"
                )
                assert (actual.resolution, actual.target_file_id) == (expected_resolution, expected_target)

    def test_ambiguous_module_suffix_does_not_choose_an_arbitrary_target(self) -> None:
        result = self.extract(
            {
                "example_first/example_package/example_value.py": "class ExampleValue:\n    pass\n",
                "example_second/example_package/example_value.py": "class ExampleValue:\n    pass\n",
                "example_consumer.py": "from example_first.example_package.example_value import ExampleValue\n",
            }
        )
        edge = result.dependency_edges().first().edge
        assert edge.resolution == "unresolved"
        assert edge.to_id is None
        assert not result.tracked_dependency_edges().all()

    def test_resolves_imports_between_supplied_sources(self) -> None:
        result = self.extract(
            {
                "example_package/example_value.py": "class ExampleValue:\n    pass\n",
                "example_package/example_consumer.py": "from example_package.example_value import ExampleValue\n",
            }
        )
        edges = result.tracked_dependency_edges().all()
        assert len(edges) == 1
        assert edges[0].edge.to_id == "example_package/example_value.py"
        assert edges[0].edge.resolution == "resolved"

    def test_resolves_exported_symbol_without_matching_the_exporting_module(self) -> None:
        result = self.extract(
            {
                "example_package/example_value.py": "class ExampleValue:\n    pass\n",
                "example_consumer.py": "from example_package import ExampleValue\n",
            }
        )
        edge = result.tracked_dependency_edges().first().edge
        assert edge.to_id == "example_package/example_value.py"
        assert edge.resolution == "resolved"

    def test_external_import_has_no_tracked_target(self) -> None:
        result = self.extract({"example.py": "import json\n"})
        edge = result.external_dependency_edges().first().edge
        assert edge.specifier == "json"
        assert edge.resolution == "external"
        assert edge.to_id is None

    def test_unresolved_relative_import_remains_queryable(self) -> None:
        result = self.extract({"example_package/example.py": "from .example_missing import ExampleValue\n"})
        edge = result.dependency_edges().first().edge
        assert edge.resolution == "unresolved"
        assert edge.to_id is None
