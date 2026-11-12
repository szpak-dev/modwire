import json
from collections import Counter
from typing import assert_never

from pydantic import TypeAdapter

from modwire.application import (
    CapabilityStatus,
    CodeMap,
    CodeMapProducer,
    ExtractorDescriptor,
    FactCapability,
    FileId,
    ImplementationManifest,
    RelationshipFamily,
    SourceFile,
    SourceParameter,
    SourceSignature,
    SourceTypeAbsent,
    SourceTypeKind,
    SourceTypeReference,
    SourceTypeUnsupported,
)

from .claim_result import ClaimResult
from .conclusion import Conclusion
from .discrepancy import Discrepancy
from .language_capability_matrix.contracts.coverage.contract import LanguageContract
from .language_capability_matrix.contracts.manifests.claim import ManifestClaim
from .language_capability_matrix.contracts.scenarios.claims.scenario import ScenarioClaim
from .language_capability_matrix.contracts.scenarios.observations.capability import CapabilityObservation
from .language_capability_matrix.contracts.scenarios.observations.relationship import RelationshipObservation
from .language_capability_matrix.oracle.binding import LanguageScenarioBinding
from .language_capability_matrix.oracle.catalog import FixtureScenarioCatalog
from .language_capability_matrix.oracle.identities import FixtureSourceIdentities
from .language_capability_matrix.oracle.model_gap import ModelGapExpectation
from .language_capability_matrix.oracle.observation import PublicFactObservation
from .language_capability_matrix.oracle.ownership import FixtureSourceOwnership
from .language_capability_matrix.oracle.scenario_kind import ScenarioKind
from .language_capability_matrix.oracle.source_facts import SourceFactExpectation
from .language_capability_matrix.values.enums.claim_state import ClaimState
from .language_capability_matrix.values.enums.observation_kind import ObservationKind
from .language_capability_matrix.values.enums.type_slot_role import TypeSlotRole
from .language_capability_matrix.values.names.identifier import Identifier
from .language_capability_matrix.values.names.language_id import LanguageId
from .language_capability_matrix.values.names.scenario_id import ScenarioId
from .scenario_contract_error import ScenarioContractError
from .scenario_violation import ScenarioViolation


class FixtureClaimEvaluator:
    def evaluate_obligations(
        self,
        catalog: FixtureScenarioCatalog,
        results: dict[LanguageId, dict[ScenarioId, tuple[ClaimResult, ...]]],
        equivalence_cases: frozenset[ScenarioId],
    ) -> dict[LanguageId, dict[ScenarioId, tuple[ClaimResult, ...]]]:
        evaluated = {language: dict(cases) for language, cases in results.items()}
        for conclusion, obligation in catalog.obligations.items():
            for language, applicability in obligation.languages.items():
                if applicability.applicable:
                    missing = tuple(
                        scenario.value
                        for scenario in applicability.evidence
                        if not any(conclusion in result.conclusions for result in results[language][scenario])
                    )
                    if applicability.evidence and not missing:
                        continue
                    expected = json.dumps(tuple(scenario.value for scenario in applicability.evidence))
                    actual = json.dumps(missing) if applicability.evidence else "no native scenario selected"
                    discrepancy = Discrepancy.UNASSESSED
                else:
                    contradictory = tuple(
                        result
                        for scenario, items in results[language].items()
                        if scenario not in equivalence_cases
                        for result in items
                        if conclusion in result.conclusions
                    )
                    if not contradictory:
                        continue
                    expected = applicability.reason
                    actual = TypeAdapter(tuple[ClaimResult, ...]).dump_json(contradictory).decode()
                    discrepancy = Discrepancy.INVALID_EVIDENCE
                evaluated[language][ScenarioId(f"obligation-{conclusion}")] = (
                    ClaimResult(
                        subject=obligation.meaning,
                        expected=expected,
                        actual=actual,
                        discrepancies=(discrepancy,),
                        conclusions=(conclusion,),
                        owner_issue=95,
                    ),
                )
        return evaluated

    def evaluate_producer(
        self, producer: CodeMapProducer, contract: LanguageContract, descriptor: ExtractorDescriptor
    ) -> ClaimResult:
        expected = (
            descriptor.model_dump_json(),
            tuple((name.value, item.status.value) for name, item in contract.capabilities.items()),
            tuple(
                (name.value, item.semantics.value, item.inventory.value, name.evidence_requirements)
                for name, item in contract.relationships.items()
            ),
        )
        actual = (
            producer.extractor.model_dump_json(),
            tuple((item.capability.value, item.status.value) for item in producer.capabilities),
            tuple(
                (item.family.value, item.semantics.value, item.inventory.value, item.evidence_requirements)
                for item in producer.relationship_capabilities
            ),
        )
        return self.compare(
            "producer support and registered extractor",
            json.dumps(expected),
            json.dumps(actual),
            Discrepancy.FALSE_SUPPORT,
            (Conclusion.PROVENANCE,),
            95,
        )

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
        if set(code_map.extraction.files) != sources or not FixtureSourceOwnership(frozenset(sources)).accepts(
            code_map.dependency_graph, code_map.extraction.manifest
        ):
            return (
                ClaimResult(
                    subject="selected sources and dependency ownership",
                    expected=json.dumps(sorted(str(source) for source in sources)),
                    actual=code_map.model_dump_json(),
                    discrepancies=(Discrepancy.INVALID_EVIDENCE,),
                    conclusions=(Conclusion.SOURCE_INVENTORY,),
                    owner_issue=95,
                ),
            )
        expectation = catalog.expected[binding.scenario].root
        if expectation.kind is ScenarioKind.SOURCE_FACTS:
            provenance = self.compare(
                "structural source selection and scan policy",
                json.dumps((expectation.policy.model_dump_json(), len(sources), 0, 0, True)),
                json.dumps(
                    (
                        code_map.extraction.manifest.policy.model_dump_json(),
                        code_map.extraction.files_found,
                        code_map.extraction.files_excluded,
                        code_map.extraction.directories_pruned,
                        all(item.relative_path == item.source_id for item in code_map.extraction.manifest.sources),
                    )
                ),
                Discrepancy.INVALID_EVIDENCE,
                (Conclusion.SOURCE_INVENTORY, Conclusion.PROVENANCE),
                95,
            )
            return (
                provenance,
                *(
                    result
                    for authored, canonical in identities.sources.items()
                    for result in self.evaluate_source_facts(
                        identities.source(code_map.extraction.files[authored]),
                        expectation.sources[canonical],
                        code_map.producer,
                        catalog.model_gaps,
                    )
                ),
            )
        expected = expectation.code_map
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
            ClaimResult(
                subject="source selection, policy and artifact provenance",
                expected=expected.extraction.model_dump_json(exclude={"files", "import_identities"}),
                actual=code_map.extraction.model_dump_json(exclude={"files", "import_identities"}),
                discrepancies=() if provenance else (Discrepancy.INVALID_EVIDENCE,),
                conclusions=(Conclusion.SOURCE_INVENTORY, Conclusion.PROVENANCE),
                owner_issue=95,
            ),
            *(
                self.compare(
                    fact.model_dump_json(),
                    TypeAdapter(PublicFactObservation).dump_json(fact.read_expected(expected)).decode(),
                    TypeAdapter(PublicFactObservation).dump_json(fact.read_actual(code_map, identities)).decode(),
                    Discrepancy.INCORRECT,
                    (Conclusion.CONTRACT,),
                    95,
                )
                for fact in binding.facts
            ),
        )

    def evaluate_observation(
        self,
        source: SourceFile,
        wrapped: CapabilityObservation | RelationshipObservation,
        state: ClaimState,
        expected_source: SourceFile,
    ) -> ClaimResult:
        return self.observe(source, wrapped, state, expected_source).with_evidence(
            wrapped.model_dump_json(), expected_source.model_dump_json(), source.model_dump_json()
        )

    def observe(
        self,
        source: SourceFile,
        wrapped: CapabilityObservation | RelationshipObservation,
        state: ClaimState,
        expected_source: SourceFile,
    ) -> ClaimResult:
        observation = wrapped.root
        if observation.kind is ObservationKind.SOURCE:
            present = str(source.file_id) == observation.relative_path.value.as_posix()
        elif observation.kind is ObservationKind.EMPTY_SOURCE:
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
        elif observation.kind is ObservationKind.DECLARATION:
            present = any(
                declaration.declaration_id.qualified_name == observation.qualified_name.value
                and declaration.kind is observation.declaration_kind
                for declaration in source.declarations
            )
        elif observation.kind is ObservationKind.CALLABLE:
            present = any(
                callable_fact.qualified_name == observation.qualified_name.value
                and callable_fact.kind is observation.callable_kind
                for callable_fact in source.canonical_callables()
            )
        elif observation.kind is ObservationKind.CALL:
            present = any(
                callable_fact.qualified_name == observation.owner.value
                and call.target_name == observation.target.value
                and call.resolution is observation.resolution
                for callable_fact in source.canonical_callables()
                for call in source.calls
                if call.source_callable_id == callable_fact.declaration_id
            )
        elif observation.kind is ObservationKind.PARAMETER:
            expected_parameters = self.parameters(expected_source, observation.owner.value, observation.position.root)
            actual_parameters = self.parameters(source, observation.owner.value, observation.position.root)
            if state is ClaimState.ABSENT:
                return self.result(bool(actual_parameters), state)
            present = bool(expected_parameters) and actual_parameters == expected_parameters
        elif observation.kind is ObservationKind.PARAMETER_LIST:
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
        elif observation.kind is ObservationKind.TYPE_REFERENCE:
            expected_slots = self.type_slots(
                expected_source, observation.owner.value, observation.role, observation.position.root
            )
            present = (
                bool(expected_slots)
                and all(slot.kind is SourceTypeKind.REFERENCE for slot in expected_slots)
                and self.type_slots(source, observation.owner.value, observation.role, observation.position.root)
                == expected_slots
            )
        elif observation.kind is ObservationKind.TYPE_SLOT:
            slots = self.type_slots(source, observation.owner.value, observation.role, observation.position.root)
            if state is ClaimState.UNSUPPORTED:
                return self.result(any(slot.kind is SourceTypeKind.UNSUPPORTED for slot in slots), ClaimState.PRESENT)
            if state is ClaimState.ABSENT:
                return self.result(any(slot.kind is SourceTypeKind.ABSENT for slot in slots), ClaimState.PRESENT)
            present = any(slot.kind is SourceTypeKind.REFERENCE for slot in slots)
        elif observation.kind is ObservationKind.ANNOTATION:
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
        elif observation.kind is ObservationKind.MODIFIER:
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
        elif observation.kind is ObservationKind.ATTRIBUTE:
            present = any(
                declaration.declaration_id.qualified_name == observation.owner.value
                and attribute.name == observation.name.value
                and attribute.member_kind is observation.member_kind
                for declaration in source.declarations
                for attribute in declaration.properties
            )
        elif observation.kind is ObservationKind.ASSIGNED_VALUES:
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
        elif observation.kind is ObservationKind.DECLARATION_RELATION:
            present = any(
                relation.source_declaration_id.qualified_name == observation.source.value
                and relation.kind is observation.relation
                and relation.target_reference == observation.target.value
                for relation in source.declaration_relations
            )
        elif observation.kind is ObservationKind.NAMESPACE:
            present = any(
                namespace.qualified_name == observation.qualified_name.value
                and namespace.kind is observation.namespace_kind
                for namespace in source.namespaces
            )
        elif observation.kind is ObservationKind.DEPENDENCY:
            present = any(
                str(source.file_id) == observation.source.value.as_posix()
                and (str(dependency.target_file_id) if dependency.target_file_id is not None else str(dependency.path))
                == observation.target.value
                and dependency.resolution is observation.resolution
                for dependency in source.imports
            )
        elif observation.kind is ObservationKind.EXACT_SPAN:
            present = any(
                callable_fact.qualified_name == observation.owner.value
                and callable_fact.line_start == observation.start.root
                and callable_fact.line_end == observation.end.root
                for callable_fact in source.canonical_callables()
            )
        elif observation.kind is ObservationKind.SPAN_OWNER:
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
        if observation.kind is ObservationKind.SOURCE:
            present = any(
                source.relative_path == observation.relative_path.value.as_posix()
                for source in manifest.source_manifest.sources
            )
        elif observation.kind is ObservationKind.NAMESPACE:
            present = any(
                item.qualified_name == observation.qualified_name.value and item.kind is observation.namespace_kind
                for item in manifest.namespaces
            )
        elif observation.kind is ObservationKind.SYMBOL:
            present = any(
                item.qualified_name == observation.qualified_name.value and item.kind is observation.symbol_kind
                for item in manifest.symbols
            )
        elif observation.kind is ObservationKind.CALLABLE:
            present = any(
                item.symbol_id.qualified_name == observation.qualified_name.value
                and item.callable_kind is observation.callable_kind
                for item in manifest.callables
            )
        elif observation.kind is ObservationKind.PARAMETER:
            actual = tuple(
                item
                for item in manifest.parameters
                if item.callable_id.qualified_name == observation.owner.value
                and item.position == observation.position.root
            )
            if claim.state is ClaimState.ABSENT:
                return self.result(bool(actual), claim.state).with_evidence(
                    claim.model_dump_json(), "no selected parameter", manifest.model_dump_json()
                )
            parameters = self.parameters(expected, observation.owner.value, observation.position.root)
            present = any(
                item.name == parameter.name
                and item.kind is parameter.kind
                and item.has_default is parameter.has_default
                for item in actual
                for parameter in parameters
            )
        elif observation.kind is ObservationKind.ATTRIBUTE:
            present = any(
                item.owner_symbol_id.qualified_name == observation.owner.value
                and item.name == observation.name.value
                and item.member_kind is observation.member_kind
                for item in manifest.attributes
            )
        elif observation.kind is ObservationKind.CALL:
            present = any(
                item.source_callable_id.qualified_name == observation.owner.value
                and item.target_name == observation.target.value
                and item.resolution is observation.resolution
                for item in manifest.calls
            )
        elif observation.kind is ObservationKind.DECLARATION_RELATION:
            present = any(
                item.source_symbol_id.qualified_name == observation.source.value
                and item.kind is observation.relation
                and item.target_reference == observation.target.value
                for item in manifest.declaration_relations
            )
        elif observation.kind is ObservationKind.DEPENDENCY:
            present = any(
                str(item.source_id) == observation.source.value.as_posix()
                and item.target == observation.target.value
                and item.resolution is observation.resolution
                for item in manifest.dependencies
            )
        else:
            assert_never(observation)
        return self.result(present, claim.state).with_evidence(
            claim.model_dump_json(), expected.model_dump_json(), manifest.model_dump_json()
        )

    def result(self, present: bool, state: ClaimState) -> ClaimResult:
        if state is ClaimState.PRESENT:
            return self.compare(
                "presence",
                "present",
                "present" if present else "absent",
                Discrepancy.MISSING,
                (Conclusion.CONTRACT,),
                95,
            )
        if state is ClaimState.ABSENT:
            return self.compare(
                "absence", "absent", "present" if present else "absent", Discrepancy.EXTRA, (Conclusion.CONTRACT,), 95
            )
        raise ScenarioContractError(ScenarioViolation.UNSUPPORTED_CLAIM_STATE, state.value)

    def compare(
        self,
        subject: str,
        expected: str,
        actual: str,
        failure: Discrepancy,
        conclusions: tuple[Conclusion, ...],
        owner_issue: int,
    ) -> ClaimResult:
        return ClaimResult(
            subject=subject,
            expected=expected,
            actual=actual,
            discrepancies=() if expected == actual else (failure,),
            conclusions=conclusions,
            owner_issue=owner_issue,
        )

    def inventory(
        self,
        subject: str,
        expected: tuple[tuple[str, ...], ...],
        actual: tuple[tuple[str, ...], ...],
        conclusion: Conclusion,
    ) -> ClaimResult:
        missing = Counter(expected) - Counter(actual)
        extra = Counter(actual) - Counter(expected)
        return ClaimResult(
            subject=subject,
            expected=json.dumps(sorted(expected)),
            actual=json.dumps(sorted(actual)),
            discrepancies=(
                *((Discrepancy.MISSING,) if missing else ()),
                *((Discrepancy.EXTRA,) if extra else ()),
            ),
            conclusions=(conclusion,),
            owner_issue=81,
        )

    def evaluate_source_facts(
        self,
        source: SourceFile,
        expected: SourceFactExpectation,
        producer: CodeMapProducer,
        model_gaps: dict[Identifier, ModelGapExpectation],
    ) -> tuple[ClaimResult, ...]:
        callables = source.canonical_callables()
        inventories = (
            self.inventory(
                f"{source.file_id}:{Conclusion.DECLARATIONS}:declarations",
                tuple((item.qualified_name.value, item.declaration_kind.value) for item in expected.declarations),
                tuple((item.declaration_id.qualified_name, item.kind.value) for item in source.declarations),
                Conclusion.DECLARATIONS,
            ),
            self.inventory(
                f"{source.file_id}:{Conclusion.CALLABLES}:callables",
                tuple((item.qualified_name.value, item.callable_kind.value) for item in expected.callables),
                tuple((item.qualified_name, item.kind.value) for item in callables),
                Conclusion.CALLABLES,
            ),
            self.inventory(
                f"{source.file_id}:{Conclusion.PROPERTIES}:properties",
                tuple((item.owner.value, item.name.value, item.member_kind.value) for item in expected.attributes),
                tuple(
                    (item.owner_declaration_id.qualified_name, item.name, item.member_kind.value)
                    for declaration in source.declarations
                    for item in declaration.properties
                ),
                Conclusion.PROPERTIES,
            ),
        )
        namespaces = self.inventory(
            f"{source.file_id}:{Conclusion.DECLARATIONS}:namespaces",
            tuple((item.qualified_name.value, item.namespace_kind.value) for item in expected.namespaces),
            tuple((item.qualified_name, item.kind.value) for item in source.namespaces),
            Conclusion.DECLARATIONS,
        )
        owners = tuple(
            (method.qualified_name, method.owner_declaration_id.qualified_name)
            for declaration in source.declarations
            for method in (*declaration.methods, *declaration.abstract_methods)
        )
        ownership = tuple(
            self.compare(
                f"{source.file_id}:{Conclusion.OWNERSHIP}:{name.value}",
                json.dumps([owner.value]),
                json.dumps(sorted({owner_name for callable_name, owner_name in owners if callable_name == name.value})),
                Discrepancy.WRONG_OWNER if any(item[0] == name.value for item in owners) else Discrepancy.MISSING,
                (Conclusion.OWNERSHIP,),
                81,
            )
            for name, owner in expected.owners.items()
        )
        located_owners = tuple(
            self.compare(
                f"{source.file_id}:{Conclusion.OWNERSHIP}:{span.owner.value}:owner at authored span",
                json.dumps([expected.owners[span.owner].value]),
                json.dumps(
                    [
                        method.owner_declaration_id.qualified_name
                        for declaration in source.declarations
                        for method in (*declaration.methods, *declaration.abstract_methods)
                        if method.line_start == span.start.root and method.line_end == span.end.root
                    ]
                ),
                Discrepancy.WRONG_OWNER,
                (Conclusion.OWNERSHIP,),
                81,
            )
            for span in expected.spans
        )
        signatures = tuple(
            self.compare(
                f"{source.file_id}:{Conclusion.CALLABLES}:{name.value}:signatures",
                TypeAdapter(tuple[SourceSignature, ...]).dump_json(items).decode(),
                TypeAdapter(tuple[SourceSignature, ...])
                .dump_json(
                    tuple(
                        item
                        for declaration in source.declarations
                        if declaration.declaration_id.qualified_name == name.value
                        for item in declaration.signatures
                    )
                )
                .decode(),
                Discrepancy.INCORRECT,
                (Conclusion.CALLABLES,),
                106,
            )
            for name, items in expected.signatures.items()
        )
        parameters = tuple(
            self.compare(
                f"{source.file_id}:{Conclusion.PARAMETERS}:{name.value}",
                TypeAdapter(tuple[tuple[SourceParameter, ...], ...]).dump_json((items,)).decode(),
                TypeAdapter(tuple[tuple[SourceParameter, ...], ...])
                .dump_json(
                    tuple(callable_.parameters for callable_ in callables if callable_.qualified_name == name.value)
                )
                .decode(),
                Discrepancy.INCORRECT
                if any(item.qualified_name == name.value for item in callables)
                else Discrepancy.MISSING,
                (Conclusion.PARAMETERS,),
                106,
            )
            for name, items in expected.parameters.items()
        )
        returns = tuple(
            self.compare(
                f"{source.file_id}:{Conclusion.TYPES}:{name.value}",
                TypeAdapter(tuple[SourceTypeReference, ...]).dump_json((type_,)).decode(),
                TypeAdapter(tuple[SourceTypeReference | SourceTypeAbsent | SourceTypeUnsupported, ...])
                .dump_json(tuple(item.return_type for item in callables if item.qualified_name == name.value))
                .decode(),
                Discrepancy.INCORRECT,
                (Conclusion.TYPES,),
                106,
            )
            for name, type_ in expected.returns.items()
        )
        gaps = tuple(
            ClaimResult(
                subject=f"{source.file_id}:{gap.conclusion}:{identifier}",
                expected=required_fact,
                actual=gap.missing_representation,
                discrepancies=(gap.state,),
                conclusions=(gap.conclusion,),
                owner_issue=gap.owner_issue,
            )
            for identifier, required_fact in expected.gaps.items()
            for gap in (model_gaps[identifier],)
        )
        completeness = tuple(
            ClaimResult(
                subject=f"{source.file_id}:{Conclusion.COMPLETENESS}:member inventory claim",
                expected="an incomplete member inventory cannot be declared supported",
                actual=item.model_dump_json(),
                discrepancies=(Discrepancy.FALSE_COMPLETENESS,),
                conclusions=(Conclusion.COMPLETENESS,),
                owner_issue=104,
            )
            for item in producer.relationship_capabilities
            if item.family is RelationshipFamily.MEMBER
            and item.inventory is CapabilityStatus.SUPPORTED
            and any(not result.satisfied for result in inventories[1:])
        )
        claims = {item.capability: item for item in producer.capabilities}
        support = tuple(
            ClaimResult(
                subject=f"{result.subject}:producer support",
                expected="supported coverage must satisfy the selected representable source fact",
                actual=claims[capability].model_dump_json(),
                discrepancies=(Discrepancy.FALSE_SUPPORT,),
                conclusions=result.conclusions,
                owner_issue=result.owner_issue,
            )
            for capability, result in (
                *zip(
                    (FactCapability.SYMBOLS, FactCapability.CALLABLES, FactCapability.ATTRIBUTES),
                    inventories,
                    strict=True,
                ),
                *((FactCapability.PARAMETERS, result) for result in parameters),
            )
            if not result.satisfied and claims[capability].status is CapabilityStatus.SUPPORTED
        )
        return (
            *inventories,
            namespaces,
            *ownership,
            *located_owners,
            *signatures,
            *parameters,
            *returns,
            *gaps,
            *completeness,
            *support,
        )
