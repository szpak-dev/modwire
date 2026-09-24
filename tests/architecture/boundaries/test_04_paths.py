import time

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
            assert report.violations[0].source_module == "example_second"
            assert report.violations[0].target_module == "example_first"

    def test_reentry_analysis_bounds_converging_dependency_paths(self) -> None:
        config = self.application.configure(
            {
                "boundaries": {
                    "tags": [{"name": "example-module", "match": "src/*"}],
                    "flow": {"module_tag": "example-module", "analyzers": ["no-reentry"]},
                },
                "shape": {"realms": [{"name": "example-source", "match": "src"}]},
            }
        )
        paths = ["src/example_module/example_root.source"]
        levels: list[tuple[str, str]] = []
        for level in range(18):
            nodes = (
                f"src/example_module/example_{level}_a.source",
                f"src/example_module/example_{level}_b.source",
            )
            paths.extend(nodes)
            levels.append(nodes)
        paths.append("src/example_module/example_target.source")
        edges: list[tuple[str, str | None, str, str]] = []
        previous = (paths[0],)
        for current in levels:
            edges.extend((source, target, "resolved", "example.target") for source in previous for target in current)
            previous = current
        edges.extend((source, paths[-1], "resolved", "example.target") for source in previous)
        code_map = self.queryable_map(tuple(paths), tuple(edges))
        started = time.perf_counter()
        report = self.report("architecture.violations.flow", config, code_map)
        elapsed = time.perf_counter() - started
        assert not report.violations
        assert elapsed < 1.0

    def test_reentry_analysis_preserves_distinct_states_across_repeated_dependencies_and_cycles(self) -> None:
        config = self.application.configure(
            {
                "boundaries": {
                    "tags": [{"name": "example-module", "match": "src/*"}],
                    "flow": {"module_tag": "example-module", "analyzers": ["no-reentry"]},
                },
                "shape": {"realms": [{"name": "example-source", "match": "src"}]},
            }
        )
        root = "src/example_entry/example_root.source"
        first = "src/example_first/example_branch.source"
        second = "src/example_second/example_branch.source"
        shared = "src/example_shared/example_shared.source"
        first_target = "src/example_first/example_target.source"
        second_target = "src/example_second/example_target.source"
        loop_one = "src/example_entry/example_loop_one.source"
        loop_two = "src/example_entry/example_loop_two.source"
        paths = (root, first, second, shared, first_target, second_target, loop_one, loop_two)
        edges = (
            (root, first, "resolved", "example.first"),
            (root, first, "resolved", "example.first"),
            (root, second, "resolved", "example.second"),
            (first, shared, "resolved", "example.shared"),
            (second, shared, "resolved", "example.shared"),
            (shared, first_target, "resolved", "example.first_target"),
            (shared, second_target, "resolved", "example.second_target"),
            (root, loop_one, "resolved", "example.loop_one"),
            (loop_one, loop_two, "resolved", "example.loop_two"),
            (loop_two, loop_one, "resolved", "example.loop_one"),
        )
        report = self.report("architecture.violations.flow", config, self.queryable_map(paths, edges))
        assert tuple(
            (violation.path, violation.violation_index, violation.source_module, violation.target_module)
            for violation in report.violations
        ) == (
            ((root, first, shared, first_target), 3, "example_shared", "example_first"),
            ((root, second, shared, second_target), 3, "example_shared", "example_second"),
        )

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
