from ....fixture_model import FixtureModel
from ...values.paths.source_path import RepositorySourcePath


class SourceIdentityProjection(FixtureModel):
    authored: RepositorySourcePath
    canonical: RepositorySourcePath
