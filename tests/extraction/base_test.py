from pathlib import Path

from modwire.extraction import ExtractionFacade
from modwire.shared import FileId, ModuleId, QueryableCodeMap, SourceExtraction, SourceFile
from tests.support.service_test import ServiceTestCase


class ExtractionTestCase(ServiceTestCase):
    def extractor(self) -> ExtractionFacade:
        return self.service(ExtractionFacade, self.example_configuration())

    def source_extraction(self, files: dict[str, str]) -> SourceExtraction:
        extractor = self.extractor()
        root = Path("/example/virtual/project")
        parsed = {
            FileId(name): SourceFile.model_validate(
                {**extractor.parse_python(content, root / name, root, name),
                 "file_id": name, "module_id": name.rsplit(".", 1)[0]}
            )
            for name, content in files.items()
        }
        return SourceExtraction(
            files=parsed,
            modules={ModuleId(name.rsplit(".", 1)[0]): FileId(name) for name in files},
            files_found=len(files), files_excluded=0,
        )

    def extract(self, files: dict[str, str]) -> QueryableCodeMap:
        return self.extractor().generate_queryable_map("python", self.source_extraction(files))
