from dataclasses import dataclass

from modwire.application import (
    DeclarationIdentity,
    Edge,
    FileId,
    Node,
    SourceCallable,
    SourceClassMethod,
    SourceClassProperty,
    SourceDeclaration,
    SourceFile,
)


@dataclass(frozen=True)
class FixtureSourceIdentities:
    sources: dict[FileId, FileId]

    def authored(self, source: FileId) -> FileId:
        return next(authored for authored, canonical in self.sources.items() if canonical == source)

    def node(self, value: Node) -> Node:
        return value.model_copy(update={"id": self.sources[value.id]})

    def edge(self, value: Edge) -> Edge:
        return value.model_copy(
            update={
                "from_id": self.sources[value.from_id],
                "to_id": self.sources[value.to_id] if value.to_id is not None else None,
            }
        )

    def declaration(self, identity: DeclarationIdentity) -> DeclarationIdentity:
        return identity.model_copy(update={"source_id": self.sources[identity.source_id]})

    def callable[Callable: SourceCallable](self, value: Callable) -> Callable:
        return value.model_copy(
            update={
                "source_id": self.sources[value.source_id],
                "declaration_id": self.declaration(value.declaration_id),
            }
        )

    def method(self, value: SourceClassMethod) -> SourceClassMethod:
        return self.callable(value).model_copy(
            update={"owner_declaration_id": self.declaration(value.owner_declaration_id)}
        )

    def property(self, value: SourceClassProperty) -> SourceClassProperty:
        return value.model_copy(
            update={
                "declaration_id": self.declaration(value.declaration_id),
                "owner_declaration_id": self.declaration(value.owner_declaration_id),
            }
        )

    def symbol(self, value: SourceDeclaration) -> SourceDeclaration:
        return value.model_copy(
            update={
                "declaration_id": self.declaration(value.declaration_id),
                "methods": tuple(self.method(method) for method in value.methods),
                "abstract_methods": tuple(self.method(method) for method in value.abstract_methods),
                "properties": tuple(self.property(property_) for property_ in value.properties),
            }
        )

    def source(self, value: SourceFile) -> SourceFile:
        return value.model_copy(
            update={
                "file_id": self.sources[value.file_id],
                "declarations": tuple(self.symbol(declaration) for declaration in value.declarations),
                "functions": tuple(self.callable(function) for function in value.functions),
                "callable_values": tuple(self.callable(callable_) for callable_ in value.callable_values),
                "anonymous_callables": tuple(self.callable(callable_) for callable_ in value.anonymous_callables),
                "values": tuple(
                    item.model_copy(update={"declaration_id": self.declaration(item.declaration_id)})
                    for item in value.values
                ),
                "calls": tuple(
                    call.model_copy(
                        update={
                            "source_id": self.sources[call.source_id],
                            "source_callable_id": self.declaration(call.source_callable_id),
                            "target_callable_id": (
                                self.declaration(call.target_callable_id)
                                if call.target_callable_id is not None
                                else None
                            ),
                        }
                    )
                    for call in value.calls
                ),
                "declaration_relations": tuple(
                    relation.model_copy(
                        update={"source_declaration_id": self.declaration(relation.source_declaration_id)}
                    )
                    for relation in value.declaration_relations
                ),
                "imports": [
                    item.model_copy(
                        update={
                            "target_file_id": (
                                self.sources[item.target_file_id] if item.target_file_id is not None else None
                            )
                        }
                    )
                    for item in value.imports
                ],
            }
        )
