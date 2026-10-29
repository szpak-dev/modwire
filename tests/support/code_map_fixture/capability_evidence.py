from modwire.application import (
    CodeMap,
    DeclarationIdentity,
    FactCapability,
    RelationshipFamily,
    SourceAssignedValueKind,
    SourceDeclarationRelationKind,
    SourceMemberKind,
    SourceParameterKind,
    SourceTypeAbsent,
    SourceTypeKind,
    SourceTypeReference,
    SourceTypeUnsupported,
)

from .language_capability_matrix.evidence.dependency import DependencyEvidence
from .language_capability_matrix.evidence.endpoint import DeclarationRelationEndpointEvidence
from .language_capability_matrix.evidence.relation import DeclarationRelationEvidence
from .language_capability_matrix.expectations.evidence import EvidenceExpectation


class FixtureCapabilityEvidence:
    def capability_evidence(
        self,
        code_map: CodeMap,
        capability: FactCapability,
    ) -> EvidenceExpectation:
        if capability is FactCapability.SOURCES:
            observations = tuple(f"source:{source_id}" for source_id in code_map.extraction.files)
        elif capability is FactCapability.SYMBOLS:
            observations = tuple(
                observation
                for source in code_map.extraction.files.values()
                for observation in (
                    *(f"declaration:{item.kind.value}:{item.name}" for item in source.declarations),
                    *(f"function:{item.name}" for item in source.functions),
                    *(f"value:{item.value_kind.value}:{item.name}" for item in source.values),
                    *(f"callable_value:{item.qualified_name}" for item in source.callable_values),
                    *(f"anonymous:{item.qualified_name}" for item in source.anonymous_callables),
                )
            )
        elif capability is FactCapability.CALLABLES:
            observations = tuple(
                f"{item.kind.value}:{item.qualified_name}"
                for source in code_map.extraction.files.values()
                for item in source.canonical_callables()
            )
        elif capability is FactCapability.CALLS:
            observations = tuple(
                f"{item.resolution.value}:{item.target_name}:{item.ordinal}"
                for source in code_map.extraction.files.values()
                for item in source.calls
            )
        elif capability is FactCapability.PARAMETERS:
            observations = tuple(
                f"{item.kind.value}:{item.name}:{str(item.has_default).lower()}"
                for source in code_map.extraction.files.values()
                for callable_fact in source.canonical_callables()
                for item in callable_fact.parameters
            )
        elif capability is FactCapability.TYPE_REFERENCES:
            observations = tuple(
                token for slot in self.type_slots(code_map) for token in self.type_tokens(slot)
            )
        elif capability is FactCapability.ANNOTATIONS:
            observations = tuple(
                observation
                for source in code_map.extraction.files.values()
                for observation in (
                    *(
                        f"declaration:{item}"
                        for declaration in source.declarations
                        for item in declaration.declaration_annotations
                    ),
                    *(
                        f"callable:{item}"
                        for callable_fact in source.canonical_callables()
                        for item in callable_fact.decorators
                    ),
                )
            )
        elif capability is FactCapability.MODIFIERS:
            observations = tuple(
                observation
                for source in code_map.extraction.files.values()
                for observation in (
                    *(
                        f"visibility:{item.visibility_intent.value}:{item.name}"
                        for item in (
                            *source.declarations,
                            *source.functions,
                            *source.values,
                            *source.callable_values,
                            *source.anonymous_callables,
                        )
                    ),
                    *(
                        f"callable_kind:{item.kind.value}:{item.qualified_name}"
                        for item in source.canonical_callables()
                    ),
                    *(
                        f"member_kind:{item.member_kind.value}:{item.name}"
                        for declaration in source.declarations
                        for item in declaration.properties
                    ),
                )
            )
        elif capability is FactCapability.ATTRIBUTES:
            observations = tuple(
                f"{item.member_kind.value}:{item.name}"
                for source in code_map.extraction.files.values()
                for declaration in source.declarations
                for item in declaration.properties
            )
        elif capability is FactCapability.ASSIGNED_VALUES:
            observations = tuple(
                f"{assigned.kind.value}:{property_fact.name}:{assigned.expression}:{assigned.reference}"
                for source in code_map.extraction.files.values()
                for declaration in source.declarations
                for property_fact in declaration.properties
                for assigned in property_fact.assigned_values
            )
        elif capability is FactCapability.INHERITANCE:
            observations = tuple(
                f"{relation.source_declaration_id.qualified_name}:{relation.target_reference}"
                for source in code_map.extraction.files.values()
                for relation in source.declaration_relations
                if relation.kind is SourceDeclarationRelationKind.EXTENDS
            )
        elif capability is FactCapability.NAMESPACES:
            observations = tuple(
                f"{item.kind.value}:{item.qualified_name}"
                for source in code_map.extraction.files.values()
                for item in source.namespaces
            )
        elif capability is FactCapability.DECLARATION_KINDS:
            observations = tuple(
                observation
                for source in code_map.extraction.files.values()
                for observation in (
                    *(f"{item.kind.value}:{item.name}" for item in source.declarations),
                    *(f"function:{item.name}" for item in source.functions),
                    *(f"{item.value_kind.value}:{item.name}" for item in source.values),
                    *(f"value_callable:{item.qualified_name}" for item in source.callable_values),
                    *(f"callable:{item.qualified_name}" for item in source.anonymous_callables),
                )
            )
        elif capability is FactCapability.COMPOSITION:
            observations = tuple(
                f"{relation.kind.value}:{relation.source_declaration_id.qualified_name}:{relation.target_reference}"
                for source in code_map.extraction.files.values()
                for relation in source.declaration_relations
                if relation.kind is not SourceDeclarationRelationKind.EXTENDS
            )
        elif capability is FactCapability.DEPENDENCIES:
            observations = tuple(
                f"{item.resolution.value}:{item.path}:{item.target_file_id or ''}"
                for source in code_map.extraction.files.values()
                for item in source.imports
            )
        else:
            observations = tuple(
                f"{item.kind.value}:{item.qualified_name}:{item.line_start}:{item.line_end}"
                for source in code_map.extraction.files.values()
                for item in source.canonical_callables()
                if item.line_start > 0 and item.line_end >= item.line_start
            )
        return self.evidence_expectation(observations)

    def relationship_evidence(
        self,
        code_map: CodeMap,
        family: RelationshipFamily,
    ) -> EvidenceExpectation:
        if family is RelationshipFamily.DECLARATION:
            observations = tuple(
                f"{relation.kind.value}:{relation.source_declaration_id.qualified_name}:{relation.target_reference}"
                for source in code_map.extraction.files.values()
                for relation in source.declaration_relations
            )
        elif family is RelationshipFamily.MEMBER:
            observations = tuple(
                observation
                for source in code_map.extraction.files.values()
                for observation in (
                    *(f"callable:{item.kind.value}:{item.qualified_name}" for item in source.canonical_callables()),
                    *(
                        f"parameter:{item.kind.value}:{callable_fact.qualified_name}:{item.name}"
                        for callable_fact in source.canonical_callables()
                        for item in callable_fact.parameters
                    ),
                    *(
                        f"attribute:{item.member_kind.value}:{declaration.name}:{item.name}"
                        for declaration in source.declarations
                        for item in declaration.properties
                    ),
                    *(
                        f"assigned:{assigned.kind.value}:{declaration.name}:{property_fact.name}"
                        for declaration in source.declarations
                        for property_fact in declaration.properties
                        for assigned in property_fact.assigned_values
                    ),
                    *(f"call:{item.resolution.value}:{item.target_name}:{item.ordinal}" for item in source.calls),
                    *(
                        f"annotation:{declaration.name}:{item}"
                        for declaration in source.declarations
                        for item in declaration.declaration_annotations
                    ),
                    *(
                        f"decorator:{callable_fact.qualified_name}:{item}"
                        for callable_fact in source.canonical_callables()
                        for item in callable_fact.decorators
                    ),
                )
            )
        else:
            observations = tuple(
                f"{item.resolution.value}:{item.path}:{item.target_file_id or ''}"
                for source in code_map.extraction.files.values()
                for item in source.imports
            )
        return self.evidence_expectation(observations)

    def evidence_expectation(self, observations: tuple[str, ...]) -> EvidenceExpectation:
        return EvidenceExpectation(count=len(observations), variants=tuple(sorted(set(observations))))

    def annotations(self, code_map: CodeMap) -> tuple[str, ...]:
        declarations = tuple(
            declaration for source in code_map.extraction.files.values() for declaration in source.declarations
        )
        callables = tuple(
            callable_fact
            for source in code_map.extraction.files.values()
            for callable_fact in source.canonical_callables()
        )
        annotations = (
            *(annotation for declaration in declarations for annotation in declaration.declaration_annotations),
            *(annotation for callable_fact in callables for annotation in callable_fact.decorators),
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
                    for callable_fact in source.canonical_callables()
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

    def parameter_kinds(self, code_map: CodeMap) -> tuple[SourceParameterKind, ...]:
        observed = {
            parameter.kind
            for source in code_map.extraction.files.values()
            for callable_fact in source.canonical_callables()
            for parameter in callable_fact.parameters
        }
        return tuple(kind for kind in SourceParameterKind if kind in observed)

    def parameter_names(self, code_map: CodeMap) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    parameter.name
                    for source in code_map.extraction.files.values()
                    for callable_fact in source.canonical_callables()
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
            for symbol in (
                *source.declarations,
                *source.functions,
                *source.values,
                *source.callable_values,
                *source.anonymous_callables,
            )
        )
        return tuple(sorted({symbol.visibility_intent.value for symbol in symbols}))

    def callable_kinds(self, code_map: CodeMap) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    callable_fact.kind.value
                    for source in code_map.extraction.files.values()
                    for callable_fact in source.canonical_callables()
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

    def type_kinds(self, code_map: CodeMap) -> tuple[SourceTypeKind, ...]:
        observed = {kind for slot in self.type_slots(code_map) for kind in self.slot_kinds(slot)}
        return tuple(kind for kind in SourceTypeKind if kind in observed)

    def type_reference_names(self, code_map: CodeMap) -> tuple[str, ...]:
        return tuple(sorted({name for slot in self.type_slots(code_map) for name in self.reference_names(slot)}))

    def nested_type_reference_names(self, code_map: CodeMap) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    name
                    for slot in self.type_slots(code_map)
                    if slot.kind is SourceTypeKind.REFERENCE
                    for argument in slot.arguments
                    for name in self.reference_names(argument)
                }
            )
        )

    def type_slot_count(self, code_map: CodeMap) -> int:
        return len(self.type_slots(code_map))

    def owned_method_identities(self, code_map: CodeMap) -> tuple[DeclarationIdentity, ...]:
        return tuple(
            method.owner_declaration_id
            for source in code_map.extraction.files.values()
            for declaration in source.declarations
            for method in (*declaration.methods, *declaration.abstract_methods)
        )

    def owned_property_identities(self, code_map: CodeMap) -> tuple[DeclarationIdentity, ...]:
        return tuple(
            property_fact.owner_declaration_id
            for source in code_map.extraction.files.values()
            for declaration in source.declarations
            for property_fact in declaration.properties
        )

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
                    for callable_fact in source.canonical_callables()
                    if callable_fact.line_start > 0 and callable_fact.line_end >= callable_fact.line_start
                ),
                key=lambda identity: identity.canonical(),
            )
        )

    def type_slots(
        self,
        code_map: CodeMap,
    ) -> tuple[SourceTypeReference | SourceTypeAbsent | SourceTypeUnsupported, ...]:
        return tuple(
            slot
            for source in code_map.extraction.files.values()
            for slot in (
                *(callable_fact.return_type for callable_fact in source.canonical_callables()),
                *(
                    parameter.type
                    for callable_fact in source.canonical_callables()
                    for parameter in callable_fact.parameters
                ),
                *(
                    property_fact.type
                    for declaration in source.declarations
                    for property_fact in declaration.properties
                ),
            )
        )

    def slot_kinds(
        self,
        slot: SourceTypeReference | SourceTypeAbsent | SourceTypeUnsupported,
    ) -> tuple[SourceTypeKind, ...]:
        if slot.kind is not SourceTypeKind.REFERENCE:
            return (slot.kind,)
        return (slot.kind, *(kind for argument in slot.arguments for kind in self.slot_kinds(argument)))

    def reference_names(
        self,
        slot: SourceTypeReference | SourceTypeAbsent | SourceTypeUnsupported,
    ) -> tuple[str, ...]:
        if slot.kind is not SourceTypeKind.REFERENCE:
            return ()
        return (slot.name, *(name for argument in slot.arguments for name in self.reference_names(argument)))

    def type_tokens(
        self,
        slot: SourceTypeReference | SourceTypeAbsent | SourceTypeUnsupported,
    ) -> tuple[str, ...]:
        if slot.kind is not SourceTypeKind.REFERENCE:
            return (slot.kind.value,)
        return (
            f"reference:{slot.name}",
            *(token for argument in slot.arguments for token in self.type_tokens(argument)),
        )
