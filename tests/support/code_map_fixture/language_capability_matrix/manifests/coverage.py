from pydantic import Field

from ...model import FixtureModel


class ManifestEvidenceExpectation(FixtureModel):
    source: str = Field(min_length=1)
    namespaces: tuple[str, ...]
    symbols: tuple[str, ...]
    callables: tuple[str, ...]
    parameters: tuple[str, ...]
    attributes: tuple[str, ...]
    annotations: tuple[str, ...]
    calls: tuple[str, ...]
    declaration_relations: tuple[str, ...]
    dependencies: tuple[str, ...]


class ManifestTransitionExpectation(FixtureModel):
    before: str = Field(min_length=1)
    after: str = Field(min_length=1)
