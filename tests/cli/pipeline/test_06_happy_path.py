from ..base_test import CliTestCase


class TestParallelExtractionHappyPath(CliTestCase):
    def test_parallel_threshold_preserves_source_facts_and_canonical_output(self) -> None:
        serial_names = tuple(f"example_{index:04d}.py" for index in range(999))
        self.write_files(
            {
                **{name: "" for name in serial_names},
                "example_0000.py": (
                    "from collections.abc import Iterable\n\n"
                    "class ExampleValue:\n"
                    "    def values(self) -> Iterable[int]:\n"
                    "        return (1, 2, 3)\n"
                ),
            }
        )
        serial = self.application.generate_map("python", self.workspace, self.scan_policy())

        parallel_names = (*serial_names, "example_0999.py")
        self.write_files({"example_0999.py": "class ExampleAdded:\n    pass\n"})
        parallel = self.application.generate_map("python", self.workspace, self.scan_policy())
        repeated = self.application.generate_map("python", self.workspace, self.scan_policy())

        assert {name: parallel.extraction.files[name] for name in serial_names} == serial.extraction.files
        assert parallel.dependency_graph.edges == serial.dependency_graph.edges
        assert tuple(parallel.extraction.files) == parallel_names
        assert tuple(source.relative_path for source in parallel.extraction.manifest.sources) == parallel_names
        assert repeated == parallel
        format = self.application.implementation_manifest_formats()[0]
        assert self.application.implementation_manifest(repeated, format) == self.application.implementation_manifest(
            parallel, format
        )


class TestReportCommands(CliTestCase):
    def test_explicit_and_legacy_commands_preserve_exit_status_and_output(self) -> None:
        self.write_project(1)
        explicit = self.run_cli(("report", "--language", "python"))
        legacy = self.run_cli(("--language", "python"))
        assert explicit.returncode == legacy.returncode == 0
        assert explicit.stdout == legacy.stdout
        assert "Architecture checks passed." in explicit.stdout

    def test_summary_omits_file_listing(self) -> None:
        self.write_project(1)
        result = self.run_cli(("report", "--language", "python", "--summary"))
        assert result.returncode == 0, result.stderr
        assert "Architecture checks passed." in result.stdout
        assert "src/example.py" not in result.stdout

    def test_violation_sets_a_nonzero_exit_status(self) -> None:
        self.write_project(0)
        result = self.run_cli(("report", "--language", "python", "--summary"))
        assert result.returncode == 1
        assert "max_functions_per_file" in result.stdout
        assert "src/example.py" in result.stdout
