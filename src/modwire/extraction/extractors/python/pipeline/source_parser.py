import ast
from dataclasses import dataclass

from wireup import injectable

from .....shared.code.models.identity import FileId
from ...domain import SourceParser
from ...models.parsed_source_file import ParsedSourceFile
from ..observations.source_context import PythonSourceContext
from ..semantics.reader import PythonSemanticReader
from ..source_facts.reader import PythonSourceFactReader
from ..traversal.observation_reader import PythonObservationReader


@injectable(as_type=SourceParser, qualifier="python")
@dataclass(frozen=True)
class PythonSyntaxParser(SourceParser):
    observations: PythonObservationReader
    semantics: PythonSemanticReader
    facts: PythonSourceFactReader

    def extract(self, content: str, path: str, sources_root: str, source_id: FileId) -> ParsedSourceFile:
        context = PythonSourceContext(
            source_id=source_id,
            path=path,
            sources_root=sources_root,
            content=content,
        )
        observation = self.observations.read(ast.parse(content, filename=path))
        catalog = self.semantics.read(observation, context)
        return self.facts.read(catalog, context)
