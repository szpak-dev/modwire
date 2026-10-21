from typing import Literal, Self

from pydantic import model_validator

from ....shared.code.models.code_map_producer import CodeMapProducer
from ....shared.code.models.source_call import SourceCall
from ....shared.code.models.source_manifest import SourceManifest
from ....shared.values.models.value_model import ValueModel
from .implementation_manifest_validator import ImplementationManifestValidator
from .manifest_annotation import ManifestAnnotation
from .manifest_attribute import ManifestAttribute
from .manifest_callable import ManifestCallable
from .manifest_declaration_relation import ManifestDeclarationRelation
from .manifest_dependency import ManifestDependency
from .manifest_namespace import ManifestNamespace
from .manifest_parameter import ManifestParameter
from .manifest_span import ManifestSpan
from .manifest_symbol import ManifestSymbol


class ImplementationManifest(ValueModel):
    """A versioned, language-neutral statement of observed implementation facts and provenance."""

    schema_version: Literal[7] = 7
    producer: CodeMapProducer
    source_manifest: SourceManifest
    namespaces: tuple[ManifestNamespace, ...]
    symbols: tuple[ManifestSymbol, ...]
    callables: tuple[ManifestCallable, ...]
    parameters: tuple[ManifestParameter, ...]
    attributes: tuple[ManifestAttribute, ...]
    annotations: tuple[ManifestAnnotation, ...]
    calls: tuple[SourceCall, ...]
    declaration_relations: tuple[ManifestDeclarationRelation, ...]
    dependencies: tuple[ManifestDependency, ...]
    spans: tuple[ManifestSpan, ...]

    @model_validator(mode="after")
    def validate_facts(self) -> Self:
        """Validate canonical ordering, identity uniqueness, and fact references."""
        ImplementationManifestValidator(
            source_manifest=self.source_manifest,
            namespaces=self.namespaces,
            symbols=self.symbols,
            callables=self.callables,
            parameters=self.parameters,
            attributes=self.attributes,
            annotations=self.annotations,
            calls=self.calls,
            declaration_relations=self.declaration_relations,
            dependencies=self.dependencies,
            spans=self.spans,
        ).validate()
        return self
