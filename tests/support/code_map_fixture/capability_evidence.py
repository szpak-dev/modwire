from modwire.application import (
    CodeMap,
    DeclarationIdentity,
    SourceAssignedValueKind,
    SourceMemberKind,
)

from .language_capability_matrix.evidence.dependency import DependencyEvidence
from .language_capability_matrix.evidence.endpoint import DeclarationRelationEndpointEvidence
from .language_capability_matrix.evidence.relation import DeclarationRelationEvidence


class FixtureCapabilityEvidence:
    def annotations(self, code_map: CodeMap) -> tuple[str, ...]:
        files = tuple(code_map.extraction.files.values())
        declarations = tuple(declaration for source in files for declaration in source.declarations)
        functions = tuple(function for source in files for function in source.functions)
        callables = tuple(callable_fact for source in files for callable_fact in source.callables)
        properties = tuple(property_fact for declaration in declarations for property_fact in declaration.properties)
        annotations = (
            *(annotation for declaration in declarations for annotation in declaration.declaration_annotations),
            *(annotation for function in functions for annotation in function.declaration_annotations),
            *(annotation for callable_fact in callables for annotation in callable_fact.decorators),
            *(callable_fact.return_annotation for callable_fact in callables if callable_fact.return_annotation),
            *(
                parameter.annotation
                for callable_fact in callables
                for parameter in callable_fact.parameters
                if parameter.annotation
            ),
            *(property_fact.annotation for property_fact in properties if property_fact.annotation),
        )
        return tuple(sorted(set(annotations)))

    def declaration_names(self, code_map: CodeMap) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    declaration.name
                    for source in code_map.extraction.files.values()
                    for declaration in source.declarations
                }
            )
        )

    def callable_names(self, code_map: CodeMap) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    callable_fact.qualified_name
                    for source in code_map.extraction.files.values()
                    for callable_fact in source.callables
                }
            )
        )

    def call_resolutions(self, code_map: CodeMap) -> tuple[str, ...]:
        return tuple(
            sorted({call.resolution.value for source in code_map.extraction.files.values() for call in source.calls})
        )

    def call_target_names(self, code_map: CodeMap) -> tuple[str, ...]:
        return tuple(
            sorted({call.target_name for source in code_map.extraction.files.values() for call in source.calls})
        )

    def parameter_kinds(self, code_map: CodeMap) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    parameter.kind.value
                    for source in code_map.extraction.files.values()
                    for callable_fact in source.callables
                    for parameter in callable_fact.parameters
                }
            )
        )

    def parameter_names(self, code_map: CodeMap) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    parameter.name
                    for source in code_map.extraction.files.values()
                    for callable_fact in source.callables
                    for parameter in callable_fact.parameters
                }
            )
        )

    def attribute_names(self, code_map: CodeMap) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    property_fact.name
                    for source in code_map.extraction.files.values()
                    for declaration in source.declarations
                    for property_fact in declaration.properties
                }
            )
        )

    def assigned_value_kinds(self, code_map: CodeMap) -> dict[str, tuple[SourceAssignedValueKind, ...]]:
        observed: dict[str, set[SourceAssignedValueKind]] = {}
        for source in code_map.extraction.files.values():
            for declaration in source.declarations:
                for property_fact in declaration.properties:
                    observed.setdefault(property_fact.name, set()).update(
                        assigned.kind for assigned in property_fact.assigned_values
                    )
        return {
            name: tuple(kind for kind in SourceAssignedValueKind if kind in kinds)
            for name, kinds in sorted(observed.items())
        }

    def namespaces(self, code_map: CodeMap) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    namespace.qualified_name
                    for source in code_map.extraction.files.values()
                    for namespace in source.namespaces
                }
            )
        )

    def visibility_intents(self, code_map: CodeMap) -> tuple[str, ...]:
        symbols = tuple(
            symbol
            for source in code_map.extraction.files.values()
            for symbol in (*source.declarations, *source.functions, *source.values)
        )
        return tuple(sorted({symbol.visibility_intent.value for symbol in symbols}))

    def callable_kinds(self, code_map: CodeMap) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    callable_fact.kind.value
                    for source in code_map.extraction.files.values()
                    for callable_fact in source.callables
                }
            )
        )

    def member_kinds(self, code_map: CodeMap) -> tuple[SourceMemberKind, ...]:
        observed = {
            property_fact.member_kind
            for source in code_map.extraction.files.values()
            for declaration in source.declarations
            for property_fact in declaration.properties
        }
        return tuple(member_kind for member_kind in SourceMemberKind if member_kind in observed)

    def declaration_relations(self, code_map: CodeMap) -> tuple[DeclarationRelationEvidence, ...]:
        return tuple(
            sorted(
                (
                    DeclarationRelationEvidence(
                        source_declaration_id=relation.source_declaration_id,
                        relation=relation.kind,
                        target_reference=relation.target_reference,
                    )
                    for source in code_map.extraction.files.values()
                    for relation in source.declaration_relations
                ),
                key=lambda evidence: (
                    evidence.source_declaration_id.canonical(),
                    evidence.relation.value,
                    evidence.target_reference,
                ),
            )
        )

    def declaration_relation_endpoints(self, code_map: CodeMap) -> tuple[DeclarationRelationEndpointEvidence, ...]:
        return tuple(
            sorted(
                (
                    DeclarationRelationEndpointEvidence(
                        source_declaration_id=relation.source_declaration_id,
                        target_reference=relation.target_reference,
                    )
                    for source in code_map.extraction.files.values()
                    for relation in source.declaration_relations
                ),
                key=lambda evidence: (
                    evidence.source_declaration_id.canonical(),
                    evidence.target_reference,
                ),
            )
        )

    def dependencies(self, code_map: CodeMap) -> tuple[DependencyEvidence, ...]:
        return tuple(
            sorted(
                (
                    DependencyEvidence(path=str(imported.path), resolution=imported.resolution.value)
                    for source in code_map.extraction.files.values()
                    for imported in source.imports
                ),
                key=lambda evidence: (evidence.path, evidence.resolution),
            )
        )

    def exact_span_owners(self, code_map: CodeMap) -> tuple[DeclarationIdentity, ...]:
        return tuple(
            sorted(
                (
                    callable_fact.declaration_id
                    for source in code_map.extraction.files.values()
                    for callable_fact in source.callables
                    if callable_fact.line_start > 0 and callable_fact.line_end >= callable_fact.line_start
                ),
                key=lambda identity: identity.canonical(),
            )
        )
