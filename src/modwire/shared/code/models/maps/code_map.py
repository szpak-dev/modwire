from typing import ClassVar, Self

from pydantic import model_validator

from ....values.models.value_model import ValueModel
from ..callables.source_call_resolution import SourceCallResolution
from ..capabilities.capability_status import CapabilityStatus
from ..capabilities.fact_capability import FactCapability
from ..dependencies.dependency_graph import DependencyGraph
from ..failures.code_validation_error import CodeValidationError
from ..failures.code_violation import CodeViolation
from ..source_types.absent import SourceTypeAbsent
from ..source_types.kind import SourceTypeKind
from ..source_types.reference import SourceTypeReference
from ..source_types.unsupported import SourceTypeUnsupported
from ..sources.source_extraction import SourceExtraction
from ..sources.source_file import SourceFile
from .code_map_producer import CodeMapProducer


class CodeMap(ValueModel):
    schema_version: ClassVar[int] = 13
    language: str
    producer: CodeMapProducer
    extraction: SourceExtraction
    dependency_graph: DependencyGraph

    @model_validator(mode="after")
    def validate_facts(self) -> Self:
        self.validate_producer_language()
        self.validate_resolved_call_targets()
        self.validate_type_capability()
        return self

    def validate_producer_language(self) -> None:
        if self.language != self.producer.extractor.language:
            raise CodeValidationError(CodeViolation.INCONSISTENT_PRODUCER_LANGUAGE, self.language)

    def validate_resolved_call_targets(self) -> None:
        callable_ids = {
            item.declaration_id.canonical()
            for source_file in self.extraction.files.values()
            for item in source_file.canonical_callables()
        }
        if any(
            call.resolution is SourceCallResolution.RESOLVED
            and (call.target_callable_id is None or call.target_callable_id.canonical() not in callable_ids)
            for source_file in self.extraction.files.values()
            for call in source_file.calls
        ):
            raise CodeValidationError(CodeViolation.UNKNOWN_RESOLVED_CALL_TARGET, self.language)

    def validate_type_capability(self) -> None:
        coverage = next(
            item for item in self.producer.capabilities if item.capability is FactCapability.TYPE_REFERENCES
        )
        slots = tuple(slot for source_file in self.extraction.files.values() for slot in self.type_slots(source_file))
        kinds = tuple(kind for slot in slots for kind in self.type_kinds(slot))
        has_unsupported = SourceTypeKind.UNSUPPORTED in kinds
        has_observed = any(kind in {SourceTypeKind.REFERENCE, SourceTypeKind.ABSENT} for kind in kinds)
        if coverage.status is CapabilityStatus.SUPPORTED and has_unsupported:
            raise CodeValidationError(
                CodeViolation.UNSUPPORTED_TYPE_WITH_SUPPORTED_CAPABILITY,
                self.language,
            )
        if coverage.status is CapabilityStatus.UNSUPPORTED and has_observed:
            raise CodeValidationError(
                CodeViolation.OBSERVED_TYPE_WITH_UNSUPPORTED_CAPABILITY,
                self.language,
            )

    def type_slots(
        self,
        source_file: SourceFile,
    ) -> tuple[SourceTypeReference | SourceTypeAbsent | SourceTypeUnsupported, ...]:
        callables = source_file.canonical_callables()
        return (
            *(callable.return_type for callable in callables),
            *(parameter.type for callable in callables for parameter in callable.parameters),
            *(property_.type for declaration in source_file.declarations for property_ in declaration.properties),
        )

    def type_kinds(
        self,
        slot: SourceTypeReference | SourceTypeAbsent | SourceTypeUnsupported,
    ) -> tuple[SourceTypeKind, ...]:
        if slot.kind is not SourceTypeKind.REFERENCE:
            return (slot.kind,)
        return (
            slot.kind,
            *(kind for argument in slot.arguments for kind in self.type_kinds(argument)),
        )

    def type_reference_names(
        self,
        slot: SourceTypeReference | SourceTypeAbsent | SourceTypeUnsupported,
    ) -> tuple[str, ...]:
        if slot.kind is not SourceTypeKind.REFERENCE:
            return ()
        return (
            slot.name,
            *(name for argument in slot.arguments for name in self.type_reference_names(argument)),
        )

    def nested_type_reference_names(
        self,
        slot: SourceTypeReference | SourceTypeAbsent | SourceTypeUnsupported,
    ) -> tuple[str, ...]:
        if slot.kind is not SourceTypeKind.REFERENCE:
            return ()
        return tuple(name for argument in slot.arguments for name in self.type_reference_names(argument))

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
