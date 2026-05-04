"""
URL을 정규화
→ utm_source 같은 추적 파라미터 제거
→ sha256 hash 생성
"""

import hashlib
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


TRACKING_QUERY_PREFIXES = (
    "utm_",
)

TRACKING_QUERY_KEYS = {
    "fbclid",
    "gclid",
    "igshid",
    "mc_cid",
    "mc_eid",
}


def normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())

    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    path = parsed.path or "/"

    query_items = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        lower_key = key.lower()

        if lower_key in TRACKING_QUERY_KEYS:
            continue

        if lower_key.startswith(TRACKING_QUERY_PREFIXES):
            continue

        query_items.append((key, value))

    query_items.sort()
    query = urlencode(query_items, doseq=True)

    normalized = urlunparse(
        (
            scheme,
            netloc,
            path,
            "",
            query,
            "",
        )
    )

    return normalized


def hash_url(url: str) -> str:
    normalized = normalize_url(url)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()