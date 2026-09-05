from abc import ABC, abstractmethod


class ExampleContract(ABC):
    @abstractmethod
    def example_required(self, example_value: str) -> str:
        raise NotImplementedError

    def example_concrete(self) -> str:
        return "example_value"


class ExampleImplementation(ExampleContract):
    example_optional: str | None

    def example_required(self, example_value: str) -> str:
        return example_value


async def example_async(example_value: str, *, example_suffix: str = "example_suffix") -> str:
    return example_value + example_suffix


def example_outer(example_value: str) -> str:
    def example_inner(example_input: str) -> str:
        return example_input

    return example_inner(example_value)
