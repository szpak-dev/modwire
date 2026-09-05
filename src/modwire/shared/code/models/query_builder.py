from collections.abc import Callable

from ...values.models.value_model import ValueModel


class QueryBuilder[T](ValueModel):
    items: tuple[T, ...]
    predicates: tuple[Callable[[T], bool], ...] = ()

    def where(self, predicate: Callable[[T], bool]) -> "QueryBuilder[T]":
        return QueryBuilder(items=self.items, predicates=(*self.predicates, predicate))

    def where_equal(self, selector: Callable[[T], object], expected: object) -> "QueryBuilder[T]":
        return self.where(lambda item: selector(item) == expected)

    def where_contains(
        self, selector: Callable[[T], str], expected: str, *, case_sensitive: bool = True
    ) -> "QueryBuilder[T]":
        if case_sensitive:
            return self.where(lambda item: expected in selector(item))
        lowered = expected.casefold()
        return self.where(lambda item: lowered in selector(item).casefold())

    def all(self) -> tuple[T, ...]:
        return tuple(item for item in self.items if all(predicate(item) for predicate in self.predicates))

    def first(self) -> T | None:
        for item in self.all():
            return item
        return None

    def count(self) -> int:
        return len(self.all())
