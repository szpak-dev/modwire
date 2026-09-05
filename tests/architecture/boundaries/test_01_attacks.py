import pytest

from .base_test import BoundaryTestCase


class TestBoundaryAttacks(BoundaryTestCase):
    @pytest.mark.parametrize(
        ("source", "target", "denied"),
        (
            ("src/example_one/example_a/service.py", "src/example_one/example_b/service.py", True),
            ("src/example_one/example_a/service.py", "src/example_one/example_a/other.py", False),
        ),
    )
    def test_a_shared_context_cannot_bypass_a_module_boundary(self, source: str, target: str, denied: bool) -> None:
        config = self.application.configure(
            {
                "boundaries": {
                    "tags": [
                        {"name": "example-context", "match": "src/*"},
                        {"name": "example-module", "match": "src/*/*"},
                    ],
                    "flow": {
                        "realms": [
                            {"name": "example-contexts", "module_tag": "example-context"},
                            {"name": "example-modules", "module_tag": "example-module"},
                        ],
                        "analyzers": ["module-boundaries"],
                    },
                },
                "shape": {"realms": [{"name": "example-source", "match": "src"}]},
            }
        )
        assert bool(self.violations(config, source, target)) is denied

    def test_unclassified_source_cannot_reach_a_closed_module(self) -> None:
        config = self.application.configure(
            {
                "boundaries": {
                    "tags": [{"name": "example-module", "match": "src/*"}],
                    "flow": {"module_tag": "example-module", "analyzers": ["module-boundaries"]},
                },
                "shape": {"realms": [{"name": "example-source", "match": "src"}]},
            }
        )
        paths = self.violations(config, "example_tool.py", "src/example_module/example.py")
        assert ("example_tool.py",) in paths
        assert ("example_tool.py", "src/example_module/example.py") in paths
