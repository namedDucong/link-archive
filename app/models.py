import uuid

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.mysql import BINARY
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator

from app.db import Base


class BinaryUUID(TypeDecorator):
    """
    MySQL BINARY(16)에 UUID를 저장하기 위한 타입.

    DB에는 16바이트 binary로 저장하고,
    Python 코드에서는 uuid.UUID 객체로 다룰 수 있게 해준다.
    """

    impl = BINARY(16)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """
        Python 값 → DB에 저장할 값으로 변환.

        예:
        "550e8400-e29b-41d4-a716-446655440000"
        → 16바이트 binary
        """
        if value is None:
            return None

        if isinstance(value, uuid.UUID):
            return value.bytes

        if isinstance(value, bytes):
            return value

        if isinstance(value, str):
            return uuid.UUID(value).bytes

        raise ValueError(f"Invalid UUID value: {value}")

    def process_result_value(self, value, dialect):
        """
        DB 값 → Python 값으로 변환.

        DB의 BINARY(16)
        → uuid.UUID 객체
        """
        if value is None:
            return None

        if isinstance(value, uuid.UUID):
            return value

        return uuid.UUID(bytes=value)


class User(Base):
    __tablename__ = "users"

    id = Column(BinaryUUID(), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, unique=True)
    name = Column(String(255), nullable=True)

    password_hash = Column(String(255), nullable=True)

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    saved_links = relationship(
        "SavedLink",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    tags = relationship(
        "Tag",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    collections = relationship(
        "Collection",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class CrawledPage(Base):
    __tablename__ = "crawled_pages"

    id = Column(BinaryUUID(), primary_key=True, default=uuid.uuid4)

    canonical_url = Column(Text, nullable=False)
    canonical_url_hash = Column(String(255), nullable=False)

    title = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    domain = Column(String(255), nullable=True)
    author = Column(String(255), nullable=True)
    published_at = Column(DateTime, nullable=True)
    page_language = Column(String(50), nullable=True)

    raw_html_path = Column(Text, nullable=True)
    extracted_text_path = Column(Text, nullable=True)
    screenshot_path = Column(Text, nullable=True)
    thumbnail_path = Column(Text, nullable=True)

    crawl_status = Column(
        String(50),
        nullable=False,
        server_default=text("'done'"),
    )

    crawled_at = Column(DateTime, nullable=True)

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
    )

    saved_links = relationship(
        "SavedLink",
        back_populates="page",
    )

    __table_args__ = (
        UniqueConstraint(
            "canonical_url_hash",
            name="unique_canonical_url_hash",
        ),
        Index("idx_crawled_pages_domain", "domain"),
        Index("idx_crawled_pages_crawl_status", "crawl_status"),
    )


class SavedLink(Base):
    __tablename__ = "saved_links"

    id = Column(BinaryUUID(), primary_key=True, default=uuid.uuid4)

    user_id = Column(
        BinaryUUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    page_id = Column(
        BinaryUUID(),
        ForeignKey("crawled_pages.id", ondelete="SET NULL"),
        nullable=True,
    )

    original_url = Column(Text, nullable=False)
    original_url_hash = Column(String(255), nullable=False)

    memo = Column(Text, nullable=True)

    status = Column(
        String(50),
        nullable=False,
        server_default=text("'active'"),
    )

    crawl_status = Column(
        String(50),
        nullable=False,
        server_default=text("'queued'"),
    )

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
    )

    archived_at = Column(DateTime, nullable=True)

    user = relationship(
        "User",
        back_populates="saved_links",
    )

    page = relationship(
        "CrawledPage",
        back_populates="saved_links",
    )

    crawl_jobs = relationship(
        "CrawlJob",
        back_populates="saved_link",
        cascade="all, delete-orphan",
    )

    saved_link_tags = relationship(
        "SavedLinkTag",
        back_populates="saved_link",
        cascade="all, delete-orphan",
    )

    collection_saved_links = relationship(
        "CollectionSavedLink",
        back_populates="saved_link",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "original_url_hash",
            name="unique_user_original_url",
        ),
        Index("idx_saved_links_user_created", "user_id", "created_at"),
        Index("idx_saved_links_status", "status"),
        Index("idx_saved_links_crawl_status", "crawl_status"),
        Index("idx_saved_links_page_id", "page_id"),
    )


class CrawlJob(Base):
    __tablename__ = "crawl_jobs"

    id = Column(BinaryUUID(), primary_key=True, default=uuid.uuid4)

    saved_link_id = Column(
        BinaryUUID(),
        ForeignKey("saved_links.id", ondelete="CASCADE"),
        nullable=False,
    )

    status = Column(
        String(50),
        nullable=False,
        server_default=text("'queued'"),
    )

    attempt_count = Column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )

    last_error = Column(Text, nullable=True)

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    saved_link = relationship(
        "SavedLink",
        back_populates="crawl_jobs",
    )

    __table_args__ = (
        Index("idx_crawl_jobs_status_created", "status", "created_at"),
        Index("idx_crawl_jobs_saved_link_id", "saved_link_id"),
    )


class Tag(Base):
    __tablename__ = "tags"

    id = Column(BinaryUUID(), primary_key=True, default=uuid.uuid4)

    user_id = Column(
        BinaryUUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    name = Column(String(255), nullable=False)

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    user = relationship(
        "User",
        back_populates="tags",
    )

    saved_link_tags = relationship(
        "SavedLinkTag",
        back_populates="tag",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "name",
            name="unique_user_tag",
        ),
        Index("idx_tags_user_id", "user_id"),
    )


class SavedLinkTag(Base):
    __tablename__ = "saved_link_tags"

    saved_link_id = Column(
        BinaryUUID(),
        ForeignKey("saved_links.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )

    tag_id = Column(
        BinaryUUID(),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )

    saved_link = relationship(
        "SavedLink",
        back_populates="saved_link_tags",
    )

    tag = relationship(
        "Tag",
        back_populates="saved_link_tags",
    )

    __table_args__ = (
        Index("idx_slt_tag_id", "tag_id"),
    )


class Collection(Base):
    __tablename__ = "collections"

    id = Column(BinaryUUID(), primary_key=True, default=uuid.uuid4)

    user_id = Column(
        BinaryUUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    user = relationship(
        "User",
        back_populates="collections",
    )

    collection_saved_links = relationship(
        "CollectionSavedLink",
        back_populates="collection",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "name",
            name="unique_user_collection",
        ),
        Index("idx_collections_user_id", "user_id"),
    )


class CollectionSavedLink(Base):
    __tablename__ = "collection_saved_links"

    collection_id = Column(
        BinaryUUID(),
        ForeignKey("collections.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )

    saved_link_id = Column(
        BinaryUUID(),
        ForeignKey("saved_links.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )

    added_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    collection = relationship(
        "Collection",
        back_populates="collection_saved_links",
    )

    saved_link = relationship(
        "SavedLink",
        back_populates="collection_saved_links",
    )

    __table_args__ = (
        Index("idx_csl_saved_link_id", "saved_link_id"),
    )