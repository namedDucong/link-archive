"""
링크 저장 API
중요한 점은 링크 저장 시 saved_links에 insert하고, 동시에 crawl_jobs도 insert함
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from datetime import datetime

from app.db import get_db
from app.models import CrawlJob, SavedLink, User
from app.schemas import SavedLinkCreate, SavedLinkResponse, SavedLinkUpdate
from app.utils import hash_url

router = APIRouter(tags=["saved_links"])


@router.post("/api/users/{user_id}/links", response_model=SavedLinkResponse)
def create_saved_link(
    user_id: uuid.UUID,
    link_data: SavedLinkCreate,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    original_url = str(link_data.original_url)
    original_url_hash = hash_url(original_url)

    saved_link = SavedLink(
        user_id=user.id,
        original_url=original_url,
        original_url_hash=original_url_hash,
        memo=link_data.memo,
        status="active",
        crawl_status="queued",
    )

    crawl_job = CrawlJob(
        saved_link=saved_link,
        status="queued",
        attempt_count=0,
    )

    db.add(saved_link)
    db.add(crawl_job)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="This URL is already saved by this user",
        )

    db.refresh(saved_link)

    return saved_link


@router.get("/api/users/{user_id}/links", response_model=list[SavedLinkResponse])
def get_user_saved_links(
    user_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    user_exists = (
        db.query(User.id)
        .filter(User.id == user_id)
        .first()
    )

    if user_exists is None:
        raise HTTPException(status_code=404, detail="User not found")

    links = (
        db.query(SavedLink)
        .options(joinedload(SavedLink.page))
        .filter(SavedLink.user_id == user_id)
        .order_by(SavedLink.created_at.desc())
        .limit(limit)
        .all()
    )

    return links


@router.get("/api/saved-links/{saved_link_id}", response_model=SavedLinkResponse)
def get_saved_link(
    saved_link_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    saved_link = (
        db.query(SavedLink)
        .options(joinedload(SavedLink.page))
        .filter(SavedLink.id == saved_link_id)
        .first()
    )

    if saved_link is None:
        raise HTTPException(status_code=404, detail="Saved link not found")

    return saved_link


@router.delete("/api/saved-links/{saved_link_id}")
def delete_saved_link(
    saved_link_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    saved_link = (
        db.query(SavedLink)
        .filter(SavedLink.id == saved_link_id)
        .first()
    )

    if saved_link is None:
        raise HTTPException(status_code=404, detail="Saved link not found")

    db.delete(saved_link)
    db.commit()

    return {
        "message": "Saved link deleted successfully",
        "id": str(saved_link_id),
    }


@router.patch("/api/saved-links/{saved_link_id}", response_model=SavedLinkResponse)
def update_saved_link(
    saved_link_id: uuid.UUID,
    update_data: SavedLinkUpdate,
    db: Session = Depends(get_db),
):
    saved_link = (
        db.query(SavedLink)
        .options(joinedload(SavedLink.page))
        .filter(SavedLink.id == saved_link_id)
        .first()
    )

    if saved_link is None:
        raise HTTPException(status_code=404, detail="Saved link not found")

    data = update_data.model_dump(exclude_unset=True)

    if "memo" in data:
        saved_link.memo = data["memo"]

    if "status" in data:
        new_status = data["status"]
        saved_link.status = new_status

        if new_status == "archived":
            saved_link.archived_at = datetime.utcnow()

        if new_status == "active":
            saved_link.archived_at = None

    db.commit()
    db.refresh(saved_link)

    return saved_link


@router.post("/api/saved-links/{saved_link_id}/recrawl")
def create_recrawl_job(
    saved_link_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    saved_link = (
        db.query(SavedLink)
        .filter(SavedLink.id == saved_link_id)
        .first()
    )

    if saved_link is None:
        raise HTTPException(status_code=404, detail="Saved link not found")

    existing_job = (
        db.query(CrawlJob)
        .filter(CrawlJob.saved_link_id == saved_link_id)
        .filter(CrawlJob.status.in_(["queued", "running"]))
        .first()
    )

    if existing_job is not None:
        raise HTTPException(
            status_code=409,
            detail="A crawl job is already queued or running for this saved link",
        )

    crawl_job = CrawlJob(
        saved_link_id=saved_link.id,
        status="queued",
        attempt_count=0,
    )

    saved_link.crawl_status = "queued"

    db.add(crawl_job)
    db.commit()
    db.refresh(crawl_job)
    db.refresh(saved_link)

    return {
        "message": "Recrawl job created successfully",
        "saved_link": {
            "id": str(saved_link.id),
            "crawl_status": saved_link.crawl_status,
        },
        "crawl_job": {
            "id": str(crawl_job.id),
            "status": crawl_job.status,
            "attempt_count": crawl_job.attempt_count,
        },
    }