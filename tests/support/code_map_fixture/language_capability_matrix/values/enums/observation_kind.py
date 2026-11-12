from enum import StrEnum


class ObservationKind(StrEnum):
    ANNOTATION = "annotation"
    ASSIGNED_VALUES = "assigned_values"
    ATTRIBUTE = "attribute"
    CALL = "call"
    CALLABLE = "callable"
    DECLARATION = "declaration"
    DECLARATION_RELATION = "declaration_relation"
    DEPENDENCY = "dependency"
    EMPTY_SOURCE = "empty_source"
    EXACT_SPAN = "exact_span"
    MODIFIER = "modifier"
    NAMESPACE = "namespace"
    PARAMETER = "parameter"
    PARAMETER_LIST = "parameter_list"
    SOURCE = "source"
    SPAN_OWNER = "span_owner"
    SYMBOL = "symbol"
    TYPE_REFERENCE = "type_reference"
    TYPE_SLOT = "type_slot"
