from enum import StrEnum


class ImplementationManifestViolation(StrEnum):
    """Identify the implementation-manifest invariant violated by canonical facts."""

    NON_CANONICAL_ORDER = "non_canonical_order"
    DUPLICATE_FACT = "duplicate_fact"
    DUPLICATE_IDENTITY = "duplicate_identity"
    UNKNOWN_REFERENCE = "unknown_reference"
    INCONSISTENT_DEPENDENCY = "inconsistent_dependency"
    INCONSISTENT_CALL = "inconsistent_call"
    INCONSISTENT_CALL_SOURCE = "inconsistent_call_source"
    MISSING_DEPENDENCY_TARGET_SOURCE = "missing_dependency_target_source"
    NON_IMPORT_MANIFEST_DEPENDENCY = "non_import_manifest_dependency"
    INCONSISTENT_ATTRIBUTE_IDENTITY = "inconsistent_attribute_identity"
    INVALID_DOCUMENT_DIGEST = "invalid_document_digest"
