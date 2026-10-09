from .identity import FileId
from .identity_kind import IdentityKind


class DuplicateIdentityError(ValueError):
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
        return {
            "code": self.code,
            "identity_kind": self.identity_kind,
            "identity": self.identity,
            "existing_file_id": self.existing_file_id,
            "duplicate_file_id": self.duplicate_file_id,
        }
