import shutil

import pytest

from ..base_test import CliTestCase


class TestParallelExtractionHappyPath(CliTestCase):
    @pytest.mark.parametrize(("language", "extension"), (("python", "py"), ("ruby", "rb")))
    def test_parallel_threshold_preserves_source_facts_and_canonical_output(
        self, language: str, extension: str
    ) -> None:
        threshold = self.application.extraction.request(language, str(self.workspace)).batch_config.parallel_threshold
        fixtures = self.repository / "tests/fixtures/implementation_manifest" / language
        small = fixtures / "no_calls/src" / f"example.{extension}"
        large = fixtures / "canonical/src" / f"example.{extension}"
        serial_names = tuple(f"example_{index:04d}.{extension}" for index in range(threshold - 1))
        for index, name in enumerate(serial_names):
            shutil.copyfile(large if index % 3 == 0 else small, self.workspace / name)
        serial = self.application.generate_map(language, self.workspace, self.scan_policy())

        added = f"example_{threshold - 1:04d}.{extension}"
        parallel_names = (*serial_names, added)
        shutil.copyfile(small, self.workspace / added)
        parallel = self.application.generate_map(language, self.workspace, self.scan_policy())
        repeated = self.application.generate_map(language, self.workspace, self.scan_policy())

        assert {name: parallel.extraction.files[name] for name in serial_names} == serial.extraction.files
        assert parallel.dependency_graph.edges == serial.dependency_graph.edges
        assert tuple(parallel.extraction.files) == parallel_names
        assert tuple(source.relative_path for source in parallel.extraction.manifest.sources) == parallel_names
        assert repeated == parallel
        format = self.application.implementation_manifest_formats()[0]
        assert self.application.implementation_manifest(repeated, format) == self.application.implementation_manifest(
            parallel, format
        )
