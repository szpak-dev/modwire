from modwire.application import (
    ManifestAnnotation,
    ManifestAttribute,
    ManifestCallable,
    ManifestDeclarationRelation,
    ManifestDependency,
    ManifestNamespace,
    ManifestParameter,
    ManifestSymbol,
    SourceCall,
)

from ...model import FixtureModel


class ManifestEvidence(FixtureModel):
    namespaces: tuple[ManifestNamespace, ...]
    symbols: tuple[ManifestSymbol, ...]
    callables: tuple[ManifestCallable, ...]
    parameters: tuple[ManifestParameter, ...]
    attributes: tuple[ManifestAttribute, ...]
    annotations: tuple[ManifestAnnotation, ...]
    calls: tuple[SourceCall, ...]
    declaration_relations: tuple[ManifestDeclarationRelation, ...]
    dependencies: tuple[ManifestDependency, ...]
