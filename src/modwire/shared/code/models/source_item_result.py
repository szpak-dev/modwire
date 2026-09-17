from .source_file_result import SourceFileResult


class SourceItemResult[SourceItem](SourceFileResult):
    item: SourceItem
