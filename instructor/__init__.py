import importlib.util

__version__ = "1.14.4"

from .mode import Mode
from .processing.multimodal import Image, Audio

from .dsl import (
    CitationMixin,
    Maybe,
    Partial,
    IterableModel,
)

from .validation import llm_validator, openai_moderation
from .processing.function_calls import (
    ResponseSchema,
    response_schema,
    OpenAISchema,
    openai_schema,
)
from .processing.schema import generate_openai_schema, generate_anthropic_schema
from .core.patch import apatch, patch
from .core.client import (
    Instructor,
    AsyncInstructor,
    from_openai,
    from_litellm,
)
from .core import hooks
from .utils.providers import Provider
from .auto_client import from_provider
from .batch import BatchProcessor, BatchRequest, BatchJob
from .distil import FinetuneFormat, Instructions

__all__ = [
    "Instructor",
    "Image",
    "Audio",
    "from_openai",
    "from_litellm",
    "from_provider",
    "AsyncInstructor",
    "Provider",
    "ResponseSchema",
    "response_schema",
    "OpenAISchema",
    "CitationMixin",
    "IterableModel",
    "Maybe",
    "Partial",
    "openai_schema",
    "generate_openai_schema",
    "generate_anthropic_schema",
    "Mode",
    "patch",
    "apatch",
    "FinetuneFormat",
    "Instructions",
    "BatchProcessor",
    "BatchRequest",
    "BatchJob",
    "llm_validator",
    "openai_moderation",
    "hooks",
    "client",
]

from . import client


if importlib.util.find_spec("google") and importlib.util.find_spec("google.genai") is not None:
    from .v2.providers.genai.client import from_genai

    __all__ += ["from_genai"]
