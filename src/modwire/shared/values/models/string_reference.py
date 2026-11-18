from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema

from .value_reference import ValueReference


class StringReference(ValueReference):
    def resolved_schema(self, source_type: object, handler: GetCoreSchemaHandler) -> CoreSchema:
        return handler(source_type)
