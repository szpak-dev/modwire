from dataclasses import dataclass, field


@dataclass
class ValueReuse[T]:
    values: dict[T, T] = field(default_factory=dict[T, T])
    field_sets: dict[frozenset[str], set[str]] = field(default_factory=dict[frozenset[str], set[str]])
    indexed: bool = False
    references: list[T | str] = field(default_factory=list[T | str])
    last_fields: set[str] | None = None

    def retain(self, value: T) -> T:
        return value if self.indexed else self.values.setdefault(value, value)

    def field_names(self, supplied: set[str]) -> set[str]:
        previous = self.last_fields
        if previous is not None and previous == supplied:
            return previous
        self.last_fields = self.field_sets.setdefault(frozenset(supplied), supplied)
        return self.last_fields

    def clear(self) -> None:
        self.values.clear()
        self.field_sets.clear()
        self.references.clear()
        self.last_fields = None
