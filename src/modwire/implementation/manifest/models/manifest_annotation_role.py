from enum import StrEnum


class ManifestAnnotationRole(StrEnum):
    DECLARATION = "declaration"
    DECORATOR = "decorator"
    ATTRIBUTE_TYPE = "attribute_type"
    PARAMETER_TYPE = "parameter_type"
    RETURN_TYPE = "return_type"
