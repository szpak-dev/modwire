from pathlib import Path

from .extractor_entrypoint import ExtractorEntrypoint


class ModuleExtractorEntrypoint(ExtractorEntrypoint):
    module: str

    def command_arguments(self, resource_path: Path) -> tuple[str, ...]:
        return ("-m", self.module)
