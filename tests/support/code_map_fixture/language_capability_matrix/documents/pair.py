from ...fixture_model import FixtureModel
from ..values.paths.document_path import RepositoryDocumentPath


class LanguageDocumentPair(FixtureModel):
    contract: RepositoryDocumentPath
    reference_projection: RepositoryDocumentPath
