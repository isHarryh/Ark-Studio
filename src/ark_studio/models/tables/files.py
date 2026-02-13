# Copyright (c) 2024-2026, Harry Huang
# @ BSD 3-Clause License
from sqlmodel import SQLModel, Field, Index


class FileRecord(SQLModel, table=True):
    """File system record in database."""

    __tablename__ = "files"  # type: ignore
    __table_args__ = (
        Index("idx_name", "name"),
        Index("idx_path", "path"),
        Index("idx_type", "type"),
        Index("idx_parent", "parent"),
    )

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=False)
    path: str = Field(index=False, unique=True)
    type: str = Field(index=False)  # 'file' or 'folder'
    size: int = Field(default=0)
    parent: str | None = Field(default=None, index=False)
