from pydantic import Field

from modwire.application import FileId, SourceManifest

from ....fixture_model import FixtureModel
from ...values.paths.document_path import RepositoryDocumentPath


class ScenarioExtractionDocument(FixtureModel):
    files: dict[FileId, RepositoryDocumentPath] = Field(min_length=1)
    manifest: SourceManifest
    files_excluded: int = Field(ge=0)
    directories_pruned: int = Field(ge=0)
