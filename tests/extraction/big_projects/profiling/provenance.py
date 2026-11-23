from .document import ProfileDocument


class ProfileProvenance(ProfileDocument):
    revision: str
    source_digest: str
    harness_digest: str
    config_digest: str
    python_version: str
    limit_seconds: float
    rss_limit_bytes: int
    process_limit: int
    max_workers: int
    resource_sampling_seconds: float
    sampler_timeout_seconds: float
    resource_measurement: str = (
        "Sampled process-group RSS sum; shared pages count per process and allocations between samples "
        "may exceed the limit."
    )
