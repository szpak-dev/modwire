from modwire.application import ImplementationManifest

from .language_capability_matrix.expectations.manifest import ManifestEvidenceExpectation


class FixtureManifestEvidence:
    def observe(self, manifest: ImplementationManifest, source: str) -> ManifestEvidenceExpectation:
        return ManifestEvidenceExpectation(
            source=source,
            namespaces=tuple(sorted(f"{item.kind.value}:{item.qualified_name}" for item in manifest.namespaces)),
            symbols=tuple(sorted(f"{item.kind.value}:{item.qualified_name}" for item in manifest.symbols)),
            callables=tuple(
                sorted(f"{item.callable_kind.value}:{item.symbol_id.qualified_name}" for item in manifest.callables)
            ),
            parameters=tuple(
                sorted(
                    f"{item.kind.value}:{item.callable_id.qualified_name}:{item.name}:{item.position}:"
                    f"{str(item.has_default).lower()}"
                    for item in manifest.parameters
                )
            ),
            attributes=tuple(
                sorted(
                    f"{item.member_kind.value}:{item.owner_symbol_id.qualified_name}:{item.name}:"
                    f"{str(item.is_optional).lower()}:{item.visibility.value}:"
                    f"{','.join(value.kind.value for value in item.assigned_values)}"
                    for item in manifest.attributes
                )
            ),
            annotations=tuple(
                sorted(f"{item.role.value}:{item.target_id}:{item.expression}" for item in manifest.annotations)
            ),
            calls=tuple(
                sorted(
                    f"{item.resolution.value}:{item.source_callable_id.qualified_name}:{item.target_name}:"
                    f"{item.ordinal}:"
                    f"{item.target_callable_id.qualified_name if item.target_callable_id else ''}"
                    for item in manifest.calls
                )
            ),
            declaration_relations=tuple(
                sorted(
                    f"{item.kind.value}:{item.source_symbol_id.qualified_name}:{item.target_reference}"
                    for item in manifest.declaration_relations
                )
            ),
            dependencies=tuple(
                sorted(
                    f"{item.kind.value}:{item.resolution.value}:{item.source_id}:{item.target_kind.value}:"
                    f"{item.target}:{item.specifier}"
                    for item in manifest.dependencies
                )
            ),
        )
