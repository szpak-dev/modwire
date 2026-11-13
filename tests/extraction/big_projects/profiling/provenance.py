from .document import ProfileDocument


class ProfileProvenance(ProfileDocument):
    revision: str
    source_digest: str
    harness_digest: str
    config_digest: str
    python_version: str
    limit_seconds: float
