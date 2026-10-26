class ExampleValue:
    pass


def example_inner() -> int:
    return 1


def example_outer(example_value: int) -> int:
    return example_value


def example_mixed_caller() -> None:
    example_outer(example_inner())
    ExampleValue()
