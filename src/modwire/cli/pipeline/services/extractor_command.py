import json
import sys
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError
from wireup import injectable

from ....shared.code.contracts.identity_resolver import IdentityResolver
from ..models.extractor_batch_input import ExtractorBatchInput
from ..models.extractor_command_input import ExtractorCommandInput
from ..models.extractor_source_input import ExtractorSourceInput


@injectable
@dataclass(frozen=True)
class ExtractorCommand:
    identities: IdentityResolver

    def read(self, language: str) -> ExtractorCommandInput | None:
        root = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else Path.cwd()
        batch = len(sys.argv) > 1 and sys.argv[1] == "--batch"
        if batch:
            try:
                paths = ExtractorBatchInput.model_validate({"paths": json.load(sys.stdin)}).paths
            except ValidationError:
                print(
                    f"Expected a JSON object mapping source ids to {language.capitalize()} file paths.", file=sys.stderr
                )
                return None
        else:
            path = Path(sys.argv[1]).resolve()
            paths = {self.identities.file_id(str(root), str(path)): str(path)}
        return ExtractorCommandInput(
            batch=batch,
            sources=tuple(
                ExtractorSourceInput(
                    source_id=source_id,
                    path=Path(path).resolve(),
                    root=root,
                    content=Path(path).read_text(encoding="utf-8"),
                )
                for source_id, path in paths.items()
            ),
        )

    def write(self, document: str) -> int:
        print(document)
        return 0
