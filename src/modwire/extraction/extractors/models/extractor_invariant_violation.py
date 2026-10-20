from enum import StrEnum


class ExtractorInvariantViolation(StrEnum):
    ANNOTATED_CLASS_PROPERTY_REQUIRES_ANNOTATED_ASSIGNMENT = "annotated_class_property_requires_annotated_assignment"
    UNSUPPORTED_VALUE_STATEMENT = "unsupported_value_statement"
    UNCLASSIFIED_CALL_TARGET = "unclassified_call_target"
    DECORATED_METHOD_PROPERTY_REQUIRES_FUNCTION = "decorated_method_property_requires_function"
    ASSIGNED_CLASS_PROPERTY_REQUIRES_ASSIGNMENT = "assigned_class_property_requires_assignment"
    ANNOTATED_INSTANCE_PROPERTY_REQUIRES_ANNOTATED_ASSIGNMENT = (
        "annotated_instance_property_requires_annotated_assignment"
    )
    INVALID_BUILD_ARGUMENTS = "invalid_build_arguments"
    STALE_GENERATED_RESOURCE = "stale_generated_resource"
    BUILD_COMMAND_FAILED = "build_command_failed"
    BUILD_RESOURCE_ACCESS_FAILED = "build_resource_access_failed"
    ASSIGNED_INSTANCE_PROPERTY_REQUIRES_ASSIGNMENT = "assigned_instance_property_requires_assignment"
    UNCLASSIFIED_CALLABLE = "unclassified_callable"
    UNCLASSIFIED_PROPERTY = "unclassified_property"
    UNCLASSIFIED_CLASS = "unclassified_class"
    UNCLASSIFIED_EXPORT = "unclassified_export"
    MISSING_CALLABLE_END_LINE = "missing_callable_end_line"
    UNSUPPORTED_IMPORT_CANDIDATE = "unsupported_import_candidate"
    MISSING_VALUE_END_LINE = "missing_value_end_line"
    MISSING_CLASS_END_LINE = "missing_class_end_line"
    MISSING_FUNCTION_END_LINE = "missing_function_end_line"
