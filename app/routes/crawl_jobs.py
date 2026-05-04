# from datetime import datetime

# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.exc import IntegrityError
# from sqlalchemy.orm import Session, joinedload

# from app.db import get_db
# from app.models import CrawlJob, CrawledPage, SavedLink
# from app.services.crawler import crawl_page
# from app.utils import hash_url

# router = APIRouter(prefix="/api/crawl-jobs", tags=["crawl_jobs"])


# @router.post("/run-once")
# def run_one_crawl_job(db: Session = Depends(get_db)):
#     """
#     queued 상태의 crawl job 하나를 가져와서 처리한다.

#     개발/테스트용 API.
#     나중에는 이 로직을 백그라운드 worker로 옮기면 된다.
#     """

#     job = (
#         db.query(CrawlJob)
#         .options(joinedload(CrawlJob.saved_link))
#         .filter(CrawlJob.status == "queued")
#         .order_by(CrawlJob.created_at.asc())
#         .first()
#     )

#     if job is None:
#         return {
#             "message": "No queued crawl job",
#             "processed": False,
#         }

#     saved_link = job.saved_link

#     if saved_link is None:
#         job.status = "failed"
#         job.last_error = "Saved link not found"
#         job.finished_at = datetime.utcnow()
#         job.attempt_count = job.attempt_count + 1
#         db.commit()

#         raise HTTPException(
#             status_code=404,
#             detail="Saved link not found for this crawl job",
#         )

#     job.status = "running"
#     job.started_at = datetime.utcnow()
#     job.attempt_count = job.attempt_count + 1

#     saved_link.crawl_status = "running"

#     db.commit()
#     db.refresh(job)
#     db.refresh(saved_link)

#     try:
#         crawled_data = crawl_page(saved_link.original_url)

#         canonical_url = crawled_data["canonical_url"]
#         canonical_url_hash = hash_url(canonical_url)

#         page = (
#             db.query(CrawledPage)
#             .filter(CrawledPage.canonical_url_hash == canonical_url_hash)
#             .first()
#         )

#         if page is None:
#             page = CrawledPage(
#                 canonical_url=canonical_url,
#                 canonical_url_hash=canonical_url_hash,
#                 title=crawled_data.get("title"),
#                 description=crawled_data.get("description"),
#                 domain=crawled_data.get("domain"),
#                 author=crawled_data.get("author"),
#                 page_language=crawled_data.get("page_language"),
#                 crawl_status="done",
#                 crawled_at=datetime.utcnow(),
#             )

#             db.add(page)

#             try:
#                 db.flush()
#             except IntegrityError:
#                 db.rollback()

#                 page = (
#                     db.query(CrawledPage)
#                     .filter(CrawledPage.canonical_url_hash == canonical_url_hash)
#                     .first()
#                 )

#                 if page is None:
#                     raise

#         else:
#             page.title = crawled_data.get("title") or page.title
#             page.description = crawled_data.get("description") or page.description
#             page.domain = crawled_data.get("domain") or page.domain
#             page.author = crawled_data.get("author") or page.author
#             page.page_language = crawled_data.get("page_language") or page.page_language
#             page.crawl_status = "done"
#             page.crawled_at = datetime.utcnow()

#         saved_link.page_id = page.id
#         saved_link.crawl_status = "done"

#         job.status = "done"
#         job.finished_at = datetime.utcnow()
#         job.last_error = None

#         db.commit()
#         db.refresh(saved_link)
#         db.refresh(page)
#         db.refresh(job)

#         return {
#             "message": "Crawl job processed successfully",
#             "processed": True,
#             "job": {
#                 "id": str(job.id),
#                 "status": job.status,
#                 "attempt_count": job.attempt_count,
#             },
#             "saved_link": {
#                 "id": str(saved_link.id),
#                 "original_url": saved_link.original_url,
#                 "crawl_status": saved_link.crawl_status,
#                 "page_id": str(saved_link.page_id) if saved_link.page_id else None,
#             },
#             "page": {
#                 "id": str(page.id),
#                 "canonical_url": page.canonical_url,
#                 "title": page.title,
#                 "description": page.description,
#                 "domain": page.domain,
#                 "crawl_status": page.crawl_status,
#             },
#         }

#     except Exception as error:
#         db.rollback()

#         job = (
#             db.query(CrawlJob)
#             .filter(CrawlJob.id == job.id)
#             .first()
#         )

#         saved_link = (
#             db.query(SavedLink)
#             .filter(SavedLink.id == saved_link.id)
#             .first()
#         )

#         if job is not None:
#             job.status = "failed"
#             job.last_error = str(error)
#             job.finished_at = datetime.utcnow()

#         if saved_link is not None:
#             saved_link.crawl_status = "failed"

#         db.commit()

#         raise HTTPException(
#             status_code=500,
#             detail=f"Crawl job failed: {error}",
#         )

# from fastapi import APIRouter, Depends
# from sqlalchemy.orm import Session

# from app.db import get_db
# from app.services.crawl_job_runner import process_one_crawl_job

# router = APIRouter(prefix="/api/crawl-jobs", tags=["crawl_jobs"])


# @router.post("/run-once")
# def run_one_crawl_job(db: Session = Depends(get_db)):
#     return process_one_crawl_job(db)



from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import CrawlJob
from app.schemas import CrawlJobResponse
from app.services.crawl_job_runner import process_one_crawl_job

router = APIRouter(prefix="/api/crawl-jobs", tags=["crawl_jobs"])


@router.post("/run-once")
def run_one_crawl_job(db: Session = Depends(get_db)):
    return process_one_crawl_job(db)


@router.get("", response_model=list[CrawlJobResponse])
def get_crawl_jobs(
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(CrawlJob)

    if status is not None:
        query = query.filter(CrawlJob.status == status)

    jobs = (
        query
        .order_by(CrawlJob.created_at.desc())
        .limit(limit)
        .all()
    )

    return jobs