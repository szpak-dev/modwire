from concurrent.futures import ThreadPoolExecutor

from modwire.application import CacheOptions, CacheStage

from .base_test import ApplicationTestCase


class TestPersistentCache(ApplicationTestCase):
    def test_public_map_diagnostics_distinguish_cold_and_warm_cache_stages(self) -> None:
        root = self.project({"src/example.py": "def example_function():\n    return 1\n"})
        options = self.cache_options("example-diagnostics")

        cold = self.application.generate_map_cached_with_diagnostics("python", root, self.scan_policy(), options)
        warm = self.application.generate_map_cached_with_diagnostics("python", root, self.scan_policy(), options)

        assert cold.value == warm.value
        assert cold.outcome(CacheStage.EXTRACTION).to_dict() == {
            "stage": "extraction",
            "namespace": "example-diagnostics",
            "hits": 0,
            "misses": 1,
            "invalidated": 0,
            "computed": 1,
            "stored": 1,
        }
        assert cold.outcome(CacheStage.CODE_MAP).to_dict() == {
            "stage": "code-map",
            "namespace": "example-diagnostics",
            "hits": 0,
            "misses": 1,
            "invalidated": 0,
            "computed": 1,
            "stored": 1,
        }
        assert warm.outcome(CacheStage.EXTRACTION).hits == 1
        assert warm.outcome(CacheStage.EXTRACTION).misses == 0
        assert warm.outcome(CacheStage.CODE_MAP).hits == 1
        assert warm.outcome(CacheStage.CODE_MAP).misses == 0

    def test_public_map_diagnostics_report_partial_source_reuse(self) -> None:
        root = self.project(
            {
                "src/example_first.py": "def example_first():\n    return 1\n",
                "src/example_second.py": "def example_second():\n    return 2\n",
            }
        )
        options = self.cache_options("example-partial-diagnostics")
        self.application.generate_map_cached_with_diagnostics("python", root, self.scan_policy(), options)
        (root / "src/example_second.py").write_text("def example_changed():\n    return 2\n", encoding="utf-8")

        changed = self.application.generate_map_cached_with_diagnostics("python", root, self.scan_policy(), options)

        extraction = changed.outcome(CacheStage.EXTRACTION)
        code_map = changed.outcome(CacheStage.CODE_MAP)
        assert (extraction.hits, extraction.misses, extraction.computed, extraction.stored) == (1, 1, 1, 1)
        assert extraction.invalidated == 0
        assert (code_map.hits, code_map.misses, code_map.computed, code_map.stored) == (0, 1, 1, 1)

    def test_public_map_diagnostics_report_invalidated_entries(self) -> None:
        root = self.project({"src/example.py": "class ExampleValue:\n    pass\n"})
        options = self.cache_options("example-invalidated-diagnostics")
        expected = self.application.generate_map_cached_with_diagnostics("python", root, self.scan_policy(), options)
        for path in (self.workspace / "cache").rglob("*.cache"):
            path.write_bytes(b"not-a-cache-entry")

        recovered = self.application.generate_map_cached_with_diagnostics("python", root, self.scan_policy(), options)

        assert recovered.value == expected.value
        assert recovered.outcome(CacheStage.EXTRACTION).invalidated == 1
        assert recovered.outcome(CacheStage.EXTRACTION).misses == 1
        assert recovered.outcome(CacheStage.CODE_MAP).invalidated == 1
        assert recovered.outcome(CacheStage.CODE_MAP).misses == 1

    def test_public_report_diagnostics_distinguish_cold_and_warm_results(self) -> None:
        root = self.project({"src/example.py": "def example_function():\n    return 1\n"})
        options = self.cache_options("example-report-diagnostics")
        code_map = self.application.generate_queryable_map_cached("python", root, self.scan_policy(), options)
        config = self.example_configuration()

        cold = self.application.analyze_cached_with_diagnostics(code_map, config, options)
        warm = self.application.analyze_cached_with_diagnostics(code_map, config, options)

        assert cold.value == warm.value
        assert cold.outcome(CacheStage.REPORTS).to_dict() == {
            "stage": "reports",
            "namespace": "example-report-diagnostics",
            "hits": 0,
            "misses": 1,
            "invalidated": 0,
            "computed": 1,
            "stored": 1,
        }
        assert warm.outcome(CacheStage.REPORTS).hits == 1
        assert warm.outcome(CacheStage.REPORTS).misses == 0

    def test_warm_code_map_matches_the_uncached_public_result(self) -> None:
        root = self.project({"src/example.py": "def example_function():\n    return 1\n"})
        options = self.cache_options("example-warm")

        expected = self.application.generate_map("python", root, self.scan_policy())
        cold = self.application.generate_map_cached("python", root, self.scan_policy(), options)
        warm = self.application.generate_map_cached("python", root, self.scan_policy(), options)

        assert cold == expected
        assert warm == expected
        assert tuple((self.workspace / "cache").rglob("*.cache"))

    def test_same_size_edit_invalidates_cached_source_content(self) -> None:
        root = self.project({"src/example.py": "def example_one():\n    return 1\n"})
        options = self.cache_options("example-edit")
        before = self.application.generate_queryable_map_cached("python", root, self.scan_policy(), options)

        (root / "src/example.py").write_text("def example_two():\n    return 1\n", encoding="utf-8")
        after = self.application.generate_queryable_map_cached("python", root, self.scan_policy(), options)

        assert before.functions().first().item.name == "example_one"
        assert after.functions().first().item.name == "example_two"

    def test_manifest_changes_track_additions_deletions_and_renames(self) -> None:
        root = self.project({"src/example_first.py": "class ExampleFirst:\n    pass\n"})
        options = self.cache_options("example-manifest")
        first = self.application.generate_queryable_map_cached("python", root, self.scan_policy(), options)

        (root / "src/example_first.py").rename(root / "src/example_renamed.py")
        (root / "src/example_second.py").write_text("class ExampleSecond:\n    pass\n", encoding="utf-8")
        changed = self.application.generate_queryable_map_cached("python", root, self.scan_policy(), options)
        (root / "src/example_renamed.py").unlink()
        final = self.application.generate_queryable_map_cached("python", root, self.scan_policy(), options)

        assert first.source_ids() == ("src/example_first.py",)
        assert changed.source_ids() == ("src/example_renamed.py", "src/example_second.py")
        assert final.source_ids() == ("src/example_second.py",)

    def test_manifest_change_rebuilds_import_resolution_for_unchanged_sources(self) -> None:
        root = self.project(
            {
                "example_package/example_value.py": "class ExampleValue:\n    pass\n",
                "example_package/example_consumer.py": ("from example_package.example_value import ExampleValue\n"),
            }
        )
        options = self.cache_options("example-resolution")
        before = self.application.generate_queryable_map_cached("python", root, self.scan_policy(), options)

        (root / "example_package/example_value.py").unlink()
        after = self.application.generate_queryable_map_cached("python", root, self.scan_policy(), options)

        assert before.dependency_edges().first().edge.resolution == "resolved"
        assert after.dependency_edges().first().edge.resolution != "resolved"
        assert after.dependency_edges().first().edge.to_id is None

    def test_corrupt_entries_recover_as_cache_misses(self) -> None:
        root = self.project({"src/example.py": "class ExampleValue:\n    pass\n"})
        options = self.cache_options("example-corruption")
        expected = self.application.generate_map_cached("python", root, self.scan_policy(), options)
        for path in (self.workspace / "cache").rglob("*.cache"):
            path.write_bytes(b"not-a-cache-entry")

        recovered = self.application.generate_map_cached("python", root, self.scan_policy(), options)

        assert recovered == expected

    def test_reports_are_identical_across_cold_warm_and_uncached_paths(self) -> None:
        root = self.project({"src/example.py": "def example_function():\n    return 1\n"})
        options = self.cache_options("example-reports")
        code_map = self.application.generate_queryable_map_cached("python", root, self.scan_policy(), options)
        config = self.example_configuration()

        expected = self.application.analyze(code_map, config)
        cold = self.application.analyze_cached(code_map, config, options)
        warm = self.application.analyze_cached(code_map, config, options)

        assert cold == expected
        assert warm == expected

    def test_effective_configuration_change_invalidates_cached_reports(self) -> None:
        root = self.project({"src/example.py": "def example_function():\n    return 1\n"})
        options = self.cache_options("example-configuration")
        code_map = self.application.generate_queryable_map_cached("python", root, self.scan_policy(), options)
        strict = self.application.configure({"shape": {"realms": [{"name": "example-source", "match": "src"}]}})
        permissive = self.application.configure(
            {"shape": {"realms": [{"name": "example-source", "match": "src", "shape": {"max_functions_per_file": 1}}]}}
        )

        strict_reports = self.application.analyze_cached(code_map, strict, options)
        permissive_reports = self.application.analyze_cached(code_map, permissive, options)

        assert strict_reports == self.application.analyze(code_map, strict)
        assert permissive_reports == self.application.analyze(code_map, permissive)
        assert strict_reports != permissive_reports

    def test_concurrent_requests_never_expose_partial_entries(self) -> None:
        root = self.project({"src/example.py": "class ExampleValue:\n    pass\n"})
        options = self.cache_options("example-concurrent")

        with ThreadPoolExecutor(max_workers=4) as executor:
            results = tuple(
                executor.map(
                    lambda _: self.application.generate_map_cached("python", root, self.scan_policy(), options),
                    range(4),
                )
            )

        assert all(result == results[0] for result in results[1:])

    def test_clear_removes_only_the_selected_cache_namespace(self) -> None:
        root = self.project({"src/example.py": "class ExampleValue:\n    pass\n"})
        selected = self.cache_options("example-selected")
        retained = self.cache_options("example-retained")
        self.application.generate_map_cached("python", root, self.scan_policy(), selected)
        self.application.generate_map_cached("python", root, self.scan_policy(), retained)
        before = set((self.workspace / "cache").rglob("*.cache"))

        self.application.clear_cache(selected)

        after = set((self.workspace / "cache").rglob("*.cache"))
        assert root.joinpath("src/example.py").is_file()
        assert after
        assert after < before

    def test_storage_limit_is_enforced_after_each_public_operation(self) -> None:
        root = self.project({"src/example.py": "class ExampleValue:\n    pass\n"})
        options = CacheOptions(directory=str(self.workspace / "cache"), namespace="example-limit", max_bytes=1)

        result = self.application.generate_map_cached("python", root, self.scan_policy(), options)

        assert result.extraction.files
        assert sum(path.stat().st_size for path in (self.workspace / "cache").rglob("*.cache")) <= 1

    def cache_options(self, namespace: str) -> CacheOptions:
        return CacheOptions(directory=str(self.workspace / "cache"), namespace=namespace, max_bytes=10_000_000)
