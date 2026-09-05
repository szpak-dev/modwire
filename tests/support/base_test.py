from collections.abc import Mapping
from pathlib import Path

import pytest


class BaseTestCase:
    workspace: Path
    repository = Path(__file__).resolve().parents[2]

    @pytest.fixture(autouse=True)
    def _workspace(self, tmp_path: Path) -> None:
        self.workspace = tmp_path

    def write_files(self, files: Mapping[str, str]) -> None:
        for name, content in files.items():
            target = self.workspace / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
