from ....extraction.extractors.models.extractor_error import ExtractorError
from ....shared.code.models.identity import FileId
from .extractor_contract_violation import ExtractorContractViolation


class ExtractorContractError(ExtractorError):
    """Report extractor output that violates the registered runtime contract."""

    code = "extractor_contract"

    def __init__(
        self,
        language: str,
        violation: ExtractorContractViolation,
        missing_source_ids: tuple[FileId, ...],
        unexpected_source_ids: tuple[FileId, ...],
        duplicate_source_ids: tuple[FileId, ...],
        diagnostic: str,
    ) -> None:
        self.language = language
        self.violation = violation
        self.missing_source_ids = missing_source_ids
        self.unexpected_source_ids = unexpected_source_ids
        self.duplicate_source_ids = duplicate_source_ids
        self.diagnostic = diagnostic
        super().__init__(
            f"{language} extractor violated its {violation} contract "
            f"(missing={tuple(map(str, missing_source_ids))}, "
            f"unexpected={tuple(map(str, unexpected_source_ids))}, "
            f"duplicate={tuple(map(str, duplicate_source_ids))}, diagnostic={diagnostic!r})."
        )
