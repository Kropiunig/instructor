"""Instructor V2: Registry-based architecture.

This module provides the v2 implementation with a registry-based handler system.

Usage:
    from instructor import Mode
    from instructor.v2 import from_anthropic, from_openai, from_genai

    client = from_anthropic(anthropic_client, mode=Mode.TOOLS)
    client = from_openai(openai_client, mode=Mode.TOOLS)
    client = from_genai(genai_client, mode=Mode.TOOLS)
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

try:
    from instructor.v2.providers.genai import from_genai
except ImportError:
    from_genai = None  # type: ignore

try:
    from instructor.v2.providers.cohere import from_cohere
except ImportError:
    from_cohere = None  # type: ignore

try:
    from instructor.v2.providers.mistral import from_mistral
except ImportError:
    from_mistral = None  # type: ignore

try:
    from instructor.v2.providers.xai import from_xai
except ImportError:
    from_xai = None  # type: ignore

try:
    from instructor.v2.providers.groq import from_groq
except ImportError:
    from_groq = None  # type: ignore

try:
    from instructor.v2.providers.fireworks import from_fireworks
except ImportError:
    from_fireworks = None  # type: ignore

try:
    from instructor.v2.providers.cerebras import from_cerebras
except ImportError:
    from_cerebras = None  # type: ignore

try:
    from instructor.v2.providers.writer import from_writer
except ImportError:
    from_writer = None  # type: ignore

try:
    from instructor.v2.providers.bedrock import from_bedrock
except ImportError:
    from_bedrock = None  # type: ignore

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
    "from_bedrock",
    "from_cerebras",
    "from_cohere",
    "from_fireworks",
    "from_genai",
    "from_groq",
    "from_mistral",
    "from_openai",
    "from_writer",
    "from_xai",
]
