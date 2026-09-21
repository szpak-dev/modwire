from ....shared.values.models.value_model import ValueModel
from .source_entry import SourceEntry


class SourceInventory(ValueModel):
    entries: tuple[SourceEntry, ...]
    files_found: int
    files_excluded: int
    directories_pruned: int
