from dataclasses import dataclass


@dataclass(frozen=True)
class PythonCallReference:
    expression: str
    target_name: str
    is_reference: bool
