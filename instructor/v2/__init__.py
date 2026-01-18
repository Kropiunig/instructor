"""Instructor V2: Registry-based architecture.

This module provides the v2 implementation with a registry-based handler system.
Provider-specific functions will be added in subsequent PRs.

Usage:
    from instructor import Mode
    from instructor.v2 import mode_registry

    # Check if a mode is registered
    if mode_registry.is_registered(Provider.ANTHROPIC, Mode.TOOLS):
        handlers = mode_registry.get_handlers(Provider.ANTHROPIC, Mode.TOOLS)
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
]
