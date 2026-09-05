from dataclasses import dataclass
from importlib.resources import files

from wireup import injectable

from modwire.cli.resources.models.defaults import DEFAULT_INIT_ASSETS
from modwire.cli.resources.models.init_asset import InitAsset


@injectable
@dataclass(frozen=True)
class ResourcesApplication:
    def assets(self) -> tuple[InitAsset, ...]:
        return DEFAULT_INIT_ASSETS

    def content(self, source: str) -> str:
        return files("modwire.cli.resources").joinpath("templates", source).read_text(encoding="utf-8")
