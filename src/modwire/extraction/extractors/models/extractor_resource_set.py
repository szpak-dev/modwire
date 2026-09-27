from typing import Self

from pydantic import model_validator

from ....shared.values.models.value_model import ValueModel
from .extractor_resource import ExtractorResource


class ExtractorResourceSet(ValueModel):
    entrypoint: ExtractorResource
    identity_resources: tuple[ExtractorResource, ...]

    @model_validator(mode="after")
    def validate_resources(self) -> Self:
        ordered = tuple(sorted(self.identity_resources, key=lambda item: (item.package, item.path)))
        if self.identity_resources != ordered:
            raise ValueError("Extractor identity resources must be canonically ordered.")
        identities = {(item.package, item.path) for item in ordered}
        if len(identities) != len(ordered):
            raise ValueError("Extractor identity resources must be unique.")
        if self.entrypoint not in ordered:
            raise ValueError("Extractor identity resources must include the executable entrypoint.")
        return self
