import json
import sys
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError
from wireup import injectable

from modwire.shared.code.application import CodeApplication

from ..models.python_batch_input import PythonBatchInput
from ..models.python_command_input import PythonCommandInput
from ..models.python_source_input import PythonSourceInput


@injectable
@dataclass(frozen=True)
class PythonParserCommand:
    code: CodeApplication

    def read(self) -> PythonCommandInput | None:
        root = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else Path.cwd()
        batch = len(sys.argv) > 1 and sys.argv[1] == "--batch"
        if batch:
            try:
                paths = PythonBatchInput.model_validate({"paths": json.load(sys.stdin)}).paths
            except ValidationError:
                print("Expected a JSON object mapping source ids to Python file paths.", file=sys.stderr)
                return None
        else:
            path = Path(sys.argv[1]).resolve()
            paths = {self.code.file_id(root, path): str(path)}
        return PythonCommandInput(
            batch=batch,
            sources=tuple(
                PythonSourceInput(
                    source_id=source_id,
                    path=Path(path).resolve(),
                    root=root,
                    content=Path(path).read_text(encoding="utf-8"),
                )
                for source_id, path in paths.items()
            ),
        )

    def write(self, result: dict[str, object]) -> int:
        print(json.dumps(result))
        return 0
