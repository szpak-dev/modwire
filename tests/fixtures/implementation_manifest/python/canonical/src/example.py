from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar

EXAMPLE_CONSTANT = "example"


class ExampleContract(ABC):
    example_shared: str = "shared"

    @abstractmethod
    def example_required(self, example_value: str) -> str:
        raise NotImplementedError


class ExampleImplementation(ExampleContract):
    example_static: ClassVar[str] = "static"
    example_optional: str | None = None

    def __init__(self, example_name: str):
        self.example_name = example_name

    @staticmethod
    def example_factory(example_value: str) -> str:
        return example_value

    def example_required(self, example_value: str) -> str:
        return example_value

    def example_path(self, example_root: Path) -> str:
        return str(example_root / self.example_required(self.example_name))


async def example_async(example_value: str, *, example_suffix: str = "suffix") -> str:
    return example_value + example_suffix
