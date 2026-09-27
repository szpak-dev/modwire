import json
from dataclasses import dataclass

from wireup import injectable

from ....shared.code.models.code_map import CodeMap
from ....shared.code.models.declaration_identity import DeclarationIdentity
from ....shared.values.models.value_model import ValueModel
from ..contracts.manifest_compiler import ManifestCompiler
from ..models.implementation_manifest import ImplementationManifest
from ..models.manifest_annotation import ManifestAnnotation
from ..models.manifest_attribute import ManifestAttribute
from ..models.manifest_callable import ManifestCallable
from ..models.manifest_dependency import ManifestDependency
from ..models.manifest_inheritance import ManifestInheritance
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
        module: str,
        kind: str,
        visibility: str,
    ) -> ManifestSymbol:
        return ManifestSymbol(
            id=declaration_id,
            qualified_name=f"{module}.{declaration_id.qualified_name}",
            kind=kind,
            visibility=visibility,
        )

    def attribute_id(self, owner_symbol_id: DeclarationIdentity, name: str) -> str:
        return f"{owner_symbol_id.canonical()}::attribute:{name}"

    def compile(self, code_map: CodeMap) -> ImplementationManifest:
        symbols: list[ManifestSymbol] = []
        symbol_ids: set[str] = set()
        callables: list[ManifestCallable] = []
        parameters: list[ManifestParameter] = []
        attributes: list[ManifestAttribute] = []
        annotations: list[ManifestAnnotation] = []
        inheritance: list[ManifestInheritance] = []
        dependencies: list[ManifestDependency] = []
        spans: list[ManifestSpan] = []

        for _, source_file in sorted(code_map.extraction.files.items(), key=lambda item: str(item[0])):
            module = str(source_file.module_id)
            for symbol in source_file.classes:
                symbols.append(self.symbol(symbol.declaration_id, module, "class", symbol.visibility))
                symbol_ids.add(symbol.declaration_id.canonical())
                attributes.extend(
                    ManifestAttribute(
                        id=self.attribute_id(symbol.declaration_id, attribute.name),
                        owner_symbol_id=symbol.declaration_id,
                        name=attribute.name,
                        is_optional=attribute.is_optional,
                        annotation=attribute.annotation,
                        visibility=attribute.visibility,
                        member_kind=attribute.member_kind,
                    )
                    for attribute in symbol.properties
                )
                annotations.extend(
                    ManifestAnnotation(
                        target_id=symbol.declaration_id.canonical(), role="declaration", expression=annotation
                    )
                    for annotation in symbol.declaration_annotations
                )
                annotations.extend(
                    ManifestAnnotation(
                        target_id=self.attribute_id(symbol.declaration_id, attribute.name),
                        role="attribute_type",
                        expression=attribute.annotation,
                    )
                    for attribute in symbol.properties
                    if attribute.annotation
                )
            for symbol in source_file.abstract_classes:
                symbols.append(self.symbol(symbol.declaration_id, module, "abstract_class", symbol.visibility))
                symbol_ids.add(symbol.declaration_id.canonical())
                attributes.extend(
                    ManifestAttribute(
                        id=self.attribute_id(symbol.declaration_id, attribute.name),
                        owner_symbol_id=symbol.declaration_id,
                        name=attribute.name,
                        is_optional=attribute.is_optional,
                        annotation=attribute.annotation,
                        visibility=attribute.visibility,
                        member_kind=attribute.member_kind,
                    )
                    for attribute in symbol.properties
                )
                annotations.extend(
                    ManifestAnnotation(
                        target_id=symbol.declaration_id.canonical(), role="declaration", expression=annotation
                    )
                    for annotation in symbol.declaration_annotations
                )
                annotations.extend(
                    ManifestAnnotation(
                        target_id=self.attribute_id(symbol.declaration_id, attribute.name),
                        role="attribute_type",
                        expression=attribute.annotation,
                    )
                    for attribute in symbol.properties
                    if attribute.annotation
                )
            for symbol in source_file.interfaces:
                symbols.append(self.symbol(symbol.declaration_id, module, "interface", symbol.visibility))
                symbol_ids.add(symbol.declaration_id.canonical())
                attributes.extend(
                    ManifestAttribute(
                        id=self.attribute_id(symbol.declaration_id, attribute.name),
                        owner_symbol_id=symbol.declaration_id,
                        name=attribute.name,
                        is_optional=attribute.is_optional,
                        annotation=attribute.annotation,
                        visibility=attribute.visibility,
                        member_kind=attribute.member_kind,
                    )
                    for attribute in symbol.properties
                )
                annotations.extend(
                    ManifestAnnotation(
                        target_id=symbol.declaration_id.canonical(), role="declaration", expression=annotation
                    )
                    for annotation in symbol.declaration_annotations
                )
                annotations.extend(
                    ManifestAnnotation(
                        target_id=self.attribute_id(symbol.declaration_id, attribute.name),
                        role="attribute_type",
                        expression=attribute.annotation,
                    )
                    for attribute in symbol.properties
                    if attribute.annotation
                )
            for symbol in source_file.types:
                symbols.append(self.symbol(symbol.declaration_id, module, "type", symbol.visibility))
                symbol_ids.add(symbol.declaration_id.canonical())
                attributes.extend(
                    ManifestAttribute(
                        id=self.attribute_id(symbol.declaration_id, attribute.name),
                        owner_symbol_id=symbol.declaration_id,
                        name=attribute.name,
                        is_optional=attribute.is_optional,
                        annotation=attribute.annotation,
                        visibility=attribute.visibility,
                        member_kind=attribute.member_kind,
                    )
                    for attribute in symbol.properties
                )
                annotations.extend(
                    ManifestAnnotation(
                        target_id=symbol.declaration_id.canonical(), role="declaration", expression=annotation
                    )
                    for annotation in symbol.declaration_annotations
                )
                annotations.extend(
                    ManifestAnnotation(
                        target_id=self.attribute_id(symbol.declaration_id, attribute.name),
                        role="attribute_type",
                        expression=attribute.annotation,
                    )
                    for attribute in symbol.properties
                    if attribute.annotation
                )
            for function in source_file.functions:
                symbols.append(self.symbol(function.declaration_id, module, "function", function.visibility))
                symbol_ids.add(function.declaration_id.canonical())
            for value in source_file.values:
                symbols.append(self.symbol(value.declaration_id, module, f"value:{value.value_kind}", value.visibility))
                symbol_ids.add(value.declaration_id.canonical())
            for callable_value in source_file.callables:
                callable_id = callable_value.declaration_id
                canonical_id = callable_id.canonical()
                if canonical_id not in symbol_ids:
                    symbols.append(self.symbol(callable_id, module, "callable", callable_value.visibility))
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
                    ManifestAnnotation(target_id=canonical_id, role="decorator", expression=decorator)
                    for decorator in callable_value.decorators
                )
                if callable_value.return_annotation:
                    annotations.append(
                        ManifestAnnotation(
                            target_id=canonical_id,
                            role="return_type",
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
                                role="parameter_type",
                                expression=parameter.annotation,
                            )
                        )
            inheritance.extend(
                ManifestInheritance(
                    source_symbol_id=relation.source_declaration_id,
                    kind=relation.kind,
                    target_reference=relation.target_reference,
                )
                for relation in source_file.inheritance
            )

        for edge in code_map.dependency_graph.edges:
            if edge.resolution == "resolved":
                if edge.to_id is None:
                    raise ValueError("Resolved dependency edges must identify their target source.")
                target_kind = "source"
                target = str(edge.to_id)
            elif edge.resolution == "external":
                target_kind = "external"
                target = str(edge.specifier)
            else:
                target_kind = "unresolved"
                target = str(edge.specifier)
            dependency = ManifestDependency(
                source_id=str(edge.from_id),
                target_kind=target_kind,
                target=target,
                specifier=str(edge.specifier),
                resolution=edge.resolution,
                kind=edge.kind,
            )
            if dependency not in dependencies:
                dependencies.append(dependency)

        return ImplementationManifest(
            producer=code_map.producer,
            source_manifest=code_map.extraction.manifest,
            symbols=tuple(sorted(symbols, key=self.canonical_key)),
            callables=tuple(sorted(callables, key=self.canonical_key)),
            parameters=tuple(sorted(parameters, key=self.canonical_key)),
            attributes=tuple(sorted(attributes, key=self.canonical_key)),
            annotations=tuple(sorted(annotations, key=self.canonical_key)),
            inheritance=tuple(sorted(inheritance, key=self.canonical_key)),
            dependencies=tuple(sorted(dependencies, key=self.canonical_key)),
            spans=tuple(sorted(spans, key=self.canonical_key)),
        )
