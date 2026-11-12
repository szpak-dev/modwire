from pydantic import Field

from ....fixture_model import FixtureModel
from ...values.names.language_id import LanguageId
from .language_applicability import LanguageApplicability


class ExtractionObligation(FixtureModel):
    meaning: str = Field(min_length=1)
    priority: int = Field(ge=1, le=5)
    languages: dict[LanguageId, LanguageApplicability]
