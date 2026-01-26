"""Backward-compatible VertexAI client module."""

from .v2.providers.vertexai.client import from_vertexai

__all__ = ["from_vertexai"]
