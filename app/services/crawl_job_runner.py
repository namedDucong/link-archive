from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models import CrawlJob, CrawledPage, SavedLink
from app.services.crawler import crawl_page
from app.utils import hash_url


def process_one_crawl_job(db: Session) -> dict:
    """
    queued 상태의 crawl job 하나를 처리한다.

    처리 흐름:
    1. crawl_jobs에서 queued job 하나 조회
    2. saved_links.original_url 크롤링
    3. crawled_pages에 메타데이터 저장 또는 기존 page 재사용
    4. saved_links.page_id 연결
    5. saved_links.crawl_status 업데이트
    6. crawl_jobs.status 업데이트
    """

    job = (
        db.query(CrawlJob)
        .options(joinedload(CrawlJob.saved_link))
        .filter(CrawlJob.status == "queued")
        .order_by(CrawlJob.created_at.asc())
        .first()
    )

    if job is None:
        return {
            "message": "No queued crawl job",
            "processed": False,
        }

    saved_link = job.saved_link

    if saved_link is None:
        job.status = "failed"
        job.last_error = "Saved link not found"
        job.finished_at = datetime.utcnow()
        job.attempt_count = job.attempt_count + 1
        db.commit()

        return {
            "message": "Saved link not found",
            "processed": False,
            "job_id": str(job.id),
        }

    job.status = "running"
    job.started_at = datetime.utcnow()
    job.attempt_count = job.attempt_count + 1
    saved_link.crawl_status = "running"

    db.commit()
    db.refresh(job)
    db.refresh(saved_link)

    try:
        crawled_data = crawl_page(saved_link.original_url)

        canonical_url = crawled_data["canonical_url"]
        canonical_url_hash = hash_url(canonical_url)

        page = (
            db.query(CrawledPage)
            .filter(CrawledPage.canonical_url_hash == canonical_url_hash)
            .first()
        )

        if page is None:
            page = CrawledPage(
                canonical_url=canonical_url,
                canonical_url_hash=canonical_url_hash,
                title=crawled_data.get("title"),
                description=crawled_data.get("description"),
                domain=crawled_data.get("domain"),
                author=crawled_data.get("author"),
                page_language=crawled_data.get("page_language"),
                crawl_status="done",
                crawled_at=datetime.utcnow(),
            )

            db.add(page)

            try:
                db.flush()
            except IntegrityError:
                db.rollback()

                page = (
                    db.query(CrawledPage)
                    .filter(CrawledPage.canonical_url_hash == canonical_url_hash)
                    .first()
                )

                if page is None:
                    raise

        else:
            page.title = crawled_data.get("title") or page.title
            page.description = crawled_data.get("description") or page.description
            page.domain = crawled_data.get("domain") or page.domain
            page.author = crawled_data.get("author") or page.author
            page.page_language = crawled_data.get("page_language") or page.page_language
            page.crawl_status = "done"
            page.crawled_at = datetime.utcnow()

        saved_link.page_id = page.id
        saved_link.crawl_status = "done"

        job.status = "done"
        job.finished_at = datetime.utcnow()
        job.last_error = None

        db.commit()
        db.refresh(saved_link)
        db.refresh(page)
        db.refresh(job)

        return {
            "message": "Crawl job processed successfully",
            "processed": True,
            "job": {
                "id": str(job.id),
                "status": job.status,
                "attempt_count": job.attempt_count,
            },
            "saved_link": {
                "id": str(saved_link.id),
                "original_url": saved_link.original_url,
                "crawl_status": saved_link.crawl_status,
                "page_id": str(saved_link.page_id) if saved_link.page_id else None,
            },
            "page": {
                "id": str(page.id),
                "canonical_url": page.canonical_url,
                "title": page.title,
                "description": page.description,
                "domain": page.domain,
                "crawl_status": page.crawl_status,
            },
        }

    except Exception as error:
        db.rollback()

        job = (
            db.query(CrawlJob)
            .filter(CrawlJob.id == job.id)
            .first()
        )

        saved_link = (
            db.query(SavedLink)
            .filter(SavedLink.id == saved_link.id)
            .first()
        )

        if job is not None:
            job.status = "failed"
            job.last_error = str(error)
            job.finished_at = datetime.utcnow()

        if saved_link is not None:
            saved_link.crawl_status = "failed"

        db.commit()

        return {
            "message": "Crawl job failed",
            "processed": False,
            "error": str(error),
            "job_id": str(job.id) if job else None,
        }