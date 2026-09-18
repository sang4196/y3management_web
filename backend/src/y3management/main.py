"""ASGI factory for Uvicorn. Importing this module opens no database connection."""

from y3management.application import create_app

__all__ = ["create_app"]
