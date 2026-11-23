from pydantic import ValidationInfo

from .value_reuse import ValueReuse


class ValueTable[T]:
    def retain(self, values: list[T], info: ValidationInfo[ValueReuse[T]]) -> list[T]:
        info.context.references.extend(values)
        return values
