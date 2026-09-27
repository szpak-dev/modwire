from ....shared.code.models.identity import FileId
from ....shared.code.models.source_artifact import SourceArtifact
from ....shared.values.models.value_model import ValueModel


class SourceEntry(ValueModel):
    source_id: FileId
    relative_path: str
    content_digest: str
    path: str

    def artifact(self) -> SourceArtifact:
        return SourceArtifact(
            source_id=str(self.source_id),
            relative_path=self.relative_path,
            content_digest=self.content_digest,
        )
