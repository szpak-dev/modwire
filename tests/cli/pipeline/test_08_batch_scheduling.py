import os
import shutil
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import TypeAdapter

from .base_test import NativeExtractionTestCase


class TestSourceBatchScheduling(NativeExtractionTestCase):
    @pytest.mark.parametrize(
        ("names", "expected_loads"),
        ((("small", "large") * 4, (20, 20)), (("large",) + ("empty",) * 7, (0, 9))),
    )
    def test_balances_observed_lines_and_preserves_every_source_fact(
        self, names: tuple[str, ...], expected_loads: tuple[int, int]
    ) -> None:
        fixture = self.repository / "tests/fixtures/batch_scheduling"
        root = self.workspace / "sources"
        root.mkdir()
        for index, name in enumerate(names):
            shutil.copyfile(fixture / f"{name}.py", root / f"example_{index}.py")
        sequential = self.application.generate_map("python", str(root), self.scan_policy())
        observation = self.application.observe_sources("python", str(root), self.scan_policy())
        weights = {str(entry.source_id): entry.line_count for entry in observation.entries}
        strategy = observation.request.strategy
        strategy.batch_config = strategy.batch_config.model_copy(
            update={"parallel_threshold": 1, "parallel_size": 4, "max_workers": 2}
        )
        strategy.runtime = strategy.runtime.model_copy(
            update={"command": (sys.executable, str(fixture / "record_batches.py"), sys.executable)}
        )
        recorded = self.workspace / "recorded"
        recorded.mkdir()
        with patch.dict(os.environ, {"MODWIRE_TEST_BATCHES": str(recorded)}):
            parallel = self.application.generate_map("python", str(root), self.scan_policy())
        records = TypeAdapter(list[str])
        batches = [records.validate_json(path.read_bytes()) for path in recorded.glob("*.json")]

        assert len(batches) == 2
        assert all(len(batch) == 4 for batch in batches)
        assert sorted(source_id for batch in batches for source_id in batch) == sorted(weights)
        assert sorted(sum(weights[source_id] for source_id in batch) for batch in batches) == sorted(expected_loads)
        assert parallel.extraction.files == sequential.extraction.files
        assert tuple(parallel.extraction.files) == tuple(sequential.extraction.files)

    def test_line_count_and_digest_share_one_source_read(self) -> None:
        fixture = self.repository / "tests/fixtures/source_line_counts"
        with patch.object(Path, "read_bytes", autospec=True, side_effect=Path.read_bytes) as record_read:
            observation = self.application.observe_sources("python", str(fixture), self.scan_policy())

        assert {str(entry.source_id): entry.line_count for entry in observation.entries} == {
            "empty.py": 0,
            "cr.py": 2,
            "crlf.py": 2,
            "lf.py": 2,
            "unterminated.py": 1,
        }
        reads = [call.args[0] for call in record_read.call_args_list]
        assert all(reads.count(Path(entry.path)) == 1 for entry in observation.entries)
