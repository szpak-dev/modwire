from enum import StrEnum


class RuntimeViolation(StrEnum):
    LANGUAGE_IDENTITY = "language_identity"
    RUNTIME_IDENTITY = "runtime_identity"
    UNAVAILABLE = "unavailable"
    PROBE_FAILED = "probe_failed"
    VERSION_MISMATCH = "version_mismatch"
    PACKAGE_UNAVAILABLE = "package_unavailable"
