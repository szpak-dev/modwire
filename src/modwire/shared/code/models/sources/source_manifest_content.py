import hashlib
import json
from itertools import pairwise
from typing import Self

from ....values.models.value_model import ValueModel
from ..failures.code_validation_error import CodeValidationError
from ..failures.code_violation import CodeViolation
from .runtime_observation import RuntimeObservation
from .scan_policy import ScanPolicy
from .source_artifact import SourceArtifact


class SourceManifestContent(ValueModel):
    policy: ScanPolicy
    runtime: RuntimeObservation
    sources: tuple[SourceArtifact, ...]

    def validate_sources(self) -> Self:
        if any(
            (left.source_id, left.relative_path) > (right.source_id, right.relative_path)
            for left, right in pairwise(self.sources)
        ):
            raise CodeValidationError(CodeViolation.NON_CANONICAL_SOURCE_ARTIFACTS, "source manifest")
        if len({item.source_id for item in self.sources}) != len(self.sources):
            raise CodeValidationError(CodeViolation.DUPLICATE_SOURCE_IDENTITY, "source manifest")
        return self

    def canonical_digest(self) -> str:
        payload = {
            "policy": self.policy.model_dump(mode="json"),
            "runtime": self.runtime.model_dump(mode="json"),
            "sources": [source.model_dump(mode="json") for source in self.sources],
        }
        serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return hashlib.sha256(serialized).hexdigest()
