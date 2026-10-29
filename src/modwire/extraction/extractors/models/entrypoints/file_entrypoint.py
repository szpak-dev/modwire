from pathlib import Path

from .extractor_entrypoint import ExtractorEntrypoint


class FileExtractorEntrypoint(ExtractorEntrypoint):
    arguments: tuple[str, ...]

    def command_arguments(self, resource_path: Path) -> tuple[str, ...]:
        return (*self.arguments, str(resource_path))
