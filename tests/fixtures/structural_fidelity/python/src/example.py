from collections.abc import Callable


type ExampleAlias = dict[str, int]


class ExampleGeneric[T: str]:
    pass


class ExampleOwner:
    example_value: str

    class ExampleNested:
        def example_method(self, example_value: str) -> str:
            return example_value

    def example_method(example_receiver, example_value: str) -> str:
        return example_value

    @staticmethod
    def example_static(self: str) -> str:
        return self

    @property
    def example_property(self) -> str:
        return self.example_value

    @example_property.setter
    def example_property(self, example_value: str) -> None:
        self.example_value = example_value


class ExampleOther:
    example_value: int

    def example_method(self, example_value: int) -> int:
        return example_value


def example_function(self: str, example_value: int, /, *, example_named: str = "") -> str:
    class ExampleLocal:
        pass

    return self


def example_types(
    example_mixed: dict[str, list[int | None]],
    example_quoted: "ExampleOwner",
    example_tuple: tuple[str, int],
    example_callable: Callable[[str], int],
) -> ExampleAlias:
    return {}
