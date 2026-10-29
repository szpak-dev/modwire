from pydantic import Field

from .row import LanguageCapabilityRow


class LanguageCapabilityDocument(LanguageCapabilityRow):
    language: str = Field(min_length=1)
