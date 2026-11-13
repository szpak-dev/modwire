import ast
import hashlib
from dataclasses import dataclass

from wireup import injectable

from .....shared.code.models.inventories.file_inventory_coverage import FileInventoryCoverage
from .....shared.code.models.inventories.inventory_coverage import InventoryCoverage
from .....shared.code.models.inventories.inventory_limitation import InventoryLimitation
from .....shared.code.models.inventories.inventory_status import InventoryStatus
from .....shared.code.models.sources.identity import FileId
from ...domain import SourceParser
from ...models.extractor_invariant_error import ExtractorInvariantError
from ...models.extractor_invariant_violation import ExtractorInvariantViolation
from ...models.parsed_source_file import ParsedSourceFile
from ...models.source_parse_error import SourceParseError
from ..observations.source_context import PythonSourceContext
from ..semantics.catalog import PythonSemanticCatalog
from ..semantics.reader import PythonSemanticReader
from ..traversal.observation_reader import PythonObservationReader
from .source_assembler import PythonSourceAssembler


@injectable(as_type=SourceParser, qualifier="python")
@dataclass(frozen=True)
class PythonSyntaxParser(SourceParser):
    observations: PythonObservationReader
    semantics: PythonSemanticReader
    assembler: PythonSourceAssembler

    def extract(self, content: str, path: str, sources_root: str, source_id: FileId) -> ParsedSourceFile:
        context = PythonSourceContext(
            source_id=source_id,
            path=path,
            sources_root=sources_root,
            content=content,
            content_digest=hashlib.sha256(content.encode("utf-8")).hexdigest(),
        )
        try:
            tree = ast.parse(content, filename=path)
        except SyntaxError as error:
            if error.lineno is None or error.offset is None:
                raise ExtractorInvariantError(
                    ExtractorInvariantViolation.MISSING_SOURCE_PARSE_LOCATION,
                    path,
                ) from error
            raise SourceParseError(
                language="python",
                path=path,
                line=error.lineno,
                column=error.offset,
                diagnostic=error.msg,
            ) from error
        observation = self.observations.read(tree)
        catalog = self.semantics.read(observation, context)
        return self.assembler.assemble(catalog, self.inventory(catalog))

    def inventory(self, catalog: PythonSemanticCatalog) -> FileInventoryCoverage:
        evidence = catalog.inventory
        return FileInventoryCoverage(
            declarations=self.coverage(tuple(evidence.declarations)),
            functions=self.coverage(tuple(evidence.functions)),
            values=self.coverage(tuple(evidence.values)),
            callable_values=self.coverage(tuple(evidence.callable_values)),
            anonymous_callables=self.coverage(tuple(evidence.anonymous_callables)),
            exports=self.coverage((*evidence.exports, *evidence.implicit_exports)),
            namespaces=InventoryCoverage(status=InventoryStatus.NOT_APPLICABLE, limitations=()),
            unresolved_methods=InventoryCoverage(status=InventoryStatus.NOT_APPLICABLE, limitations=()),
        )

    def coverage(self, limitations: tuple[InventoryLimitation, ...]) -> InventoryCoverage:
        return InventoryCoverage(
            status=InventoryStatus.INCOMPLETE if limitations else InventoryStatus.COMPLETE, limitations=limitations
        )
