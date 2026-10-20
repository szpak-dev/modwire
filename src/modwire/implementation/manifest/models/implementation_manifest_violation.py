from enum import StrEnum


class ImplementationManifestViolation(StrEnum):
    """Identify the implementation-manifest invariant violated by canonical facts."""

    NON_CANONICAL_ORDER = "non_canonical_order"
    DUPLICATE_FACT = "duplicate_fact"
    DUPLICATE_IDENTITY = "duplicate_identity"
    UNKNOWN_REFERENCE = "unknown_reference"
    INCONSISTENT_DEPENDENCY = "inconsistent_dependency"
