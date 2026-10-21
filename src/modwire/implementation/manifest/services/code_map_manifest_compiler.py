import json
from dataclasses import dataclass

from wireup import injectable

from ....shared.code.models.code_map import CodeMap
from ....shared.code.models.declaration_identity import DeclarationIdentity
from ....shared.code.models.source_call import SourceCall
from ....shared.code.models.source_declaration import SourceDeclaration
from ....shared.code.models.source_dependency_resolution import SourceDependencyResolution
from ....shared.code.models.source_symbol_kind import SourceSymbolKind
from ....shared.code.models.source_visibility import SourceVisibility
from ....shared.values.models.value_model import ValueModel
from ..contracts.manifest_compiler import ManifestCompiler
from ..models.implementation_manifest import ImplementationManifest
from ..models.implementation_manifest_validation_error import ImplementationManifestValidationError
from ..models.implementation_manifest_violation import ImplementationManifestViolation
from ..models.manifest_annotation import ManifestAnnotation
from ..models.manifest_annotation_role import ManifestAnnotationRole
from ..models.manifest_attribute import ManifestAttribute
from ..models.manifest_callable import ManifestCallable
from ..models.manifest_declaration_relation import ManifestDeclarationRelation
from ..models.manifest_dependency import ManifestDependency
from ..models.manifest_dependency_target_kind import ManifestDependencyTargetKind
from ..models.manifest_namespace import ManifestNamespace
from ..models.manifest_parameter import ManifestParameter
from ..models.manifest_span import ManifestSpan
from ..models.manifest_symbol import ManifestSymbol


@injectable(as_type=ManifestCompiler)
@dataclass(frozen=True)
class CodeMapManifestCompiler(ManifestCompiler):
    def canonical_key(self, value: ValueModel) -> str:
        return json.dumps(value.model_dump(mode="json"), ensure_ascii=False, separators=(",", ":"), sort_keys=True)

    def symbol(
        self,
        declaration_id: DeclarationIdentity,
        namespace: str,
        kind: SourceSymbolKind,
        visibility: SourceVisibility,
    ) -> ManifestSymbol:
        return ManifestSymbol(
            id=declaration_id,
            qualified_name=f"{namespace}.{declaration_id.qualified_name}",
            kind=kind,
            visibility=visibility,
        )

    def attribute_id(self, owner_symbol_id: DeclarationIdentity, name: str) -> str:
        return f"{owner_symbol_id.canonical()}::attribute:{name}"

    def compile(self, code_map: CodeMap) -> ImplementationManifest:
        namespaces: set[ManifestNamespace] = set()
        symbols: list[ManifestSymbol] = []
        symbol_ids: set[str] = set()
        callables: list[ManifestCallable] = []
        parameters: list[ManifestParameter] = []
        attributes: list[ManifestAttribute] = []
        annotations: list[ManifestAnnotation] = []
        source_calls: list[SourceCall] = []
        declaration_relations: list[ManifestDeclarationRelation] = []
        dependencies: list[ManifestDependency] = []
        dependency_set: set[ManifestDependency] = set()
        spans: list[ManifestSpan] = []

        for _, source_file in sorted(code_map.extraction.files.items(), key=lambda item: str(item[0])):
            import_identity = str(source_file.import_identity)
            namespaces.update(
                ManifestNamespace(kind=item.kind, qualified_name=item.qualified_name) for item in source_file.namespaces
            )
            namespace = (
                max(
                    source_file.namespaces, key=lambda item: (len(item.qualified_name), item.qualified_name)
                ).qualified_name
                if source_file.namespaces
                else import_identity
            )
            for declaration in source_file.declarations:
                symbols.append(
                    self.symbol(
                        declaration.declaration_id,
                        namespace,
                        declaration.kind,
                        declaration.visibility,
                    )
                )
                symbol_ids.add(declaration.declaration_id.canonical())
                attributes.extend(self.attributes(declaration))
                annotations.extend(self.declaration_annotations(declaration))
            for function in source_file.functions:
                symbols.append(
                    self.symbol(
                        function.declaration_id,
                        namespace,
                        SourceSymbolKind.FUNCTION,
                        function.visibility,
                    )
                )
                symbol_ids.add(function.declaration_id.canonical())
            for value in source_file.values:
                symbols.append(self.symbol(value.declaration_id, namespace, value.value_kind, value.visibility))
                symbol_ids.add(value.declaration_id.canonical())
            for callable_value in source_file.callables:
                callable_id = callable_value.declaration_id
                canonical_id = callable_id.canonical()
                if canonical_id not in symbol_ids:
                    symbols.append(
                        self.symbol(
                            callable_id,
                            namespace,
                            SourceSymbolKind.CALLABLE,
                            callable_value.visibility,
                        )
                    )
                    symbol_ids.add(canonical_id)
                callables.append(ManifestCallable(symbol_id=callable_id, callable_kind=callable_value.kind))
                spans.append(
                    ManifestSpan(
                        target_id=canonical_id,
                        line_start=callable_value.line_start,
                        line_end=callable_value.line_end,
                    )
                )
                annotations.extend(
                    ManifestAnnotation(
                        target_id=canonical_id,
                        role=ManifestAnnotationRole.DECORATOR,
                        expression=decorator,
                    )
                    for decorator in callable_value.decorators
                )
                if callable_value.return_annotation:
                    annotations.append(
                        ManifestAnnotation(
                            target_id=canonical_id,
                            role=ManifestAnnotationRole.RETURN_TYPE,
                            expression=callable_value.return_annotation,
                        )
                    )
                for position, parameter in enumerate(callable_value.parameters):
                    parameter_id = f"{canonical_id}::parameter:{position}:{parameter.name}"
                    parameters.append(
                        ManifestParameter(
                            id=parameter_id,
                            callable_id=callable_id,
                            position=position,
                            name=parameter.name,
                            kind=parameter.kind,
                            has_default=parameter.has_default,
                        )
                    )
                    if parameter.annotation:
                        annotations.append(
                            ManifestAnnotation(
                                target_id=parameter_id,
                                role=ManifestAnnotationRole.PARAMETER_TYPE,
                                expression=parameter.annotation,
                            )
                        )
            source_calls.extend(source_file.calls)
            declaration_relations.extend(
                ManifestDeclarationRelation(
                    source_symbol_id=relation.source_declaration_id,
                    kind=relation.kind,
                    target_reference=relation.target_reference,
                )
                for relation in source_file.declaration_relations
            )

        for edge in code_map.dependency_graph.edges:
            if edge.resolution is SourceDependencyResolution.RESOLVED:
                if edge.to_id is None:
                    raise ImplementationManifestValidationError(
                        ImplementationManifestViolation.MISSING_DEPENDENCY_TARGET_SOURCE, str(edge.from_id)
                    )
                target_kind = ManifestDependencyTargetKind.SOURCE
                target = str(edge.to_id)
            elif edge.resolution is SourceDependencyResolution.EXTERNAL:
                target_kind = ManifestDependencyTargetKind.EXTERNAL
                target = str(edge.specifier)
            else:
                target_kind = ManifestDependencyTargetKind.UNRESOLVED
                target = str(edge.specifier)
            dependency = ManifestDependency(
                source_id=str(edge.from_id),
                target_kind=target_kind,
                target=target,
                specifier=str(edge.specifier),
                resolution=edge.resolution,
                kind=edge.kind,
            )
            if dependency not in dependency_set:
                dependencies.append(dependency)
                dependency_set.add(dependency)

        return ImplementationManifest(
            producer=code_map.producer,
            source_manifest=code_map.extraction.manifest,
            namespaces=tuple(sorted(namespaces, key=self.canonical_key)),
            symbols=tuple(sorted(symbols, key=self.canonical_key)),
            callables=tuple(sorted(callables, key=self.canonical_key)),
            parameters=tuple(sorted(parameters, key=self.canonical_key)),
            attributes=tuple(sorted(attributes, key=self.canonical_key)),
            annotations=tuple(sorted(annotations, key=self.canonical_key)),
            calls=tuple(sorted(source_calls, key=self.canonical_key)),
            declaration_relations=tuple(sorted(declaration_relations, key=self.canonical_key)),
            dependencies=tuple(sorted(dependencies, key=self.canonical_key)),
            spans=tuple(sorted(spans, key=self.canonical_key)),
        )

    def attributes(self, declaration: SourceDeclaration) -> tuple[ManifestAttribute, ...]:
        return tuple(
            ManifestAttribute(
                id=self.attribute_id(declaration.declaration_id, attribute.name),
                owner_symbol_id=declaration.declaration_id,
                name=attribute.name,
                is_optional=attribute.is_optional,
                annotation=attribute.annotation,
                visibility=attribute.visibility,
                member_kind=attribute.member_kind,
                assigned_values=attribute.assigned_values,
            )
            for attribute in declaration.properties
        )

    def declaration_annotations(self, declaration: SourceDeclaration) -> tuple[ManifestAnnotation, ...]:
        annotations = [
            ManifestAnnotation(
                target_id=declaration.declaration_id.canonical(),
                role=ManifestAnnotationRole.DECLARATION,
                expression=annotation,
            )
            for annotation in declaration.declaration_annotations
        ]
        annotations.extend(
            ManifestAnnotation(
                target_id=self.attribute_id(declaration.declaration_id, attribute.name),
                role=ManifestAnnotationRole.ATTRIBUTE_TYPE,
                expression=attribute.annotation,
            )
            for attribute in declaration.properties
            if attribute.annotation
        )
        return tuple(annotations)
