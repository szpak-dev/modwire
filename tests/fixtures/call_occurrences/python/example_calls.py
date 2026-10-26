def example_target() -> int:
    return 1


def example_caller() -> None:
    example_target()
    example_target()
