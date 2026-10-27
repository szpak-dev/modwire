def example_target(example_value: str) -> str:
    return example_value


def example_source(example_value: str) -> str:
    example_target(example_value)
    return example_target(example_value)
