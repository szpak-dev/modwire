from enum import StrEnum


class CacheViolation(StrEnum):
    SOURCE_IDENTITY_MISMATCH = "source_identity_mismatch"
    CODE_MAP_PROVENANCE_MISMATCH = "code_map_provenance_mismatch"
    REPORT_COLLECTION_INVALID = "report_collection_invalid"
    REPORT_ENTRY_INVALID = "report_entry_invalid"
    REPORT_MODEL_OUTSIDE_ARCHITECTURE = "report_model_outside_architecture"
    REPORT_MODEL_NOT_NODE = "report_model_not_node"
    EMPTY_CACHE_LOCATION = "empty_cache_location"
    INVALID_CACHE_CAPACITY = "invalid_cache_capacity"
    EMPTY_CACHE_OUTCOME_NAMESPACE = "empty_cache_outcome_namespace"
    NEGATIVE_CACHE_OUTCOME_COUNT = "negative_cache_outcome_count"
    MISSING_CACHE_OUTCOME = "missing_cache_outcome"
    DUPLICATE_CACHE_STAGE_OUTCOME = "duplicate_cache_stage_outcome"
    INAPPLICABLE_CACHE_STAGE = "inapplicable_cache_stage"
