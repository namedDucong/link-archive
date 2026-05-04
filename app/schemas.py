import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, HttpUrl


class UserCreate(BaseModel):
    email: EmailStr
    name: Optional[str] = None


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SavedLinkCreate(BaseModel):
    original_url: HttpUrl
    memo: Optional[str] = None


class CrawledPageBriefResponse(BaseModel):
    id: uuid.UUID
    canonical_url: str
    title: Optional[str] = None
    description: Optional[str] = None
    domain: Optional[str] = None
    thumbnail_path: Optional[str] = None
    crawl_status: str
    crawled_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SavedLinkResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    page_id: Optional[uuid.UUID] = None

    original_url: str
    memo: Optional[str] = None

    status: str
    crawl_status: str

    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime] = None

    page: Optional[CrawledPageBriefResponse] = None

    model_config = ConfigDict(from_attributes=True)


class SavedLinkUpdate(BaseModel):
    memo: Optional[str] = None
    status: Optional[Literal["active", "archived", "deleted"]] = None


class CrawlJobResponse(BaseModel):
    id: uuid.UUID
    saved_link_id: uuid.UUID

    status: str
    attempt_count: int
    last_error: Optional[str] = None

    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

"""
TagCreate
→ 사용자가 태그를 직접 만들 때 사용

TagAttachRequest
→ 특정 saved_link에 태그를 붙일 때 사용

TagResponse
→ 태그 응답 형식
"""

class TagCreate(BaseModel):
    name: str


class TagAttachRequest(BaseModel):
    name: str


class TagResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

"""
collections
→ 컬렉션 자체

collection_saved_links
→ 컬렉션과 saved_links 연결
"""

class CollectionCreate(BaseModel):
    name: str
    description: Optional[str] = None


class CollectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class CollectionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)