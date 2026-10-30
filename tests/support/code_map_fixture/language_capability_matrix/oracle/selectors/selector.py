from typing import Annotated

from pydantic import Field

from ....fixture_root_model import FixtureRootModel
from .dependencies import DependencySelector
from .parameters import ParameterListSelector
from .source import SourceFileSelector


class ScenarioFactSelector(
    FixtureRootModel[
        Annotated[SourceFileSelector | ParameterListSelector | DependencySelector, Field(discriminator="kind")]
    ]
):
    pass
