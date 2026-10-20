from enum import StrEnum


class ArchitectureConfigViolation(StrEnum):
    DUPLICATE_FLOW_REALM = "duplicate_flow_realm"
    DUPLICATE_FLOW_ANALYZER = "duplicate_flow_analyzer"
    DUPLICATE_SHAPE_REALM = "duplicate_shape_realm"
    DUPLICATE_ARCHITECTURE_TAG = "duplicate_architecture_tag"
    UNKNOWN_BOUNDARY_REALM = "unknown_boundary_realm"
