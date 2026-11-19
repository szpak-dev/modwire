from ....extraction.extractors.models.extraction_error import ExtractionError
from ....shared.code.models.sources.identity import FileId
from ....shared.failures.models.modwire_error_code import ModwireErrorCode


class SourceObservationInvalidatedError(ExtractionError):
    """Report exact source identities that changed after their observation."""

    code = ModwireErrorCode.SOURCE_OBSERVATION_INVALIDATED

    def __init__(
        self,
        added: tuple[FileId, ...],
        removed: tuple[FileId, ...],
        changed: tuple[FileId, ...],
    ) -> None:
        self.added = added
        self.removed = removed
        self.changed = changed
        super().__init__(
            "Source observation was invalidated "
            f"(added={tuple(map(str, added))}, removed={tuple(map(str, removed))}, "
            f"changed={tuple(map(str, changed))})."
        )
