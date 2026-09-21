import pytest

from .base_test import BoundaryTestCase


class TestFlowPaths(BoundaryTestCase):
    @pytest.mark.parametrize("reverse", (False, True))
    def test_layer_order_distinguishes_forward_and_backward_edges(self, reverse: bool) -> None:
        config = self.application.configure(
            {
                "boundaries": {
                    "tags": [
                        {"name": "example-entry", "match": "src/example_entry"},
                        {"name": "example-core", "match": "src/example_core"},
                    ],
                    "flow": {
                        "layers": ["example-entry", "example-core"],
                        "analyzers": ["backward-flow"],
                    },
                },
                "shape": {"realms": [{"name": "example-source", "match": "src"}]},
            }
        )
        paths = ("src/example_entry/example_entry.source", "src/example_core/example_core.source")
        source, target = tuple(reversed(paths)) if reverse else paths
        result = self.violations(config, source, target)
        assert result == ((source, target),) if reverse else result == ()

    @pytest.mark.parametrize("reenters", (False, True))
    def test_reentry_reports_the_complete_dependency_path(self, reenters: bool) -> None:
        config = self.application.configure(
            {
                "boundaries": {
                    "tags": [{"name": "example-module", "match": "src/*"}],
                    "flow": {"module_tag": "example-module", "analyzers": ["no-reentry"]},
                },
                "shape": {"realms": [{"name": "example-source", "match": "src"}]},
            }
        )
        target_module = "example_first" if reenters else "example_third"
        paths = (
            "src/example_first/example_entry.source",
            "src/example_second/example_middle.source",
            f"src/{target_module}/example_target.source",
        )
        edges = tuple((paths[a], paths[b], "resolved", "example.target") for a, b in ((0, 1), (1, 2)))
        report = self.report("architecture.violations.flow", config, self.queryable_map(paths, edges))
        assert tuple(item.path for item in report.violations) == ((paths,) if reenters else ())
        if reenters:
            assert report.violations[0].violation_index == 2
            assert report.violations[0].violation_type == "no-reentry"

    def test_cycles_are_reported_once_without_a_graph_root(self) -> None:
        config = self.application.configure(
            {
                "boundaries": {
                    "tags": [{"name": "example-module", "match": "src/*"}],
                    "flow": {"module_tag": "example-module", "analyzers": ["no-cycles"]},
                },
                "shape": {"realms": [{"name": "example-source", "match": "src"}]},
            }
        )
        paths = ("src/example_first/example_first.source", "src/example_second/example_second.source")
        edges = tuple((paths[a], paths[b], "resolved", "example.target") for a, b in ((0, 1), (1, 0)))
        report = self.report("architecture.violations.flow", config, self.queryable_map(paths, edges))
        assert tuple(item.path for item in report.violations) == (("example_first", "example_second", "example_first"),)
