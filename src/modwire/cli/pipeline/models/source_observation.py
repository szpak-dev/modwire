from pydantic import Field

from ....extraction.extractors.models.extraction_request import ExtractionRequest
from ....shared.code.models.source_manifest import SourceManifest
from ....shared.code.models.source_manifest_identity import SourceManifestIdentity
from ....shared.values.models.value_model import ValueModel
from .source_entry import SourceEntry


class SourceObservation(ValueModel):
    """Immutable canonical source inventory reusable by identity and cached map operations."""

    request: ExtractionRequest
    entries: tuple[SourceEntry, ...]
    files_found: int = Field(ge=0)
    files_excluded: int = Field(ge=0)
    directories_pruned: int = Field(ge=0)
    manifest: SourceManifest

    def identity(self) -> SourceManifestIdentity:
        """Return the canonical public identity of this observed source manifest."""

        return self.manifest.identity()
