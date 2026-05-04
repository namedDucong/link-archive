"""
URL 접속
→ HTML 파싱
→ title, description, canonical_url, domain 등 추출
→ dict로 반환
"""


from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup


def _get_meta_content(soup: BeautifulSoup, *, name: Optional[str] = None, property_: Optional[str] = None) -> Optional[str]:
    if name is not None:
        tag = soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            return tag["content"].strip()

    if property_ is not None:
        tag = soup.find("meta", attrs={"property": property_})
        if tag and tag.get("content"):
            return tag["content"].strip()

    return None


def _get_title(soup: BeautifulSoup) -> Optional[str]:
    og_title = _get_meta_content(soup, property_="og:title")
    if og_title:
        return og_title

    twitter_title = _get_meta_content(soup, name="twitter:title")
    if twitter_title:
        return twitter_title

    if soup.title and soup.title.string:
        return soup.title.string.strip()

    return None


def _get_description(soup: BeautifulSoup) -> Optional[str]:
    description = _get_meta_content(soup, name="description")
    if description:
        return description

    og_description = _get_meta_content(soup, property_="og:description")
    if og_description:
        return og_description

    twitter_description = _get_meta_content(soup, name="twitter:description")
    if twitter_description:
        return twitter_description

    return None


def _get_canonical_url(soup: BeautifulSoup, final_url: str) -> str:
    canonical_tag = soup.find("link", rel=lambda value: value and "canonical" in value)

    if canonical_tag and canonical_tag.get("href"):
        return urljoin(final_url, canonical_tag["href"].strip())

    og_url = _get_meta_content(soup, property_="og:url")
    if og_url:
        return urljoin(final_url, og_url)

    return final_url


def _get_author(soup: BeautifulSoup) -> Optional[str]:
    author = _get_meta_content(soup, name="author")
    if author:
        return author

    article_author = _get_meta_content(soup, property_="article:author")
    if article_author:
        return article_author

    return None


def _get_language(soup: BeautifulSoup) -> Optional[str]:
    html_tag = soup.find("html")

    if html_tag and html_tag.get("lang"):
        return html_tag["lang"].strip()

    return None


def crawl_page(url: str) -> dict:
    """
    URL 하나를 크롤링해서 crawled_pages에 저장할 메타데이터를 반환한다.

    반환 예:
    {
        "canonical_url": "...",
        "title": "...",
        "description": "...",
        "domain": "...",
        "author": "...",
        "page_language": "ko",
    }
    """

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    with httpx.Client(
        headers=headers,
        follow_redirects=True,
        timeout=10.0,
    ) as client:
        response = client.get(url)
        response.raise_for_status()

    final_url = str(response.url)
    soup = BeautifulSoup(response.text, "html.parser")

    canonical_url = _get_canonical_url(soup, final_url)
    parsed = urlparse(canonical_url)

    return {
        "canonical_url": canonical_url,
        "title": _get_title(soup),
        "description": _get_description(soup),
        "domain": parsed.netloc.lower() if parsed.netloc else None,
        "author": _get_author(soup),
        "page_language": _get_language(soup),
    }