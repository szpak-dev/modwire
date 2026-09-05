from modwire.shared.values.models.value_model import ValueModel


class CallableReportEntry(ValueModel):
    source_callable: str
    calls: tuple[str, ...]
    callers: tuple[str, ...]
