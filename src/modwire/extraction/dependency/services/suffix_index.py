from ....shared.code.models.identity import FileId


class SuffixIndex:
    def __init__(self) -> None:
        self._empty: dict[str, set[FileId]] = {}
        self._terminal: dict[tuple[str, str], set[FileId]] = {}
        self._singleton: dict[tuple[str, str], set[FileId]] = {}
        self._terminal_pair: dict[tuple[str, str, str], set[FileId]] = {}

    def add(self, group: str, identity: str, file_id: FileId) -> None:
        if not identity:
            self._empty.setdefault(group, set()).add(file_id)
            return
        parts = identity.split("/")
        self._terminal.setdefault((group, parts[-1]), set()).add(file_id)
        if len(parts) == 1:
            self._singleton.setdefault((group, parts[-1]), set()).add(file_id)
            return
        self._terminal_pair.setdefault((group, parts[-2], parts[-1]), set()).add(file_id)

    def find(self, group: str, identity: str) -> set[FileId]:
        if not identity:
            return set(self._empty.get(group, ()))
        parts = identity.split("/")
        if len(parts) == 1:
            return set(self._terminal.get((group, parts[-1]), ()))
        candidates = set(self._singleton.get((group, parts[-1]), ()))
        candidates.update(self._terminal_pair.get((group, parts[-2], parts[-1]), ()))
        return candidates
