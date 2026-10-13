from ....extraction.extractors.models.extraction_error import ExtractionError
from ....shared.code.models.identity import FileId


class SourceObservationInvalidatedError(ExtractionError):
    """Report exact source identities that changed after their observation."""

    code = "source_observation_invalidated"

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
