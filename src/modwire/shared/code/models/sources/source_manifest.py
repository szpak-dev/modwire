from typing import Self

from pydantic import Field, model_validator

from ..failures.code_validation_error import CodeValidationError
from ..failures.code_violation import CodeViolation
from .digest_algorithm import DigestAlgorithm
from .source_manifest_content import SourceManifestContent
from .source_manifest_identity import SourceManifestIdentity


class SourceManifest(SourceManifestContent):
    digest_algorithm: DigestAlgorithm
    digest: str = Field(pattern="^[0-9a-f]{64}$")

    def identity(self) -> SourceManifestIdentity:
        return SourceManifestIdentity(digest_algorithm=self.digest_algorithm, digest=self.digest)

    @model_validator(mode="after")
    def validate_manifest(self) -> Self:
        self.validate_sources()
        if self.canonical_digest() != self.digest:
            raise CodeValidationError(CodeViolation.INVALID_SOURCE_MANIFEST_DIGEST, self.digest)
        return self
