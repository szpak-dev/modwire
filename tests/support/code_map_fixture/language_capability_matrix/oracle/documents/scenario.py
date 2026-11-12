from typing import Annotated

from pydantic import Field

from ....fixture_root_model import FixtureRootModel
from .code_map import ScenarioCodeMapDocument
from .source_facts import ScenarioSourceFactsDocument


class ScenarioDocument(
    FixtureRootModel[Annotated[ScenarioCodeMapDocument | ScenarioSourceFactsDocument, Field(discriminator="kind")]]
):
    pass
