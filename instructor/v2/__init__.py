"""Instructor V2: Registry-based architecture.

This module provides the v2 implementation with a registry-based handler system.

Usage:
    from instructor import Mode
    from instructor.v2 import from_anthropic, from_openai

    client = from_anthropic(anthropic_client, mode=Mode.TOOLS)
    client = from_openai(openai_client, mode=Mode.TOOLS)
"""

from instructor import Mode, Provider
from instructor.v2.core.decorators import register_mode_handler
from instructor.v2.core.handler import ModeHandler
from instructor.v2.core.patch import patch_v2
from instructor.v2.core.protocols import ReaskHandler, RequestHandler, ResponseParser
from instructor.v2.core.registry import (
    ModeHandlers,
    ModeRegistry,
    mode_registry,
    normalize_mode,
)

# Import providers (will auto-register modes)
try:
    from instructor.v2.providers.anthropic import from_anthropic
except ImportError:
    from_anthropic = None  # type: ignore

try:
    from instructor.v2.providers.openai import from_openai
except ImportError:
    from_openai = None  # type: ignore

__all__ = [
    # Re-exports from instructor
    "Mode",
    "Provider",
    # Core infrastructure
    "ModeHandler",
    "ModeHandlers",
    "ModeRegistry",
    "mode_registry",
    "normalize_mode",
    "patch_v2",
    "register_mode_handler",
    # Protocols
    "ReaskHandler",
    "RequestHandler",
    "ResponseParser",
    # Providers
    "from_anthropic",
    "from_openai",
]
