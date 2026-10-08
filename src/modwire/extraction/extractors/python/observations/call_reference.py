from dataclasses import dataclass


@dataclass(frozen=True)
class PythonCallReference:
    expression: str
    target_name: str
    local_name: str
    constructor_name: str
    instance_qualified_name: str
    is_reference: bool
