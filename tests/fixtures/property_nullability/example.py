import typing
from typing import Annotated, Callable, Optional


class Example:
    callback: Callable[[int], None]
    optional_callback: Callable[[int], None] | None
    nullable_elements: list[int | None]
    optional_container: Optional[list[int | None]]
    optional_union: typing.Union[int, None]
    annotated_required: Annotated[int, None]
    annotated_optional: Annotated[int | None, "example"]
    qualified_required: typing.Callable[[], None]
    qualified_optional: typing.Optional[int]
    default_none: Callable[[], None] = None
