# import uuid

# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.exc import IntegrityError
# from sqlalchemy.orm import Session

# from app.db import get_db
# from app.models import SavedLink, SavedLinkTag, Tag, User
# from app.schemas import TagAttachRequest, TagCreate, TagResponse


# router = APIRouter(tags=["tags"])


# @router.post("/api/users/{user_id}/tags", response_model=TagResponse)
# def create_tag(
#     user_id: uuid.UUID,
#     tag_data: TagCreate,
#     db: Session = Depends(get_db),
# ):
#     user = (
#         db.query(User)
#         .filter(User.id == user_id)
#         .first()
#     )

#     if user is None:
#         raise HTTPException(status_code=404, detail="User not found")

#     tag_name = tag_data.name.strip()

#     if not tag_name:
#         raise HTTPException(status_code=400, detail="Tag name cannot be empty")

#     existing_tag = (
#         db.query(Tag)
#         .filter(Tag.user_id == user_id)
#         .filter(Tag.name == tag_name)
#         .first()
#     )

#     if existing_tag is not None:
#         return existing_tag

#     tag = Tag(
#         user_id=user.id,
#         name=tag_name,
#     )

#     db.add(tag)

#     try:
#         db.commit()
#     except IntegrityError:
#         db.rollback()

#         tag = (
#             db.query(Tag)
#             .filter(Tag.user_id == user_id)
#             .filter(Tag.name == tag_name)
#             .first()
#         )

#         if tag is None:
#             raise

#         return tag

#     db.refresh(tag)

#     return tag


# @router.get("/api/users/{user_id}/tags", response_model=list[TagResponse])
# def get_user_tags(
#     user_id: uuid.UUID,
#     db: Session = Depends(get_db),
# ):
#     user_exists = (
#         db.query(User.id)
#         .filter(User.id == user_id)
#         .first()
#     )

#     if user_exists is None:
#         raise HTTPException(status_code=404, detail="User not found")

#     tags = (
#         db.query(Tag)
#         .filter(Tag.user_id == user_id)
#         .order_by(Tag.created_at.desc())
#         .all()
#     )

#     return tags


# @router.post("/api/saved-links/{saved_link_id}/tags", response_model=TagResponse)
# def attach_tag_to_saved_link(
#     saved_link_id: uuid.UUID,
#     tag_data: TagAttachRequest,
#     db: Session = Depends(get_db),
# ):
#     saved_link = (
#         db.query(SavedLink)
#         .filter(SavedLink.id == saved_link_id)
#         .first()
#     )

#     if saved_link is None:
#         raise HTTPException(status_code=404, detail="Saved link not found")

#     tag_name = tag_data.name.strip()

#     if not tag_name:
#         raise HTTPException(status_code=400, detail="Tag name cannot be empty")

#     tag = (
#         db.query(Tag)
#         .filter(Tag.user_id == saved_link.user_id)
#         .filter(Tag.name == tag_name)
#         .first()
#     )

#     if tag is None:
#         tag = Tag(
#             user_id=saved_link.user_id,
#             name=tag_name,
#         )

#         db.add(tag)

#         try:
#             db.flush()
#         except IntegrityError:
#             db.rollback()

#             tag = (
#                 db.query(Tag)
#                 .filter(Tag.user_id == saved_link.user_id)
#                 .filter(Tag.name == tag_name)
#                 .first()
#             )

#             if tag is None:
#                 raise

#     existing_link_tag = (
#         db.query(SavedLinkTag)
#         .filter(SavedLinkTag.saved_link_id == saved_link.id)
#         .filter(SavedLinkTag.tag_id == tag.id)
#         .first()
#     )

#     if existing_link_tag is None:
#         saved_link_tag = SavedLinkTag(
#             saved_link_id=saved_link.id,
#             tag_id=tag.id,
#         )

#         db.add(saved_link_tag)

#     db.commit()
#     db.refresh(tag)

#     return tag


# @router.get("/api/saved-links/{saved_link_id}/tags", response_model=list[TagResponse])
# def get_saved_link_tags(
#     saved_link_id: uuid.UUID,
#     db: Session = Depends(get_db),
# ):
#     saved_link = (
#         db.query(SavedLink)
#         .filter(SavedLink.id == saved_link_id)
#         .first()
#     )

#     if saved_link is None:
#         raise HTTPException(status_code=404, detail="Saved link not found")

#     tags = (
#         db.query(Tag)
#         .join(SavedLinkTag, SavedLinkTag.tag_id == Tag.id)
#         .filter(SavedLinkTag.saved_link_id == saved_link_id)
#         .order_by(Tag.created_at.desc())
#         .all()
#     )

#     return tags


# @router.delete("/api/saved-links/{saved_link_id}/tags/{tag_id}")
# def detach_tag_from_saved_link(
#     saved_link_id: uuid.UUID,
#     tag_id: uuid.UUID,
#     db: Session = Depends(get_db),
# ):
#     saved_link_tag = (
#         db.query(SavedLinkTag)
#         .filter(SavedLinkTag.saved_link_id == saved_link_id)
#         .filter(SavedLinkTag.tag_id == tag_id)
#         .first()
#     )

#     if saved_link_tag is None:
#         raise HTTPException(
#             status_code=404,
#             detail="Tag is not attached to this saved link",
#         )

#     db.delete(saved_link_tag)
#     db.commit()

#     return {
#         "message": "Tag detached successfully",
#         "saved_link_id": str(saved_link_id),
#         "tag_id": str(tag_id),
#     }

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import SavedLink, SavedLinkTag, Tag, User
from app.schemas import TagAttachRequest, TagCreate, TagResponse

router = APIRouter(tags=["tags"])


def get_owned_saved_link_or_404(
    db: Session,
    saved_link_id: uuid.UUID,
    current_user: User,
) -> SavedLink:
    saved_link = (
        db.query(SavedLink)
        .filter(SavedLink.id == saved_link_id)
        .filter(SavedLink.user_id == current_user.id)
        .first()
    )

    if saved_link is None:
        raise HTTPException(status_code=404, detail="Saved link not found")

    return saved_link


def get_owned_tag_or_404(
    db: Session,
    tag_id: uuid.UUID,
    current_user: User,
) -> Tag:
    tag = (
        db.query(Tag)
        .filter(Tag.id == tag_id)
        .filter(Tag.user_id == current_user.id)
        .first()
    )

    if tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")

    return tag


@router.post("/api/me/tags", response_model=TagResponse)
def create_my_tag(
    tag_data: TagCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tag_name = tag_data.name.strip()

    if not tag_name:
        raise HTTPException(status_code=400, detail="Tag name cannot be empty")

    existing_tag = (
        db.query(Tag)
        .filter(Tag.user_id == current_user.id)
        .filter(Tag.name == tag_name)
        .first()
    )

    if existing_tag is not None:
        return existing_tag

    tag = Tag(
        user_id=current_user.id,
        name=tag_name,
    )

    db.add(tag)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()

        tag = (
            db.query(Tag)
            .filter(Tag.user_id == current_user.id)
            .filter(Tag.name == tag_name)
            .first()
        )

        if tag is None:
            raise

        return tag

    db.refresh(tag)

    return tag


@router.get("/api/me/tags", response_model=list[TagResponse])
def get_my_tags(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tags = (
        db.query(Tag)
        .filter(Tag.user_id == current_user.id)
        .order_by(Tag.created_at.desc())
        .all()
    )

    return tags


@router.post("/api/saved-links/{saved_link_id}/tags", response_model=TagResponse)
def attach_tag_to_saved_link(
    saved_link_id: uuid.UUID,
    tag_data: TagAttachRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    saved_link = get_owned_saved_link_or_404(
        db=db,
        saved_link_id=saved_link_id,
        current_user=current_user,
    )

    tag_name = tag_data.name.strip()

    if not tag_name:
        raise HTTPException(status_code=400, detail="Tag name cannot be empty")

    tag = (
        db.query(Tag)
        .filter(Tag.user_id == current_user.id)
        .filter(Tag.name == tag_name)
        .first()
    )

    if tag is None:
        tag = Tag(
            user_id=current_user.id,
            name=tag_name,
        )

        db.add(tag)

        try:
            db.flush()
        except IntegrityError:
            db.rollback()

            tag = (
                db.query(Tag)
                .filter(Tag.user_id == current_user.id)
                .filter(Tag.name == tag_name)
                .first()
            )

            if tag is None:
                raise

    existing_link_tag = (
        db.query(SavedLinkTag)
        .filter(SavedLinkTag.saved_link_id == saved_link.id)
        .filter(SavedLinkTag.tag_id == tag.id)
        .first()
    )

    if existing_link_tag is None:
        saved_link_tag = SavedLinkTag(
            saved_link_id=saved_link.id,
            tag_id=tag.id,
        )

        db.add(saved_link_tag)

    db.commit()
    db.refresh(tag)

    return tag


@router.get("/api/saved-links/{saved_link_id}/tags", response_model=list[TagResponse])
def get_saved_link_tags(
    saved_link_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    saved_link = get_owned_saved_link_or_404(
        db=db,
        saved_link_id=saved_link_id,
        current_user=current_user,
    )

    tags = (
        db.query(Tag)
        .join(SavedLinkTag, SavedLinkTag.tag_id == Tag.id)
        .filter(SavedLinkTag.saved_link_id == saved_link.id)
        .filter(Tag.user_id == current_user.id)
        .order_by(Tag.created_at.desc())
        .all()
    )

    return tags


@router.delete("/api/saved-links/{saved_link_id}/tags/{tag_id}")
def detach_tag_from_saved_link(
    saved_link_id: uuid.UUID,
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    saved_link = get_owned_saved_link_or_404(
        db=db,
        saved_link_id=saved_link_id,
        current_user=current_user,
    )

    tag = get_owned_tag_or_404(
        db=db,
        tag_id=tag_id,
        current_user=current_user,
    )

    saved_link_tag = (
        db.query(SavedLinkTag)
        .filter(SavedLinkTag.saved_link_id == saved_link.id)
        .filter(SavedLinkTag.tag_id == tag.id)
        .first()
    )

    if saved_link_tag is None:
        raise HTTPException(
            status_code=404,
            detail="Tag is not attached to this saved link",
        )

    db.delete(saved_link_tag)
    db.commit()

    return {
        "message": "Tag detached successfully",
        "saved_link_id": str(saved_link.id),
        "tag_id": str(tag.id),
    }