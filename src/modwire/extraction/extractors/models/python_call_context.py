from modwire.shared.values.models.value_model import ValueModel


class PythonCallContext(ValueModel):
    source_id: str
    source_callable_id: str
    owner_name: str
    by_name: dict[str, str]
    by_qualified_name: dict[str, str]
    constructors_by_name: dict[str, str]
