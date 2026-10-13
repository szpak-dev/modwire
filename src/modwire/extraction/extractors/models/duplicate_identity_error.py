from ....shared.code.models.identity import FileId
from ....shared.code.models.identity_kind import IdentityKind
from .extraction_error import ExtractionError


class DuplicateIdentityError(ExtractionError):
    """Report two source files that claim the same extracted identity."""

    code = "duplicate_identity"

    def __init__(
        self,
        identity_kind: IdentityKind,
        identity: str,
        existing_file_id: FileId,
        duplicate_file_id: FileId,
    ) -> None:
        self.identity_kind = identity_kind
        self.identity = identity
        self.existing_file_id = existing_file_id
        self.duplicate_file_id = duplicate_file_id
        super().__init__(
            f"Duplicate {identity_kind} identity {identity!r}: {existing_file_id!r} and {duplicate_file_id!r}"
        )

    def as_dict(self) -> dict[str, str]:
        """Return stable machine-readable evidence for the duplicate identity."""

        return {
            "code": self.code,
            "identity_kind": self.identity_kind,
            "identity": self.identity,
            "existing_file_id": self.existing_file_id,
            "duplicate_file_id": self.duplicate_file_id,
        }
