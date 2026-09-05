from modwire.shared.values.models.value_model import ValueModel

from .python_source_input import PythonSourceInput


class PythonCommandInput(ValueModel):
    batch: bool
    sources: tuple[PythonSourceInput, ...]
