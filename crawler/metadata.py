from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; LinkArchiveBot/0.1; "
        "+https://example.com/bot)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}


@dataclass
class PageMetadata:
    original_url: str
    final_url: str
    domain: str
    title: Optional[str]
    description: Optional[str]
    thumbnail_url: Optional[str]
    favicon_url: Optional[str]
    canonical_url: Optional[str]
    site_name: Optional[str]
    content_type: Optional[str]
    status_code: int


def _clean_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None

    cleaned = " ".join(value.strip().split())
    return cleaned if cleaned else None


def _get_meta_content(soup: BeautifulSoup, *, property_name: str | None = None, name: str | None = None) -> Optional[str]:
    """
    예:
    <meta property="og:title" content="...">
    <meta name="description" content="...">
    """
    if property_name:
        tag = soup.find("meta", attrs={"property": property_name})
        if tag and tag.get("content"):
            return _clean_text(tag.get("content"))

    if name:
        tag = soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            return _clean_text(tag.get("content"))

    return None


def _get_title(soup: BeautifulSoup) -> Optional[str]:
    # 1순위: Open Graph title
    title = _get_meta_content(soup, property_name="og:title")
    if title:
        return title

    # 2순위: Twitter title
    title = _get_meta_content(soup, name="twitter:title")
    if title:
        return title

    # 3순위: HTML title
    if soup.title and soup.title.string:
        return _clean_text(soup.title.string)

    return None


def _get_description(soup: BeautifulSoup) -> Optional[str]:
    # 1순위: Open Graph description
    description = _get_meta_content(soup, property_name="og:description")
    if description:
        return description

    # 2순위: 일반 description
    description = _get_meta_content(soup, name="description")
    if description:
        return description

    # 3순위: Twitter description
    description = _get_meta_content(soup, name="twitter:description")
    if description:
        return description

    return None


def _get_thumbnail_url(soup: BeautifulSoup, base_url: str) -> Optional[str]:
    # 1순위: og:image
    image_url = _get_meta_content(soup, property_name="og:image")
    if image_url:
        return urljoin(base_url, image_url)

    # 2순위: twitter:image
    image_url = _get_meta_content(soup, name="twitter:image")
    if image_url:
        return urljoin(base_url, image_url)

    # 3순위: twitter:image:src
    image_url = _get_meta_content(soup, name="twitter:image:src")
    if image_url:
        return urljoin(base_url, image_url)

    return None


def _get_canonical_url(soup: BeautifulSoup, base_url: str) -> Optional[str]:
    tag = soup.find("link", rel="canonical")
    if tag and tag.get("href"):
        return urljoin(base_url, tag.get("href"))

    return None


def _get_favicon_url(soup: BeautifulSoup, base_url: str) -> Optional[str]:
    """
    favicon은 사이트마다 rel 값이 조금씩 다름.
    대표적으로:
    - icon
    - shortcut icon
    - apple-touch-icon
    """
    candidates = [
        soup.find("link", rel="icon"),
        soup.find("link", rel="shortcut icon"),
        soup.find("link", rel="apple-touch-icon"),
    ]

    for tag in candidates:
        if tag and tag.get("href"):
            return urljoin(base_url, tag.get("href"))

    # fallback: 도메인 루트의 /favicon.ico
    parsed = urlparse(base_url)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}/favicon.ico"

    return None


def _get_site_name(soup: BeautifulSoup) -> Optional[str]:
    site_name = _get_meta_content(soup, property_name="og:site_name")
    if site_name:
        return site_name

    application_name = _get_meta_content(soup, name="application-name")
    if application_name:
        return application_name

    return None


def fetch_page_metadata(url: str, timeout: int = 10) -> PageMetadata:
    response = requests.get(
        url,
        headers=DEFAULT_HEADERS,
        timeout=timeout,
        allow_redirects=True,
    )

    content_type = response.headers.get("Content-Type")
    final_url = response.url
    domain = urlparse(final_url).netloc

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

    return PageMetadata(
        original_url=url,
        final_url=final_url,
        domain=domain,
        title=_get_title(soup),
        description=_get_description(soup),
        thumbnail_url=_get_thumbnail_url(soup, final_url),
        favicon_url=_get_favicon_url(soup, final_url),
        canonical_url=_get_canonical_url(soup, final_url),
        site_name=_get_site_name(soup),
        content_type=content_type,
        status_code=response.status_code,
    )


def fetch_page_metadata_as_dict(url: str) -> dict:
    metadata = fetch_page_metadata(url)
    return asdict(metadata)