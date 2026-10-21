import hashlib
import json
from typing import Self

from pydantic import Field, model_validator

from ...values.models.value_model import ValueModel
from .code_validation_error import CodeValidationError
from .code_violation import CodeViolation
from .digest_algorithm import DigestAlgorithm
from .runtime_observation import RuntimeObservation
from .scan_policy import ScanPolicy
from .source_artifact import SourceArtifact
from .source_manifest_identity import SourceManifestIdentity


class SourceManifest(ValueModel):
    policy: ScanPolicy
    runtime: RuntimeObservation
    sources: tuple[SourceArtifact, ...]
    digest_algorithm: DigestAlgorithm
    digest: str = Field(pattern="^[0-9a-f]{64}$")

    def identity(self) -> SourceManifestIdentity:
        return SourceManifestIdentity(digest_algorithm=self.digest_algorithm, digest=self.digest)

    @model_validator(mode="after")
    def validate_manifest(self) -> Self:
        ordered = tuple(sorted(self.sources, key=lambda item: (item.source_id, item.relative_path)))
        if ordered != self.sources:
            raise CodeValidationError(CodeViolation.NON_CANONICAL_SOURCE_ARTIFACTS, "source manifest")
        if len({item.source_id for item in self.sources}) != len(self.sources):
            raise CodeValidationError(CodeViolation.DUPLICATE_SOURCE_IDENTITY, "source manifest")
        payload = {
            "policy": self.policy.model_dump(mode="json"),
            "runtime": self.runtime.model_dump(mode="json"),
            "sources": [source.model_dump(mode="json") for source in self.sources],
        }
        serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
        if hashlib.sha256(serialized).hexdigest() != self.digest:
            raise CodeValidationError(CodeViolation.INVALID_SOURCE_MANIFEST_DIGEST, self.digest)
        return self
