import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.db import get_db
from app.models import Collection, CollectionSavedLink, SavedLink, User
from app.schemas import CollectionCreate, CollectionResponse, CollectionUpdate, SavedLinkResponse

router = APIRouter(tags=["collections"])


@router.post("/api/users/{user_id}/collections", response_model=CollectionResponse)
def create_collection(
    user_id: uuid.UUID,
    collection_data: CollectionCreate,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    collection_name = collection_data.name.strip()

    if not collection_name:
        raise HTTPException(status_code=400, detail="Collection name cannot be empty")

    collection = Collection(
        user_id=user.id,
        name=collection_name,
        description=collection_data.description,
    )

    db.add(collection)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Collection with this name already exists for this user",
        )

    db.refresh(collection)

    return collection


@router.get("/api/users/{user_id}/collections", response_model=list[CollectionResponse])
def get_user_collections(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    user_exists = (
        db.query(User.id)
        .filter(User.id == user_id)
        .first()
    )

    if user_exists is None:
        raise HTTPException(status_code=404, detail="User not found")

    collections = (
        db.query(Collection)
        .filter(Collection.user_id == user_id)
        .order_by(Collection.created_at.desc())
        .all()
    )

    return collections


@router.get("/api/collections/{collection_id}", response_model=CollectionResponse)
def get_collection(
    collection_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    collection = (
        db.query(Collection)
        .filter(Collection.id == collection_id)
        .first()
    )

    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    return collection


@router.patch("/api/collections/{collection_id}", response_model=CollectionResponse)
def update_collection(
    collection_id: uuid.UUID,
    update_data: CollectionUpdate,
    db: Session = Depends(get_db),
):
    collection = (
        db.query(Collection)
        .filter(Collection.id == collection_id)
        .first()
    )

    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    data = update_data.model_dump(exclude_unset=True)

    if "name" in data:
        new_name = data["name"].strip()

        if not new_name:
            raise HTTPException(status_code=400, detail="Collection name cannot be empty")

        collection.name = new_name

    if "description" in data:
        collection.description = data["description"]

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Collection with this name already exists for this user",
        )

    db.refresh(collection)

    return collection


@router.delete("/api/collections/{collection_id}")
def delete_collection(
    collection_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    collection = (
        db.query(Collection)
        .filter(Collection.id == collection_id)
        .first()
    )

    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    db.delete(collection)
    db.commit()

    return {
        "message": "Collection deleted successfully",
        "id": str(collection_id),
    }


@router.post("/api/collections/{collection_id}/links/{saved_link_id}")
def add_saved_link_to_collection(
    collection_id: uuid.UUID,
    saved_link_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    collection = (
        db.query(Collection)
        .filter(Collection.id == collection_id)
        .first()
    )

    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    saved_link = (
        db.query(SavedLink)
        .filter(SavedLink.id == saved_link_id)
        .first()
    )

    if saved_link is None:
        raise HTTPException(status_code=404, detail="Saved link not found")

    if saved_link.user_id != collection.user_id:
        raise HTTPException(
            status_code=403,
            detail="This saved link does not belong to the collection owner",
        )

    existing = (
        db.query(CollectionSavedLink)
        .filter(CollectionSavedLink.collection_id == collection.id)
        .filter(CollectionSavedLink.saved_link_id == saved_link.id)
        .first()
    )

    if existing is not None:
        return {
            "message": "Saved link is already in this collection",
            "collection_id": str(collection_id),
            "saved_link_id": str(saved_link_id),
        }

    collection_saved_link = CollectionSavedLink(
        collection_id=collection.id,
        saved_link_id=saved_link.id,
    )

    db.add(collection_saved_link)
    db.commit()

    return {
        "message": "Saved link added to collection successfully",
        "collection_id": str(collection_id),
        "saved_link_id": str(saved_link_id),
    }


@router.get("/api/collections/{collection_id}/links", response_model=list[SavedLinkResponse])
def get_collection_saved_links(
    collection_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    collection = (
        db.query(Collection)
        .filter(Collection.id == collection_id)
        .first()
    )

    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    saved_links = (
        db.query(SavedLink)
        .join(CollectionSavedLink, CollectionSavedLink.saved_link_id == SavedLink.id)
        .options(joinedload(SavedLink.page))
        .filter(CollectionSavedLink.collection_id == collection_id)
        .order_by(CollectionSavedLink.added_at.desc())
        .limit(limit)
        .all()
    )

    return saved_links


@router.delete("/api/collections/{collection_id}/links/{saved_link_id}")
def remove_saved_link_from_collection(
    collection_id: uuid.UUID,
    saved_link_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    collection_saved_link = (
        db.query(CollectionSavedLink)
        .filter(CollectionSavedLink.collection_id == collection_id)
        .filter(CollectionSavedLink.saved_link_id == saved_link_id)
        .first()
    )

    if collection_saved_link is None:
        raise HTTPException(
            status_code=404,
            detail="Saved link is not in this collection",
        )

    db.delete(collection_saved_link)
    db.commit()

    return {
        "message": "Saved link removed from collection successfully",
        "collection_id": str(collection_id),
        "saved_link_id": str(saved_link_id),
    }