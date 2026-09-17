from .base_test import InsightTestCase


class TestInsightInvariants(InsightTestCase):
    def test_coherence_distinguishes_roots_leaves_isolation_and_external_imports(self) -> None:
        result = self.insight(
            {
                "example_entry.py": "import example_middle\n",
                "example_middle.py": "import example_leaf\nimport json\n",
                "example_leaf.py": "class ExampleLeaf: pass\n",
                "example_isolated.py": "class ExampleIsolated: pass\n",
            }
        ).coherence
        assert result.roots == ("example_entry.py", "example_isolated.py")
        assert result.leaves == ("example_isolated.py", "example_leaf.py")
        assert result.isolated == ("example_isolated.py",)
        assert result.external_dependencies == ("json",)

    def test_hotspots_rank_dependency_pressure_and_break_ties_by_path(self) -> None:
        result = self.insight(
            {
                "example_first.py": "import example_target\n",
                "example_second.py": "import example_target\n",
                "example_target.py": "class ExampleTarget: pass\n",
            }
        ).hotspots
        assert tuple((item.source_id, item.incoming_count, item.outgoing_count) for item in result.hotspots) == (
            ("example_target.py", 2, 0),
            ("example_first.py", 0, 1),
            ("example_second.py", 0, 1),
        )

    def test_unused_exports_do_not_include_imported_symbols(self) -> None:
        result = self.insight(
            {
                "example_values.py": "class ExampleUsed: pass\nclass ExampleUnused: pass\n",
                "example_consumer.py": "from example_values import ExampleUsed\n",
            }
        ).exports
        assert tuple((item.source_id, item.name) for item in result.unused_exports) == (
            ("example_values.py", "ExampleUnused"),
        )

    def test_callable_report_links_local_calls_and_deduplicates_repeated_calls(self) -> None:
        result = self.insight(
            {
                "example.py": "def example_target(): pass\ndef example_caller():\n"
                "    example_target()\n    example_target()\n"
            }
        ).callables
        entries = {item.source_callable: item for item in result.entries}
        caller = next(item for key, item in entries.items() if key.endswith("example_caller"))
        target = next(item for key, item in entries.items() if key.endswith("example_target"))
        assert caller.calls == (target.source_callable,)
        assert target.callers == (caller.source_callable,)
        assert target.calls == ()

    def test_empty_project_has_empty_insights(self) -> None:
        result = self.insight({})
        assert result.clusters.clusters == ()
        assert result.hotspots.hotspots == ()
        assert result.callables.entries == ()
        assert result.exports.unused_exports == ()
        assert result.coherence.roots == result.coherence.leaves == result.coherence.isolated == ()
