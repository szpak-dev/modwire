from typing import assert_never

from modwire.application import (
    CodeMap,
    FileId,
    ImplementationManifest,
    SourceFile,
    SourceTypeAbsent,
    SourceTypeKind,
    SourceTypeReference,
    SourceTypeUnsupported,
)

from .claim_result import ClaimResult
from .language_capability_matrix.contracts.manifests.claim import ManifestClaim
from .language_capability_matrix.contracts.scenarios.claims.scenario import ScenarioClaim
from .language_capability_matrix.contracts.scenarios.observations.capability import CapabilityObservation
from .language_capability_matrix.contracts.scenarios.observations.relationship import RelationshipObservation
from .language_capability_matrix.values.enums.claim_state import ClaimState
from .language_capability_matrix.values.enums.type_slot_role import TypeSlotRole


class FixtureClaimEvaluator:
    def evaluate_code_map(self, code_map: CodeMap, source_id: str, wrapped: ScenarioClaim) -> ClaimResult:
        source = code_map.extraction.files[FileId(source_id)]
        claim = wrapped.root
        return self.evaluate_observation(source, claim.observation, claim.state)

    def evaluate_observation(
        self, source: SourceFile, wrapped: CapabilityObservation | RelationshipObservation, state: ClaimState
    ) -> ClaimResult:
        observation = wrapped.root
        if observation.kind == "source":
            present = str(source.file_id) == observation.relative_path.value.as_posix()
        elif observation.kind == "empty_source":
            present = str(source.file_id) == observation.relative_path.value.as_posix() and not any(
                (
                    source.namespaces,
                    source.declarations,
                    source.functions,
                    source.values,
                    source.callable_values,
                    source.anonymous_callables,
                    source.calls,
                    source.imports,
                    source.exports,
                    source.declaration_relations,
                )
            )
        elif observation.kind == "declaration":
            present = any(
                declaration.declaration_id.qualified_name == observation.qualified_name.value
                and declaration.kind is observation.declaration_kind
                for declaration in source.declarations
            )
        elif observation.kind == "callable":
            present = any(
                callable_fact.qualified_name == observation.qualified_name.value
                and callable_fact.kind is observation.callable_kind
                for callable_fact in source.canonical_callables()
            )
        elif observation.kind == "call":
            present = any(
                callable_fact.qualified_name == observation.owner.value
                and call.target_name == observation.target.value
                and call.resolution is observation.resolution
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
                for callable_fact in source.canonical_callables()
                for position, parameter in enumerate(callable_fact.parameters)
            )
        elif observation.kind == "parameter_kinds":
            observed = {
                parameter.kind
                for callable_fact in source.canonical_callables()
                for parameter in callable_fact.parameters
            }
            present = observed == set(observation.present)
        elif observation.kind == "type_reference":
            present = observation.type in self.type_slots(
                source, observation.owner.value, observation.role, observation.position.root
            )
        elif observation.kind == "type_slot":
            slots = self.type_slots(source, observation.owner.value, observation.role, observation.position.root)
            if state is ClaimState.UNSUPPORTED:
                return ClaimResult(satisfied=any(slot.kind is SourceTypeKind.UNSUPPORTED for slot in slots))
            if state is ClaimState.ABSENT:
                return ClaimResult(satisfied=any(slot.kind is SourceTypeKind.ABSENT for slot in slots))
            present = any(slot.kind is SourceTypeKind.REFERENCE for slot in slots)
        elif observation.kind == "annotation":
            present = any(
                owner == observation.owner.value and annotation == observation.expression.value
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
            present = any(
                item.declaration_id.qualified_name == observation.owner.value
                and item.visibility_intent is observation.visibility
                for item in (*source.declarations, *source.canonical_callables(), *source.values)
            ) or any(
                item.declaration_id.qualified_name == observation.owner.value
                and item.visibility is observation.visibility
                for declaration in source.declarations
                for item in declaration.properties
            )
        elif observation.kind == "attribute":
            present = any(
                declaration.declaration_id.qualified_name == observation.owner.value
                and attribute.name == observation.name.value
                and attribute.member_kind is observation.member_kind
                for declaration in source.declarations
                for attribute in declaration.properties
            )
        elif observation.kind == "assigned_values":
            owners = tuple(
                declaration
                for declaration in source.declarations
                if declaration.declaration_id.qualified_name == observation.owner.value
            )
            observed = tuple(
                (
                    attribute.name,
                    tuple((value.kind, value.expression, value.reference) for value in attribute.assigned_values),
                )
                for declaration in owners
                for attribute in declaration.properties
            )
            expected = tuple(
                (
                    attribute.name.value,
                    tuple((value.kind, value.expression, value.reference) for value in attribute.values),
                )
                for attribute in observation.attributes
            )
            present = len(owners) == 1 and observed == expected
        elif observation.kind == "declaration_relation":
            present = any(
                relation.source_declaration_id.qualified_name == observation.source.value
                and relation.kind is observation.relation
                and relation.target_reference == observation.target.value
                for relation in source.declaration_relations
            )
        elif observation.kind == "namespace":
            present = any(
                namespace.qualified_name == observation.qualified_name.value
                and namespace.kind is observation.namespace_kind
                for namespace in source.namespaces
            )
        elif observation.kind == "dependency":
            present = any(
                str(source.file_id) == observation.source.value.as_posix()
                and (str(dependency.target_file_id) if dependency.target_file_id is not None else str(dependency.path))
                == observation.target.value
                and dependency.resolution is observation.resolution
                for dependency in source.imports
            )
        elif observation.kind == "exact_span":
            present = any(
                callable_fact.qualified_name == observation.owner.value
                and callable_fact.line_start == observation.start.root
                and callable_fact.line_end == observation.end.root
                for callable_fact in source.canonical_callables()
            )
        elif observation.kind == "span_owner":
            present = any(
                callable_fact.qualified_name == observation.owner.value
                and callable_fact.line_start > 0
                and callable_fact.line_end >= callable_fact.line_start
                for callable_fact in source.canonical_callables()
            )
        else:
            assert_never(observation)
        return self.result(present, state)

    def type_slots(
        self, source: SourceFile, owner: str, role: TypeSlotRole, position: int
    ) -> tuple[SourceTypeReference | SourceTypeAbsent | SourceTypeUnsupported, ...]:
        if role is TypeSlotRole.RETURN:
            return tuple(
                callable_fact.return_type
                for callable_fact in source.canonical_callables()
                if callable_fact.qualified_name == owner and position == 0
            )
        if role is TypeSlotRole.PARAMETER:
            return tuple(
                parameter.type
                for callable_fact in source.canonical_callables()
                for parameter_position, parameter in enumerate(callable_fact.parameters)
                if callable_fact.qualified_name == owner and parameter_position == position
            )
        if role is TypeSlotRole.ATTRIBUTE:
            return tuple(
                attribute.type
                for declaration in source.declarations
                for attribute_position, attribute in enumerate(declaration.properties)
                if declaration.declaration_id.qualified_name == owner and attribute_position == position
            )
        assert_never(role)

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
        elif observation.kind == "dependency":
            present = any(
                str(item.source_id) == observation.source.value.as_posix()
                and item.target == observation.target.value
                and item.resolution is observation.resolution
                for item in manifest.dependencies
            )
        else:
            assert_never(observation)
        return self.result(present, claim.state)

    def result(self, present: bool, state: ClaimState) -> ClaimResult:
        if state is ClaimState.PRESENT:
            return ClaimResult(satisfied=present)
        if state is ClaimState.ABSENT:
            return ClaimResult(satisfied=not present)
        raise AssertionError("unsupported state must be evaluated by a type-slot claim")
