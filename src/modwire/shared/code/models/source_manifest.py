import hashlib
import json
from typing import Self

from pydantic import Field, model_validator

from ...values.models.value_model import ValueModel
from .runtime_observation import RuntimeObservation
from .scan_policy import ScanPolicy
from .source_artifact import SourceArtifact


class SourceManifest(ValueModel):
    policy: ScanPolicy
    runtime: RuntimeObservation
    sources: tuple[SourceArtifact, ...]
    digest_algorithm: str = Field(pattern="^sha256$")
    digest: str = Field(pattern="^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_manifest(self) -> Self:
        ordered = tuple(sorted(self.sources, key=lambda item: (item.source_id, item.relative_path)))
        if ordered != self.sources:
            raise ValueError("Source manifest artifacts must be canonically ordered.")
        if len({item.source_id for item in self.sources}) != len(self.sources):
            raise ValueError("Source manifest source identities must be unique.")
        payload = {
            "policy": self.policy.model_dump(mode="json"),
            "runtime": self.runtime.model_dump(mode="json"),
            "sources": [source.model_dump(mode="json") for source in self.sources],
        }
        serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
        if hashlib.sha256(serialized).hexdigest() != self.digest:
            raise ValueError("Source manifest digest does not match its canonical payload.")
        return self
