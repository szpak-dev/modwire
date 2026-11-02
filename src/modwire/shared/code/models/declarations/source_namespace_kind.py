from enum import StrEnum


class SourceNamespaceKind(StrEnum):
    PACKAGE = "package"
    NAMESPACE = "namespace"
    MODULE = "module"
