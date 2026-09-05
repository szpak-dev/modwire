import pytest

from ..base_test import ArchitectureTestCase


class TestArchitecturePatterns(ArchitectureTestCase):
    @pytest.mark.parametrize(
        ("pattern", "included", "excluded"),
        (
            ("src/*/services", "src/example_one/services/example.py", "src/example_one/models/example.py"),
            ("src/**/services", "src/example_one/example_two/services/example.py", "src/example_one/models/example.py"),
            ("src/example_?", "src/example_a/example.py", "src/example_long/example.py"),
            ("src/example_[ab]", "src/example_a/example.py", "src/example_c/example.py"),
            ("src/example_[!a]", "src/example_b/example.py", "src/example_a/example.py"),
            ("src/example_module", "src/example_module/example.py", "src/example_module_extra/example.py"),
            ("src/*/example.py", "src/example_module/example.py", "src/example_module/nested/example.py"),
        ),
    )
    def test_glob_tags_include_only_the_intended_paths(self, pattern: str, included: str, excluded: str) -> None:
        config = self.application.configure(
            {
                "boundaries": {
                    "tags": [{"name": "example-module", "match": pattern}],
                    "flow": {"module_tag": "example-module"},
                },
                "shape": {"realms": [{"name": "example-source", "match": "src"}]},
            }
        )
        result = self.report("architecture.map", config, self.queryable_map((included, excluded), ()))
        assert result.unknown_files == (excluded,)
        assert tuple(source for module in result.modules for source in module.source_ids) == (included,)

    def test_tag_exclusions_keep_package_files_out_of_module_capture(self) -> None:
        config = self.application.configure(
            {
                "boundaries": {
                    "tags": [{"name": "example-module", "match": "src/*/*", "excluded_patterns": ["src/*/*.py"]}],
                    "flow": {"module_tag": "example-module"},
                },
                "shape": {"realms": [{"name": "example-source", "match": "src"}]},
            }
        )
        paths = ("src/example_context/example_facade.py", "src/example_context/example_module/example_service.py")
        result = self.report("architecture.map", config, self.queryable_map(paths, ()))
        assert result.unknown_files == (paths[0],)
        assert tuple((module.name, module.source_ids) for module in result.modules) == (
            ("example_context/example_module", (paths[1],)),
        )
