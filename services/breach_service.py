import hashlib
import logging

import httpx

from config import settings

logger = logging.getLogger(__name__)

HIBP_API_URL = "https://api.pwnedpasswords.com/range/{prefix}"


def check_password_breached(password: str) -> int | None:
    if not settings.breach_check_enabled:
        return None
    sha1_hash = hashlib.sha1(password.encode()).hexdigest().upper()
    prefix, suffix = sha1_hash[:5], sha1_hash[5:]
    try:
        with httpx.Client(timeout=5) as client:
            response = client.get(HIBP_API_URL.format(prefix=prefix))
            response.raise_for_status()
            for line in response.text.splitlines():
                hash_suffix, count = line.split(":")
                if hash_suffix.strip() == suffix:
                    return int(count.strip())
    except Exception:
        logger.warning("HIBP breach check failed", exc_info=True)
    return None
