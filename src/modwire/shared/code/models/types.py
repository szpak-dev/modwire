from typing import Literal

ImportCrossingType = Literal["module", "symbol"]
SourceVisibility = Literal["public", "protected", "private"]
SourceSignatureKind = Literal["call", "construct", "index"]
SourceValueDeclarationKind = Literal["assignment", "constant", "property", "unknown"]
SourceValueKind = Literal["callable", "class", "literal", "object", "unknown"]
SourceParameterKind = Literal["positional", "variadic_positional", "named_only", "variadic_named"]
SourceCallableKind = Literal[
    "function", "instance_method", "type_method", "static_method", "constructor", "callable_value", "anonymous"
]
SourceCallResolution = Literal["resolved", "unresolved", "external", "dynamic"]
SourceImportResolution = Literal["resolved", "unresolved", "external"]
SourceExportKind = Literal["module", "class", "interface", "type", "abstract_class", "function", "value", "unknown"]
