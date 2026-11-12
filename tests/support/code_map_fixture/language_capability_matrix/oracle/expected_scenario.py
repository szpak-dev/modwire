from typing import Annotated

from pydantic import Field

from ...fixture_root_model import FixtureRootModel
from .code_map_expectation import CodeMapExpectation
from .source_facts_expectation import SourceFactsExpectation


class ExpectedScenario(
    FixtureRootModel[Annotated[CodeMapExpectation | SourceFactsExpectation, Field(discriminator="kind")]]
):
    pass
