"""Définition des modèles SQLModel."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship, SQLModel


class TimestampedModel(SQLModel, table=False):
    """Mixin pour ajouter des colonnes de suivi temporel."""

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class FilmTagLink(SQLModel, table=True):
    """Table de jointure film-tag."""

    film_id: Optional[int] = Field(
        default=None, foreign_key="film.id", primary_key=True, nullable=False
    )
    tag_id: Optional[int] = Field(
        default=None, foreign_key="tag.id", primary_key=True, nullable=False
    )


class User(TimestampedModel, table=True):
    """Utilisateur pouvant noter des films."""

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(
        sa_column=Column("username", String(80), unique=True, index=True, nullable=False)
    )
    email: str = Field(
        sa_column=Column("email", String(255), unique=True, index=True, nullable=False)
    )
    hashed_password: str = Field(nullable=False)
    bio: Optional[str] = Field(default=None, max_length=500)

    reviews: list["Review"] = Relationship(
        sa_relationship=relationship("Review", back_populates="user")
    )
    watchlist_items: list["WatchlistItem"] = Relationship(
        sa_relationship=relationship(
            "WatchlistItem",
            back_populates="user",
            cascade="all, delete-orphan",
        )
    )


class Tag(SQLModel, table=True):
    """Tag associé à un film (genre, ambiance, etc.)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(sa_column=Column(String(80), unique=True, index=True, nullable=False))

    films: list["Film"] = Relationship(
        sa_relationship=relationship(
            "Film",
            secondary=FilmTagLink.__table__,
            back_populates="tags",
        )
    )


class Film(TimestampedModel, table=True):
    """Information de base sur un film."""

    id: Optional[int] = Field(default=None, primary_key=True)
    external_id: Optional[str] = Field(default=None, index=True)
    title: str
    overview: Optional[str] = Field(default=None)
    release_year: Optional[int] = Field(default=None, index=True)
    poster_url: Optional[str] = Field(default=None)
    backdrop_url: Optional[str] = Field(default=None)
    runtime_minutes: Optional[int] = Field(default=None)
    director: Optional[str] = Field(default=None)
    country: Optional[str] = Field(default=None)

    tags: list[Tag] = Relationship(
        sa_relationship=relationship(
            "Tag",
            secondary=FilmTagLink.__table__,
            back_populates="films",
        )
    )
    reviews: list["Review"] = Relationship(
        sa_relationship=relationship("Review", back_populates="film")
    )
    watchlist_items: list["WatchlistItem"] = Relationship(
        sa_relationship=relationship(
            "WatchlistItem",
            back_populates="film",
            cascade="all, delete-orphan",
        )
    )


class Review(TimestampedModel, table=True):
    """Avis d'un utilisateur sur un film."""

    __table_args__ = (UniqueConstraint("user_id", "film_id", name="uq_review_user_film"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    rating: int = Field(ge=1, le=5, nullable=False)
    comment: Optional[str] = Field(default=None, max_length=2000)
    user_id: int = Field(foreign_key="user.id", nullable=False)
    film_id: int = Field(foreign_key="film.id", nullable=False, index=True)

    user: Optional[User] = Relationship(
        sa_relationship=relationship("User", back_populates="reviews")
    )
    film: Optional[Film] = Relationship(
        sa_relationship=relationship("Film", back_populates="reviews")
    )


class WatchlistItem(TimestampedModel, table=True):
    """Association entre un utilisateur et un film de sa watchlist."""

    __table_args__ = (UniqueConstraint("user_id", "film_id", name="uq_watchlist_user_film"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", nullable=False, index=True)
    film_id: int = Field(foreign_key="film.id", nullable=False, index=True)

    user: Optional[User] = Relationship(
        sa_relationship=relationship("User", back_populates="watchlist_items")
    )
    film: Optional[Film] = Relationship(
        sa_relationship=relationship("Film", back_populates="watchlist_items")
    )

