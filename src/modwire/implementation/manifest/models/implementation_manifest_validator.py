import json
from dataclasses import dataclass

from ....shared.code.models.source_dependency_resolution import SourceDependencyResolution
from ....shared.code.models.source_manifest import SourceManifest
from .implementation_manifest_validation_error import ImplementationManifestValidationError
from .implementation_manifest_violation import ImplementationManifestViolation
from .manifest_annotation import ManifestAnnotation
from .manifest_attribute import ManifestAttribute
from .manifest_callable import ManifestCallable
from .manifest_declaration_relation import ManifestDeclarationRelation
from .manifest_dependency import ManifestDependency
from .manifest_dependency_target_kind import ManifestDependencyTargetKind
from .manifest_namespace import ManifestNamespace
from .manifest_parameter import ManifestParameter
from .manifest_span import ManifestSpan
from .manifest_symbol import ManifestSymbol


@dataclass(frozen=True)
class ImplementationManifestValidator:
    source_manifest: SourceManifest
    namespaces: tuple[ManifestNamespace, ...]
    symbols: tuple[ManifestSymbol, ...]
    callables: tuple[ManifestCallable, ...]
    parameters: tuple[ManifestParameter, ...]
    attributes: tuple[ManifestAttribute, ...]
    annotations: tuple[ManifestAnnotation, ...]
    declaration_relations: tuple[ManifestDeclarationRelation, ...]
    dependencies: tuple[ManifestDependency, ...]
    spans: tuple[ManifestSpan, ...]

    def validate(self) -> None:
        self.validate_collections()
        symbol_ids = {item.id.canonical() for item in self.symbols}
        callable_ids = {item.symbol_id.canonical() for item in self.callables}
        parameter_ids = {item.id for item in self.parameters}
        attribute_ids = {item.id for item in self.attributes}
        self.validate_identities(symbol_ids, callable_ids, parameter_ids, attribute_ids)
        self.validate_references(symbol_ids, callable_ids, parameter_ids, attribute_ids)
        self.validate_dependencies()

    def validate_collections(self) -> None:
        collections = (
            ("namespaces", self.namespaces),
            ("symbols", self.symbols),
            ("callables", self.callables),
            ("parameters", self.parameters),
            ("attributes", self.attributes),
            ("annotations", self.annotations),
            ("declaration relations", self.declaration_relations),
            ("dependencies", self.dependencies),
            ("spans", self.spans),
        )
        for subject, collection in collections:
            keys = tuple(
                json.dumps(item.model_dump(mode="json"), ensure_ascii=False, separators=(",", ":"), sort_keys=True)
                for item in collection
            )
            self.require(
                keys == tuple(sorted(keys)),
                ImplementationManifestViolation.NON_CANONICAL_ORDER,
                subject,
            )
            self.require(
                len(keys) == len(set(keys)),
                ImplementationManifestViolation.DUPLICATE_FACT,
                subject,
            )

    def validate_identities(
        self,
        symbol_ids: set[str],
        callable_ids: set[str],
        parameter_ids: set[str],
        attribute_ids: set[str],
    ) -> None:
        self.require(
            len(symbol_ids) == len(self.symbols),
            ImplementationManifestViolation.DUPLICATE_IDENTITY,
            "symbols",
        )
        self.require(
            len(callable_ids) == len(self.callables),
            ImplementationManifestViolation.DUPLICATE_IDENTITY,
            "callables",
        )
        self.require(
            len(parameter_ids) == len(self.parameters),
            ImplementationManifestViolation.DUPLICATE_IDENTITY,
            "parameters",
        )
        parameter_positions = {(item.callable_id.canonical(), item.position) for item in self.parameters}
        self.require(
            len(parameter_positions) == len(self.parameters),
            ImplementationManifestViolation.DUPLICATE_IDENTITY,
            "parameter positions",
        )
        self.require(
            len(attribute_ids) == len(self.attributes),
            ImplementationManifestViolation.DUPLICATE_IDENTITY,
            "attributes",
        )
        span_targets = {item.target_id for item in self.spans}
        self.require(
            len(span_targets) == len(self.spans),
            ImplementationManifestViolation.DUPLICATE_IDENTITY,
            "spans",
        )

    def validate_references(
        self,
        symbol_ids: set[str],
        callable_ids: set[str],
        parameter_ids: set[str],
        attribute_ids: set[str],
    ) -> None:
        source_ids = {str(item.source_id) for item in self.source_manifest.sources}
        self.require(
            all(str(item.id.source_id) in source_ids for item in self.symbols),
            ImplementationManifestViolation.UNKNOWN_REFERENCE,
            "symbol sources",
        )
        self.require(
            callable_ids <= symbol_ids,
            ImplementationManifestViolation.UNKNOWN_REFERENCE,
            "callable symbols",
        )
        self.require(
            all(item.callable_id.canonical() in callable_ids for item in self.parameters),
            ImplementationManifestViolation.UNKNOWN_REFERENCE,
            "parameter callables",
        )
        self.require(
            all(item.owner_symbol_id.canonical() in symbol_ids for item in self.attributes),
            ImplementationManifestViolation.UNKNOWN_REFERENCE,
            "attribute symbols",
        )
        targets = symbol_ids | parameter_ids | attribute_ids
        self.require(
            all(item.target_id in targets for item in self.annotations),
            ImplementationManifestViolation.UNKNOWN_REFERENCE,
            "annotation targets",
        )
        self.require(
            all(item.source_symbol_id.canonical() in symbol_ids for item in self.declaration_relations),
            ImplementationManifestViolation.UNKNOWN_REFERENCE,
            "declaration relation symbols",
        )
        self.require(
            all(item.target_id in symbol_ids for item in self.spans),
            ImplementationManifestViolation.UNKNOWN_REFERENCE,
            "span symbols",
        )
        self.require(
            all(item.source_id in source_ids for item in self.dependencies),
            ImplementationManifestViolation.UNKNOWN_REFERENCE,
            "dependency sources",
        )
        self.require(
            all(
                item.target_kind is not ManifestDependencyTargetKind.SOURCE or item.target in source_ids
                for item in self.dependencies
            ),
            ImplementationManifestViolation.UNKNOWN_REFERENCE,
            "dependency source targets",
        )

    def validate_dependencies(self) -> None:
        expected_resolutions = {
            ManifestDependencyTargetKind.SOURCE: SourceDependencyResolution.RESOLVED,
            ManifestDependencyTargetKind.EXTERNAL: SourceDependencyResolution.EXTERNAL,
            ManifestDependencyTargetKind.UNRESOLVED: SourceDependencyResolution.UNRESOLVED,
        }
        self.require(
            all(expected_resolutions[item.target_kind] == item.resolution for item in self.dependencies),
            ImplementationManifestViolation.INCONSISTENT_DEPENDENCY,
            "dependency target resolutions",
        )

    def require(
        self,
        condition: bool,
        violation: ImplementationManifestViolation,
        subject: str,
    ) -> None:
        if not condition:
            raise ImplementationManifestValidationError(violation, subject)
