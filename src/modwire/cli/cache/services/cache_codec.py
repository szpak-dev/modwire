import hashlib
import json
from dataclasses import dataclass
from typing import Any, cast

from wireup import injectable

from ..models.cache_key import CacheKey


@injectable
@dataclass(frozen=True)
class CacheCodec:
    def encode(self, key: CacheKey, value: object) -> bytes:
        payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
        envelope = {
            "schema_version": key.schema_version,
            "key": key.model_dump(mode="json"),
            "payload_digest": hashlib.sha256(payload).hexdigest(),
            "payload": value,
        }
        return json.dumps(envelope, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()

    def decode(self, key: CacheKey, payload: bytes) -> object | None:
        try:
            parsed: Any = json.loads(payload)
            if not isinstance(parsed, dict):
                return None
            envelope = cast(dict[str, object], parsed)
            if envelope.get("schema_version") != key.schema_version:
                return None
            if envelope.get("key") != key.model_dump(mode="json"):
                return None
            value = envelope["payload"]
            serialized = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
            if envelope.get("payload_digest") != hashlib.sha256(serialized).hexdigest():
                return None
            return value
        except (KeyError, TypeError, ValueError, UnicodeDecodeError):
            return None
