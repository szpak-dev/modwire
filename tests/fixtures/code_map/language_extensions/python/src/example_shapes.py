from abc import ABC, abstractmethod
from pathlib import Path

EXAMPLE_CONSTANT = "example_constant"
EXAMPLE_REFERENCE = "example"
example_variable = "example_variable"


def example_factory() -> object:
    return object()


class ExampleAssignedValues:
    example_unassigned: str
    example_literal = 1
    example_reference: str = EXAMPLE_REFERENCE
    example_call = example_factory()
    example_unresolved = 1 + 2

    def __init__(self, example_input: str):
        self.example_reference = example_input
        if example_input:
            self.example_nested = 1
        self.example_nested = 2


class ExampleContract(ABC):
    example_shared: str = "example"

    @abstractmethod
    def example_required(self, example_value: str) -> str:
        raise NotImplementedError

    def example_concrete(self) -> str:
        return "example_value"


class ExampleImplementation(ExampleContract):
    example_optional: str | None = None

    @staticmethod
    def example_static(example_value: str) -> str:
        return example_value

    def example_required(self, example_value: str) -> str:
        return example_value

    def example_path(self, example_root: Path) -> str:
        return str(example_root / self.example_required("example"))


async def example_async(example_value: str, *, example_suffix: str = "example_suffix") -> str:
    return example_value + example_suffix


def example_outer(example_value: str) -> str:
    def example_inner(example_input: str) -> str:
        return example_input

    return example_inner(example_value)
