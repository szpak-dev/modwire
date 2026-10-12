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
