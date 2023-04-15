from __future__ import annotations

from typing import List
from uuid import uuid4
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Uuid,
    ARRAY,
    func,
)
import sqlalchemy
from sqlalchemy.orm import relationship, Mapped, DeclarativeBase

from db import Base


sessions_items = Table(
    "sessionsitems",
    Base.metadata,
    Column("id", Uuid, primary_key=True, default=uuid4),
    Column("item_id", ForeignKey("items.id"), primary_key=True),
    Column("session_id", ForeignKey("sessions.id"), primary_key=True),
)


class Item(Base):
    __tablename__ = "items"

    id = Column(
        Uuid, primary_key=True, index=True, server_default=func.uuid_generate_v4()
    )
    price = Column(Integer)
    name = Column(String)
    description = Column(String)
    short_description = Column(String)
    is_sold = Column(Boolean, default=False)
    images = Column(ARRAY(String))
    created_at = Column(DateTime, server_default=func.now())

    sessions: Mapped[List[UserSession]] = relationship(
        secondary=sessions_items, back_populates="items"
    )


class UserSession(Base):
    __tablename__ = "sessions"

    id = Column(
        Uuid,
        primary_key=True,
        index=True,
        default=uuid4,
    )
    items: Mapped[List[Item]] = relationship(
        secondary=sessions_items, back_populates="sessions"
    )
    created_at = Column(DateTime, server_default=func.now())

    class PydanticMeta:
        ordering = "created_at"
