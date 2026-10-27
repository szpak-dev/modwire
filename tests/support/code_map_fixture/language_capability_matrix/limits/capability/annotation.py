from pydantic import Field

from ....model import FixtureModel


class AnnotationLimitationExpectation(FixtureModel):
    scenario: str = Field(min_length=1)
    present_annotations: tuple[str, ...]
    absent_annotations: tuple[str, ...]
    absent_attribute_names: tuple[str, ...]
