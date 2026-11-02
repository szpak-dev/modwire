from typing import assert_never

from modwire.application import (
    CodeMap,
    FileId,
    ImplementationManifest,
    SourceFile,
    SourceParameter,
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
from .language_capability_matrix.oracle.binding import LanguageScenarioBinding
from .language_capability_matrix.oracle.catalog import FixtureScenarioCatalog
from .language_capability_matrix.oracle.graph import FixtureGraphOwnership
from .language_capability_matrix.oracle.identities import FixtureSourceIdentities
from .language_capability_matrix.values.enums.claim_state import ClaimState
from .language_capability_matrix.values.enums.type_slot_role import TypeSlotRole


class FixtureClaimEvaluator:
    def evaluate_code_map(
        self, code_map: CodeMap, source_id: str, wrapped: ScenarioClaim, expected: SourceFile
    ) -> ClaimResult:
        source = code_map.extraction.files[FileId(source_id)]
        claim = wrapped.root
        return self.evaluate_observation(source, claim.observation, claim.state, expected)

    def evaluate_binding(
        self,
        code_map: CodeMap,
        catalog: FixtureScenarioCatalog,
        binding: LanguageScenarioBinding,
        identities: FixtureSourceIdentities,
    ) -> tuple[ClaimResult, ...]:
        sources = set(identities.sources)
        if set(code_map.extraction.files) != sources or not FixtureGraphOwnership(frozenset(sources)).accepts(
            code_map.dependency_graph
        ):
            return (ClaimResult(satisfied=False),)
        expected = catalog.expected[binding.scenario]
        actual_artifacts = {artifact.source_id: artifact for artifact in code_map.extraction.manifest.sources}
        expected_artifacts = {artifact.source_id: artifact for artifact in expected.extraction.manifest.sources}
        provenance = (
            code_map.extraction.files_found == len(sources)
            and code_map.extraction.files_excluded == expected.extraction.files_excluded
            and code_map.extraction.directories_pruned == expected.extraction.directories_pruned
            and code_map.extraction.manifest.policy == expected.extraction.manifest.policy
            and set(actual_artifacts) == {str(source) for source in sources}
            and all(
                actual_artifacts[str(authored)].relative_path == str(authored)
                and actual_artifacts[str(authored)].content_digest == expected_artifacts[str(canonical)].content_digest
                for authored, canonical in identities.sources.items()
            )
        )
        return (
            ClaimResult(satisfied=provenance),
            *(
                self.result(
                    expectation.fact.read_actual(code_map, identities) == expectation.fact.read_expected(expected),
                    expectation.state,
                )
                for expectation in binding.expectations
            ),
        )

    def evaluate_observation(
        self,
        source: SourceFile,
        wrapped: CapabilityObservation | RelationshipObservation,
        state: ClaimState,
        expected_source: SourceFile,
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
            expected_parameters = self.parameters(expected_source, observation.owner.value, observation.position.root)
            actual_parameters = self.parameters(source, observation.owner.value, observation.position.root)
            if state is ClaimState.ABSENT:
                return ClaimResult(satisfied=not actual_parameters)
            present = bool(expected_parameters) and actual_parameters == expected_parameters
        elif observation.kind == "parameter_list":
            expected_callables = tuple(
                callable_fact
                for callable_fact in expected_source.canonical_callables()
                if callable_fact.qualified_name == observation.owner.value
            )
            actual_callables = tuple(
                callable_fact
                for callable_fact in source.canonical_callables()
                if callable_fact.qualified_name == observation.owner.value
            )
            present = (
                len(expected_callables) == 1
                and len(actual_callables) == 1
                and actual_callables[0].parameters == expected_callables[0].parameters
            )
        elif observation.kind == "type_reference":
            expected_slots = self.type_slots(
                expected_source, observation.owner.value, observation.role, observation.position.root
            )
            present = (
                bool(expected_slots)
                and all(slot.kind is SourceTypeKind.REFERENCE for slot in expected_slots)
                and self.type_slots(source, observation.owner.value, observation.role, observation.position.root)
                == expected_slots
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
            expected_owners = tuple(
                declaration
                for declaration in expected_source.declarations
                if declaration.declaration_id.qualified_name == observation.owner.value
            )
            expected = tuple(
                (
                    attribute.name,
                    tuple((value.kind, value.expression, value.reference) for value in attribute.assigned_values),
                )
                for declaration in expected_owners
                for attribute in declaration.properties
            )
            present = len(owners) == len(expected_owners) == 1 and observed == expected
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

    def parameters(self, source: SourceFile, owner: str, position: int) -> tuple[SourceParameter, ...]:
        return tuple(
            parameter
            for callable_fact in source.canonical_callables()
            if callable_fact.qualified_name == owner
            for index, parameter in enumerate(callable_fact.parameters)
            if index == position
        )

    def evaluate_manifest(
        self, manifest: ImplementationManifest, claim: ManifestClaim, expected: SourceFile
    ) -> ClaimResult:
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
            actual = tuple(
                item
                for item in manifest.parameters
                if item.callable_id.qualified_name == observation.owner.value
                and item.position == observation.position.root
            )
            if claim.state is ClaimState.ABSENT:
                return ClaimResult(satisfied=not actual)
            parameters = self.parameters(expected, observation.owner.value, observation.position.root)
            present = any(
                item.name == parameter.name
                and item.kind is parameter.kind
                and item.has_default is parameter.has_default
                for item in actual
                for parameter in parameters
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
