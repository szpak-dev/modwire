from modwire.application import CodeMap, FactCapability, RelationshipFamily, SourceAssignedValueKind


class FixtureCapabilityEvidence:
    def capabilities(self, code_map: CodeMap) -> tuple[FactCapability, ...]:
        files = tuple(code_map.extraction.files.values())
        declarations = tuple(declaration for source in files for declaration in source.declarations)
        functions = tuple(function for source in files for function in source.functions)
        values = tuple(value for source in files for value in source.values)
        callables = tuple(callable_fact for source in files for callable_fact in source.callables)
        calls = tuple(call for source in files for call in source.calls)
        properties = tuple(property_fact for declaration in declarations for property_fact in declaration.properties)
        relations = tuple(relation for source in files for relation in source.declaration_relations)
        imports = tuple(imported for source in files for imported in source.imports)
        namespaces = tuple(namespace for source in files for namespace in source.namespaces)
        annotations = (
            *(annotation for declaration in declarations for annotation in declaration.declaration_annotations),
            *(annotation for function in functions for annotation in function.declaration_annotations),
            *(annotation for callable_fact in callables for annotation in callable_fact.decorators),
            *(callable_fact.return_annotation for callable_fact in callables if callable_fact.return_annotation),
            *(
                parameter.annotation
                for callable_fact in callables
                for parameter in callable_fact.parameters
                if parameter.annotation
            ),
            *(property_fact.annotation for property_fact in properties if property_fact.annotation),
        )
        assigned_values = tuple(
            value
            for property_fact in properties
            for value in property_fact.assigned_values
            if value.kind is not SourceAssignedValueKind.UNSUPPORTED
        )
        observed = {
            FactCapability.SOURCES: bool(files),
            FactCapability.SYMBOLS: bool(declarations or functions or values),
            FactCapability.CALLABLES: bool(callables),
            FactCapability.CALLS: bool(calls),
            FactCapability.PARAMETERS: any(callable_fact.parameters for callable_fact in callables),
            FactCapability.ANNOTATIONS: bool(annotations),
            FactCapability.MODIFIERS: bool(callables),
            FactCapability.ATTRIBUTES: bool(properties),
            FactCapability.ASSIGNED_VALUES: bool(assigned_values),
            FactCapability.INHERITANCE: bool(relations),
            FactCapability.NAMESPACES: bool(namespaces),
            FactCapability.DECLARATION_KINDS: bool(declarations),
            FactCapability.COMPOSITION: bool(relations),
            FactCapability.DEPENDENCIES: bool(imports),
            FactCapability.SPANS: bool(callables),
        }
        return tuple(capability for capability in FactCapability if observed[capability])

    def relationships(self, code_map: CodeMap) -> tuple[RelationshipFamily, ...]:
        files = tuple(code_map.extraction.files.values())
        declaration_evidence = any(source.declaration_relations for source in files)
        member_evidence = any(
            source.callables or source.calls or any(declaration.properties for declaration in source.declarations)
            for source in files
        )
        dependency_evidence = any(source.imports for source in files)
        observed = {
            RelationshipFamily.DECLARATION: declaration_evidence,
            RelationshipFamily.MEMBER: member_evidence,
            RelationshipFamily.DEPENDENCY: dependency_evidence,
        }
        return tuple(family for family in RelationshipFamily if observed[family])
