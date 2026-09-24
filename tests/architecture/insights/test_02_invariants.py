from ...support.code_map import CodeMapFactory
from .base_test import InsightTestCase


class TestInsightInvariants(InsightTestCase):
    def test_coherence_distinguishes_roots_leaves_isolation_and_external_imports(self) -> None:
        paths = ("example_entry.source", "example_middle.source", "example_leaf.source", "example_isolated.source")
        edges = (
            (paths[0], paths[1], "resolved", "example_middle"),
            (paths[1], paths[2], "resolved", "example_leaf"),
            (paths[1], None, "external", "example_external"),
        )
        result = self.insight(dict.fromkeys(paths, {}), edges).coherence
        assert result.roots == ("example_entry.source", "example_isolated.source")
        assert result.leaves == ("example_isolated.source", "example_leaf.source")
        assert result.isolated == ("example_isolated.source",)
        assert result.external_dependencies == ("example_external",)

    def test_hotspots_rank_dependency_pressure_and_break_ties_by_path(self) -> None:
        paths = ("example_first.source", "example_second.source", "example_target.source")
        edges = (
            (paths[0], paths[2], "resolved", "example_target"),
            (paths[1], paths[2], "resolved", "example_target"),
        )
        result = self.insight(dict.fromkeys(paths, {}), edges).hotspots
        assert tuple((item.source_id, item.incoming_count, item.outgoing_count) for item in result.hotspots) == (
            ("example_target.source", 2, 0),
            ("example_first.source", 0, 1),
            ("example_second.source", 0, 1),
        )

    def test_unused_exports_do_not_include_imported_symbols(self) -> None:
        result = self.insight(
            {
                "example_values.source": {
                    "exports": [
                        CodeMapFactory().source_export("ExampleUsed"),
                        CodeMapFactory().source_export("ExampleUnused"),
                    ]
                },
                "example_consumer.source": {
                    "imports": [
                        CodeMapFactory().source_import(
                            "example_values",
                            imported_name="ExampleUsed",
                            is_aliased=False,
                            imported_symbols=(),
                        )
                    ]
                },
            },
            (),
        ).exports
        assert tuple((item.source_id, item.name) for item in result.unused_exports) == (
            ("example_values.source", "ExampleUnused"),
        )

    def test_callable_report_links_local_calls_and_deduplicates_repeated_calls(self) -> None:
        source_id = "example.source"
        result = self.insight(
            {
                source_id: {
                    "callables": [
                        CodeMapFactory().source_callable(source_id, "example_target"),
                        CodeMapFactory().source_callable(source_id, "example_caller"),
                    ],
                    "calls": [
                        CodeMapFactory().source_call(source_id, "example_caller", "example_target"),
                        CodeMapFactory().source_call(source_id, "example_caller", "example_target"),
                    ],
                }
            },
            (),
        ).callables
        entries = {item.source_callable: item for item in result.entries}
        caller = next(item for key, item in entries.items() if key.endswith("example_caller"))
        target = next(item for key, item in entries.items() if key.endswith("example_target"))
        assert caller.calls == (target.source_callable,)
        assert target.callers == (caller.source_callable,)
        assert target.calls == ()

    def test_empty_project_has_empty_insights(self) -> None:
        result = self.insight({}, ())
        assert result.clusters.clusters == ()
        assert result.hotspots.hotspots == ()
        assert result.callables.entries == ()
        assert result.exports.unused_exports == ()
        assert result.coherence.roots == result.coherence.leaves == result.coherence.isolated == ()
