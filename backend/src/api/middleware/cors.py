from collections.abc import Sequence
from typing import Iterable

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

DEFAULT_ORIGINS: tuple[str, ...] = ("http://localhost:3000",)


def setup_cors(app: FastAPI, allow_origins: Iterable[str] | None = None) -> None:
    """Configure CORS middleware for the FastAPI application."""
    origins: Sequence[str] = tuple(allow_origins) if allow_origins else DEFAULT_ORIGINS

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
