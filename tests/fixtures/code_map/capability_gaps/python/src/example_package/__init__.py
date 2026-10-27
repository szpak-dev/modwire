from typing import final

EXAMPLE_PACKAGE_VALUE = "example_value"


def example_annotation(example_declaration: type) -> type:
    example_declaration.example_runtime_annotation = "example_runtime_annotation"
    return example_declaration


@example_annotation
@final
class ExampleBase:
    example_value: str = "example_value"


ExampleAlias = ExampleBase


class ExampleRuntime(ExampleAlias):
    pass


ExampleBase.example_runtime_member = "example_runtime_member"
