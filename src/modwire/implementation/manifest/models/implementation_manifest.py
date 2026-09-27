import json
from typing import Literal, Self

from pydantic import model_validator

from ....shared.code.models.code_map_producer import CodeMapProducer
from ....shared.code.models.source_manifest import SourceManifest
from ....shared.values.models.value_model import ValueModel
from .manifest_annotation import ManifestAnnotation
from .manifest_attribute import ManifestAttribute
from .manifest_callable import ManifestCallable
from .manifest_dependency import ManifestDependency
from .manifest_inheritance import ManifestInheritance
from .manifest_parameter import ManifestParameter
from .manifest_span import ManifestSpan
from .manifest_symbol import ManifestSymbol


class ImplementationManifest(ValueModel):
    """A versioned, language-neutral statement of observed implementation facts and provenance."""

    schema_version: Literal[2] = 2
    producer: CodeMapProducer
    source_manifest: SourceManifest
    symbols: tuple[ManifestSymbol, ...]
    callables: tuple[ManifestCallable, ...]
    parameters: tuple[ManifestParameter, ...]
    attributes: tuple[ManifestAttribute, ...]
    annotations: tuple[ManifestAnnotation, ...]
    inheritance: tuple[ManifestInheritance, ...]
    dependencies: tuple[ManifestDependency, ...]
    spans: tuple[ManifestSpan, ...]

    @model_validator(mode="after")
    def validate_facts(self) -> Self:
        """Validate canonical ordering, identity uniqueness, and fact references."""

        collections = (
            self.symbols,
            self.callables,
            self.parameters,
            self.attributes,
            self.annotations,
            self.inheritance,
            self.dependencies,
            self.spans,
        )
        for collection in collections:
            keys = tuple(
                json.dumps(item.model_dump(mode="json"), ensure_ascii=False, separators=(",", ":"), sort_keys=True)
                for item in collection
            )
            if keys != tuple(sorted(keys)):
                raise ValueError("Implementation manifest fact collections must be canonically ordered.")
            if len(keys) != len(set(keys)):
                raise ValueError("Implementation manifest fact collections must not contain duplicates.")

        symbol_ids = {item.id.canonical() for item in self.symbols}
        if len(symbol_ids) != len(self.symbols):
            raise ValueError("Implementation manifest declaration identities must be unique.")
        source_ids = {str(item.source_id) for item in self.source_manifest.sources}
        if any(str(item.id.source_id) not in source_ids for item in self.symbols):
            raise ValueError("Implementation manifest symbols must reference manifest sources.")
        callable_ids = {item.symbol_id.canonical() for item in self.callables}
        if len(callable_ids) != len(self.callables):
            raise ValueError("Implementation manifest callable identities must be unique.")
        if not callable_ids <= symbol_ids:
            raise ValueError("Implementation manifest callables must reference declared symbols.")
        parameter_ids = {item.id for item in self.parameters}
        if len(parameter_ids) != len(self.parameters):
            raise ValueError("Implementation manifest parameter identities must be unique.")
        parameter_positions = {(item.callable_id.canonical(), item.position) for item in self.parameters}
        if len(parameter_positions) != len(self.parameters):
            raise ValueError("Implementation manifest parameter positions must be unique per callable.")
        if any(item.callable_id.canonical() not in callable_ids for item in self.parameters):
            raise ValueError("Implementation manifest parameters must reference declared callables.")
        attribute_ids = {item.id for item in self.attributes}
        if len(attribute_ids) != len(self.attributes):
            raise ValueError("Implementation manifest attribute identities must be unique per symbol.")
        if any(item.owner_symbol_id.canonical() not in symbol_ids for item in self.attributes):
            raise ValueError("Implementation manifest attributes must reference declared symbols.")
        targets = symbol_ids | parameter_ids | attribute_ids
        if any(item.target_id not in targets for item in self.annotations):
            raise ValueError("Implementation manifest annotations must reference declared facts.")
        if any(item.source_symbol_id.canonical() not in symbol_ids for item in self.inheritance):
            raise ValueError("Implementation manifest inheritance must reference declared symbols.")
        span_targets = {item.target_id for item in self.spans}
        if len(span_targets) != len(self.spans):
            raise ValueError("Implementation manifest spans must be unique per symbol.")
        if any(item.target_id not in symbol_ids for item in self.spans):
            raise ValueError("Implementation manifest spans must reference declared symbols.")
        if any(item.source_id not in source_ids for item in self.dependencies):
            raise ValueError("Implementation manifest dependencies must originate from manifest sources.")
        if any(item.target_kind == "source" and item.target not in source_ids for item in self.dependencies):
            raise ValueError("Implementation manifest source dependencies must target manifest sources.")
        expected_resolutions = {
            "source": "resolved",
            "external": "external",
            "unresolved": "unresolved",
        }
        if any(expected_resolutions[item.target_kind] != item.resolution for item in self.dependencies):
            raise ValueError("Implementation manifest dependency targets must agree with their resolution.")
        return self
