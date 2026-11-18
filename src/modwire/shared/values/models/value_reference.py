from typing import Annotated

from pydantic import Field, GetCoreSchemaHandler, ValidationInfo
from pydantic.json_schema import SkipJsonSchema
from pydantic_core import CoreSchema, PydanticCustomError, core_schema

from .value_reuse import ValueReuse


class ValueReference:
    def __get_pydantic_core_schema__(self, source_type: object, handler: GetCoreSchemaHandler) -> CoreSchema:
        return core_schema.union_schema(
            [
                core_schema.chain_schema(
                    [
                        handler.generate_schema(SkipJsonSchema[Annotated[int, Field(strict=True, ge=0)]]),
                        core_schema.with_info_plain_validator_function(self.resolve),
                        self.resolved_schema(source_type, handler),
                    ]
                ),
                handler(source_type),
            ],
            mode="left_to_right",
        )

    def resolved_schema(self, source_type: object, handler: GetCoreSchemaHandler) -> CoreSchema:
        return core_schema.is_instance_schema(source_type)

    def resolve(self, index: int, info: ValidationInfo[ValueReuse[object] | None]) -> object:
        reuse = info.context
        if reuse is None or not reuse.indexed:
            raise PydanticCustomError("value_reference_context", "Value references require indexed transport.")
        try:
            return reuse.references[index]
        except IndexError as error:
            raise PydanticCustomError(
                "value_reference_index",
                "Reference {index} is outside the validated value table.",
                {"index": index},
            ) from error
