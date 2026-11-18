from dataclasses import dataclass, field


@dataclass
class ValueReuse[T]:
    values: dict[T, T] = field(default_factory=dict[T, T])
    field_sets: dict[frozenset[str], set[str]] = field(default_factory=dict[frozenset[str], set[str]])

    def field_names(self, supplied: set[str]) -> set[str]:
        return self.field_sets.setdefault(frozenset(supplied), supplied)

    def clear(self) -> None:
        self.values.clear()
        self.field_sets.clear()
