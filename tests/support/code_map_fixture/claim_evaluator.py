from modwire.application import (
    CodeMap,
    ImplementationManifest,
    SourceAssignedValueKind,
    SourceTypeAbsent,
    SourceTypeKind,
    SourceTypeReference,
    SourceTypeUnsupported,
)

from .language_capability_matrix.contracts.manifests import ManifestClaim
from .language_capability_matrix.contracts.scenarios import CapabilityClaim, RelationshipClaim, ScenarioClaim
from .language_capability_matrix.values import ClaimState, TypeSlotRole
from .model import FixtureModel


class ClaimResult(FixtureModel):
    satisfied: bool


class FixtureClaimEvaluator:
    def evaluate_code_map(self, code_map: CodeMap, wrapped: ScenarioClaim) -> ClaimResult:
        claim = wrapped.root
        if claim.kind == "capability":
            return self.evaluate_capability(code_map, claim)
        return self.evaluate_relationship(code_map, claim)

    def evaluate_capability(self, code_map: CodeMap, claim: CapabilityClaim) -> ClaimResult:
        observation = claim.observation.root
        if observation.kind == "source":
            present = observation.relative_path.value.as_posix() in code_map.extraction.files
        elif observation.kind == "declaration":
            present = any(
                declaration.declaration_id.qualified_name == observation.qualified_name.value
                and declaration.kind is observation.declaration_kind
                for source in code_map.extraction.files.values()
                for declaration in source.declarations
            )
        elif observation.kind == "callable":
            present = any(
                callable_fact.qualified_name == observation.qualified_name.value
                and callable_fact.kind is observation.callable_kind
                for source in code_map.extraction.files.values()
                for callable_fact in source.canonical_callables()
            )
        elif observation.kind == "call":
            present = any(
                callable_fact.qualified_name == observation.owner.value
                and call.target_name == observation.target.value
                and call.resolution is observation.resolution
                for source in code_map.extraction.files.values()
                for callable_fact in source.canonical_callables()
                for call in source.calls
                if call.source_callable_id == callable_fact.declaration_id
            )
        elif observation.kind == "parameter":
            present = any(
                callable_fact.qualified_name == observation.owner.value
                and position == observation.position.root
                and parameter.name == observation.name.value
                and parameter.kind is observation.parameter_kind
                and parameter.has_default is observation.has_default
                for source in code_map.extraction.files.values()
                for callable_fact in source.canonical_callables()
                for position, parameter in enumerate(callable_fact.parameters)
            )
        elif observation.kind == "parameter_kinds":
            observed = {
                parameter.kind
                for source in code_map.extraction.files.values()
                for callable_fact in source.canonical_callables()
                for parameter in callable_fact.parameters
            }
            present = observed == set(observation.present)
        elif observation.kind == "type_reference":
            present = observation.type in self.type_slots(
                code_map,
                observation.owner.value,
                observation.role,
                observation.position.root,
            )
        elif observation.kind == "type_slot":
            slots = self.type_slots(
                code_map,
                observation.owner.value,
                observation.role,
                observation.position.root,
            )
            if claim.state is ClaimState.UNSUPPORTED:
                return ClaimResult(satisfied=any(slot.kind is SourceTypeKind.UNSUPPORTED for slot in slots))
            if claim.state is ClaimState.ABSENT:
                return ClaimResult(satisfied=any(slot.kind is SourceTypeKind.ABSENT for slot in slots))
            present = bool(slots)
        elif observation.kind == "annotation":
            present = any(
                owner == observation.owner.value and annotation == observation.expression.value
                for source in code_map.extraction.files.values()
                for owner, annotation in (
                    *(
                        (declaration.declaration_id.qualified_name, item)
                        for declaration in source.declarations
                        for item in declaration.declaration_annotations
                    ),
                    *(
                        (callable_fact.qualified_name, item)
                        for callable_fact in source.canonical_callables()
                        for item in callable_fact.decorators
                    ),
                )
            )
        elif observation.kind == "modifier":
            present = observation.modifier.value in {
                *(
                    item.visibility_intent.value
                    for source in code_map.extraction.files.values()
                    for item in (
                        *source.declarations,
                        *source.functions,
                        *source.values,
                        *source.callable_values,
                        *source.anonymous_callables,
                    )
                    if item.declaration_id.qualified_name == observation.owner.value
                ),
                *(
                    item.kind.value
                    for source in code_map.extraction.files.values()
                    for item in source.canonical_callables()
                    if item.declaration_id.qualified_name == observation.owner.value
                ),
                *(
                    item.member_kind.value
                    for source in code_map.extraction.files.values()
                    for declaration in source.declarations
                    for item in declaration.properties
                    if declaration.declaration_id.qualified_name == observation.owner.value
                ),
            }
        elif observation.kind == "attribute":
            present = any(
                declaration.declaration_id.qualified_name == observation.owner.value
                and attribute.name == observation.name.value
                and attribute.member_kind is observation.member_kind
                for source in code_map.extraction.files.values()
                for declaration in source.declarations
                for attribute in declaration.properties
            )
        elif observation.kind == "assigned_value_partition":
            partitions: dict[SourceAssignedValueKind, set[str]] = {
                SourceAssignedValueKind.UNASSIGNED: set(),
                SourceAssignedValueKind.LITERAL: set(),
                SourceAssignedValueKind.REFERENCE: set(),
                SourceAssignedValueKind.CALL: set(),
                SourceAssignedValueKind.UNRESOLVED: set(),
            }
            for source in code_map.extraction.files.values():
                for declaration in source.declarations:
                    if declaration.declaration_id.qualified_name == observation.owner.value:
                        for attribute in declaration.properties:
                            for value in attribute.assigned_values:
                                if value.kind is SourceAssignedValueKind.UNSUPPORTED:
                                    partitions[SourceAssignedValueKind.UNASSIGNED].add(attribute.name)
                                elif value.kind in partitions:
                                    partitions[value.kind].add(attribute.name)
            present = (
                partitions[SourceAssignedValueKind.UNASSIGNED] == {item.value for item in observation.absent}
                and partitions[SourceAssignedValueKind.LITERAL] == {item.value for item in observation.literal}
                and partitions[SourceAssignedValueKind.REFERENCE] == {item.value for item in observation.reference}
                and partitions[SourceAssignedValueKind.CALL] == {item.value for item in observation.call}
                and partitions[SourceAssignedValueKind.UNRESOLVED] == {item.value for item in observation.unresolved}
            )
        elif observation.kind == "declaration_relation":
            present = any(
                relation.source_declaration_id.qualified_name == observation.source.value
                and relation.kind is observation.relation
                and relation.target_reference == observation.target.value
                for source in code_map.extraction.files.values()
                for relation in source.declaration_relations
            )
        elif observation.kind == "namespace":
            present = any(
                namespace.qualified_name == observation.qualified_name.value
                and namespace.kind is observation.namespace_kind
                for source in code_map.extraction.files.values()
                for namespace in source.namespaces
            )
        elif observation.kind == "dependency":
            present = any(
                str(source.file_id) == observation.source.value.as_posix()
                and (str(dependency.target_file_id) if dependency.target_file_id is not None else str(dependency.path))
                == observation.target.value
                and dependency.resolution is observation.resolution
                for source in code_map.extraction.files.values()
                for dependency in source.imports
            )
        elif observation.kind == "exact_span":
            present = any(
                callable_fact.qualified_name == observation.owner.value
                and callable_fact.line_start == observation.start.root
                and callable_fact.line_end == observation.end.root
                for source in code_map.extraction.files.values()
                for callable_fact in source.canonical_callables()
            )
        else:
            present = any(
                callable_fact.qualified_name == observation.owner.value
                and callable_fact.line_start > 0
                and callable_fact.line_end >= callable_fact.line_start
                for source in code_map.extraction.files.values()
                for callable_fact in source.canonical_callables()
            )
        return self.result(present, claim.state)

    def type_slots(
        self,
        code_map: CodeMap,
        owner: str,
        role: TypeSlotRole,
        position: int,
    ) -> tuple[SourceTypeReference | SourceTypeAbsent | SourceTypeUnsupported, ...]:
        if role is TypeSlotRole.RETURN:
            return tuple(
                callable_fact.return_type
                for source in code_map.extraction.files.values()
                for callable_fact in source.canonical_callables()
                if callable_fact.qualified_name == owner and position == 0
            )
        if role is TypeSlotRole.PARAMETER:
            return tuple(
                parameter.type
                for source in code_map.extraction.files.values()
                for callable_fact in source.canonical_callables()
                for parameter_position, parameter in enumerate(callable_fact.parameters)
                if callable_fact.qualified_name == owner and parameter_position == position
            )
        return tuple(
            attribute.type
            for source in code_map.extraction.files.values()
            for declaration in source.declarations
            for attribute_position, attribute in enumerate(declaration.properties)
            if declaration.declaration_id.qualified_name == owner and attribute_position == position
        )

    def evaluate_relationship(self, code_map: CodeMap, claim: RelationshipClaim) -> ClaimResult:
        observation = claim.observation.root
        if observation.kind == "declaration_relation":
            present = any(
                relation.source_declaration_id.qualified_name == observation.source.value
                and relation.kind is observation.relation
                and relation.target_reference == observation.target.value
                for source in code_map.extraction.files.values()
                for relation in source.declaration_relations
            )
        elif observation.kind == "attribute":
            present = any(
                declaration.declaration_id.qualified_name == observation.owner.value
                and attribute.name == observation.name.value
                and attribute.member_kind is observation.member_kind
                for source in code_map.extraction.files.values()
                for declaration in source.declarations
                for attribute in declaration.properties
            )
        else:
            present = any(
                str(source.file_id) == observation.source.value.as_posix()
                and (str(dependency.target_file_id) if dependency.target_file_id is not None else str(dependency.path))
                == observation.target.value
                and dependency.resolution is observation.resolution
                for source in code_map.extraction.files.values()
                for dependency in source.imports
            )
        return self.result(present, claim.state)

    def evaluate_manifest(self, manifest: ImplementationManifest, claim: ManifestClaim) -> ClaimResult:
        observation = claim.observation.root
        if observation.kind == "source":
            present = any(
                source.relative_path == observation.relative_path.value.as_posix()
                for source in manifest.source_manifest.sources
            )
        elif observation.kind == "namespace":
            present = any(
                item.qualified_name == observation.qualified_name.value and item.kind is observation.namespace_kind
                for item in manifest.namespaces
            )
        elif observation.kind == "symbol":
            present = any(
                item.qualified_name == observation.qualified_name.value and item.kind is observation.symbol_kind
                for item in manifest.symbols
            )
        elif observation.kind == "callable":
            present = any(
                item.symbol_id.qualified_name == observation.qualified_name.value
                and item.callable_kind is observation.callable_kind
                for item in manifest.callables
            )
        elif observation.kind == "parameter":
            present = any(
                item.callable_id.qualified_name == observation.owner.value
                and item.name == observation.name.value
                and item.position == observation.position.root
                and item.kind is observation.parameter_kind
                and item.has_default is observation.has_default
                for item in manifest.parameters
            )
        elif observation.kind == "attribute":
            present = any(
                item.owner_symbol_id.qualified_name == observation.owner.value
                and item.name == observation.name.value
                and item.member_kind is observation.member_kind
                for item in manifest.attributes
            )
        elif observation.kind == "call":
            present = any(
                item.source_callable_id.qualified_name == observation.owner.value
                and item.target_name == observation.target.value
                and item.resolution is observation.resolution
                for item in manifest.calls
            )
        elif observation.kind == "declaration_relation":
            present = any(
                item.source_symbol_id.qualified_name == observation.source.value
                and item.kind is observation.relation
                and item.target_reference == observation.target.value
                for item in manifest.declaration_relations
            )
        else:
            present = any(
                str(item.source_id) == observation.source.value.as_posix()
                and item.target == observation.target.value
                and item.resolution is observation.resolution
                for item in manifest.dependencies
            )
        return self.result(present, claim.state)

    def result(self, present: bool, state: ClaimState) -> ClaimResult:
        if state is ClaimState.PRESENT:
            return ClaimResult(satisfied=present)
        return ClaimResult(satisfied=not present)
