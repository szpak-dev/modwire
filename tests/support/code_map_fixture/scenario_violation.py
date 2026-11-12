from enum import StrEnum


class ScenarioViolation(StrEnum):
    EXPECTED_CODE_MAP = "expected_code_map"
    SOURCE_DOCUMENTS = "source_documents"
    SOURCE_OWNERSHIP = "source_ownership"
    UNKNOWN_PRODUCER = "unknown_producer"
    UNUSED_PRODUCER = "unused_producer"
    OBLIGATION_COVERAGE = "obligation_coverage"
    UNKNOWN_EVIDENCE = "unknown_evidence"
    MODEL_GAP_REFERENCES = "model_gap_references"
    UNSUPPORTED_CLAIM_STATE = "unsupported_claim_state"
