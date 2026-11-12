from enum import StrEnum


class Discrepancy(StrEnum):
    MISSING = "missing"
    EXTRA = "extra"
    INCORRECT = "incorrect"
    WRONG_OWNER = "wrong_owner"
    FALSE_COMPLETENESS = "false_completeness"
    FALSE_SUPPORT = "false_support"
    MODEL_GAP = "model_gap"
    EXTRACTION_FAILURE = "extraction_failure"
    UNASSESSED = "unassessed"
    INVALID_EVIDENCE = "invalid_evidence"
