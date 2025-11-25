# Instructor: Structured Outputs for LLMs

Get reliable JSON from any LLM. Built on Pydantic for validation, type safety, and IDE support.

[![PyPI](https://img.shields.io/pypi/v/instructor?style=flat-square)](https://pypi.org/project/instructor/)
[![Downloads](https://img.shields.io/pypi/dm/instructor?style=flat-square)](https://pypi.org/project/instructor/)
[![GitHub Stars](https://img.shields.io/github/stars/instructor-ai/instructor?style=flat-square)](https://github.com/instructor-ai/instructor)
[![Discord](https://img.shields.io/discord/1192334452110659664?style=flat-square)](https://discord.gg/bD9YE9JArw)
[![Twitter](https://img.shields.io/twitter/follow/jxnlco?style=flat-square)](https://twitter.com/jxnlco)

> **Use Instructor for fast extraction, reach for PydanticAI when you need agents.** Instructor keeps schema-first flows simple and cheap. If your app needs richer agent runs, built-in observability, or shareable traces, try [PydanticAI](https://ai.pydantic.dev/). It is the official agent runtime from the Pydantic team and extends your existing Instructor models with typed tools, replayable datasets, evals, and production dashboards.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Quick start](#quick-start)
- [Feature highlights](#feature-highlights)
- [Provider coverage](#provider-coverage)
- [Production-ready patterns](#production-ready-patterns)
- [Used in production by](#used-in-production-by)
- [Documentation & resources](#documentation--resources)
- [Why Instructor over alternatives?](#why-instructor-over-alternatives)
- [Contributing](#contributing)
- [License](#license)
- [Community](#community)

## Overview

Instructor is the leading open-source toolkit for structured LLM outputs. Define a Pydantic model once and reuse it across 15+ providers (OpenAI, Anthropic, Google, Groq, Mistral, Cohere, Vertex AI, Bedrock, Perplexity, Ollama, DeepSeek, and more). The library offers sync and async clients, retries, streaming (`Partial`, `IterableModel`, `Maybe`), validation helpers, moderation hooks, and batching utilities so that every request returns typed data you can trust. With 3M+ monthly downloads, 10k+ GitHub stars, and 1000+ contributors, Instructor is battle-tested in production workloads.

### Without Instructor vs With Instructor

<table>
<tr>
<td><b>Without Instructor</b></td>
<td><b>With Instructor</b></td>
</tr>
<tr>
<td>

```python
response = openai.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "..."}],
    tools=[
        {
            "type": "function",
            "function": {
                "name": "extract_user",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer"},
                    },
                },
            },
        }
    ],
)

tool_call = response.choices[0].message.tool_calls[0]
user_data = json.loads(tool_call.function.arguments)

if "name" not in user_data:
    raise ValueError("Missing name")
```

</td>
<td>

```python
import instructor
from pydantic import BaseModel


class User(BaseModel):
    name: str
    age: int


client = instructor.from_provider("openai/gpt-4")
user = client.chat.completions.create(
    response_model=User,
    messages=[{"role": "user", "content": "..."}],
)
```

</td>
</tr>
</table>

## Installation

Instructor targets Python 3.9+.

### Runtime install

```bash
uv pip install instructor
```

Install provider extras as needed:

```bash
uv pip install "instructor[anthropic,google,groq]"
```

### Project-managed install

```bash
uv add instructor
```

### Local development

```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev,anthropic]"
```

## Quick start

### Extract validated objects

```python
import instructor
from pydantic import BaseModel


class Product(BaseModel):
    name: str
    price: float
    in_stock: bool


client = instructor.from_provider("openai/gpt-4o-mini")
product = client.chat.completions.create(
    response_model=Product,
    messages=[{"role": "user", "content": "iPhone 15 Pro, $999, available now"}],
)
print(product)  # Product(name='iPhone 15 Pro', price=999.0, in_stock=True)
```

Swap `"openai/gpt-4o-mini"` with any supported provider string without changing the rest of your code.

### Stream partial objects

```python
from instructor import Partial

for partial_product in client.chat.completions.create(
    response_model=Partial[Product],
    messages=[{"role": "user", "content": "Describe a laptop"}],
    stream=True,
):
    print(partial_product)
```

### Async usage

```python
import asyncio

async def main() -> None:
    aclient = instructor.from_provider("openai/gpt-4o-mini", async_client=True)
    product = await aclient.chat.completions.create(
        response_model=Product,
        messages=[{"role": "user", "content": "Steam Deck, $399"}],
    )
    print(product)

asyncio.run(main())
```

## Feature highlights

- **Schema-first development**: Pydantic-powered `BaseModel`s and helpers such as `OpenAISchema`, `generate_openai_schema`, and `generate_anthropic_schema` keep prompts and outputs in sync with your types.
- **Automatic validation and retries**: Raise `field_validator` errors, plug in `llm_validator` or `openai_moderation`, and let Instructor re-ask with clear error messages until the schema passes.
- **Streaming and partial results**: Use `Partial`, `IterableModel`, and `Maybe` to stream nested objects or chunked lists as soon as tokens arrive.
- **Hooks and observability**: `client.on("completion:*", ...)` handlers expose every request and response so you can log, trace, or enforce policy before a response escapes.
- **Batching and distillation**: Fan out jobs with `BatchProcessor`, `BatchRequest`, and `BatchJob`, or build fine-tuning corpora with `FinetuneFormat` and `Instructions`.
- **Multimodal inputs**: Attach `Image` and `Audio` payloads to prompts while keeping the same response model API.
- **Multi-language ecosystem**: Official ports exist for [TypeScript](https://js.useinstructor.com), [Go](https://go.useinstructor.com), [Ruby](https://ruby.useinstructor.com), [Elixir](https://hex.pm/packages/instructor), and [Rust](https://rust.useinstructor.com).

## Provider coverage

Use one call site for every provider:

```python
# OpenAI
client = instructor.from_provider("openai/gpt-4o")

# Anthropic
client = instructor.from_provider("anthropic/claude-3-5-sonnet")

# Google Gemini
client = instructor.from_provider("google/gemini-pro")

# Groq
client = instructor.from_provider("groq/llama-3.1-8b-instant")

# Ollama or other local runtimes
client = instructor.from_provider("ollama/llama3.2")

# Provide keys inline when needed
client = instructor.from_provider("openai/gpt-4o", api_key="sk-...")
```

Instructor also patches native clients (`from_openai`, `from_anthropic`, `from_vertexai`, `from_bedrock`, `from_mistral`, `from_groq`, `from_litellm`, etc.) so you can keep your existing SDK configuration.

## Production-ready patterns

### Automatic retries

```python
from pydantic import BaseModel, field_validator


class User(BaseModel):
    name: str
    age: int

    @field_validator("age")
    @classmethod
    def validate_age(cls, value: int) -> int:
        if value < 0:
            raise ValueError("Age must be positive")
        return value


user = client.chat.completions.create(
    response_model=User,
    messages=[{"role": "user", "content": "..."}],
    max_retries=3,
)
```

### Streaming support

```python
from instructor import Partial

for partial_user in client.chat.completions.create(
    response_model=Partial[User],
    messages=[{"role": "user", "content": "..."}],
    stream=True,
):
    print(partial_user)
```

### Nested objects

```python
from typing import List
from pydantic import BaseModel


class Address(BaseModel):
    street: str
    city: str
    country: str


class Person(BaseModel):
    name: str
    age: int
    addresses: List[Address]


person = client.chat.completions.create(
    response_model=Person,
    messages=[{"role": "user", "content": "..."}],
)
```

## Used in production by

Trusted by over 100,000 developers and companies building AI applications:

- **3M+ monthly downloads**
- **10K+ GitHub stars**
- **1000+ community contributors**

Teams at OpenAI, Google, Microsoft, AWS, and many YC startups rely on Instructor to keep structured data flows stable.

## Documentation & resources

- [Python docs](https://python.useinstructor.com) – concepts, guides, and API details
- [Examples gallery](https://python.useinstructor.com/examples/) – copy-paste recipes for common tasks
- [Provider integrations](https://python.useinstructor.com/integrations/) – setup notes for each LLM vendor
- [Blog](https://python.useinstructor.com/blog/) – deep dives, tutorials, and release notes
- [Prompting and validation tips](https://python.useinstructor.com/prompting/) – guidance for schema-first prompts
- `instructor docs [topic]` – open the docs search from your terminal

## Why Instructor over alternatives?

- **vs Raw JSON mode**: Automatic validation, retries, streaming, and nested schema support with zero manual parsing.
- **vs LangChain or LlamaIndex**: Instructor focuses on structured extraction, so the API stays light, fast, and easy to debug.
- **vs Custom glue code**: Thousands of teams have already burned down the edge cases around retries, moderation, schema drift, and provider quirks—Instructor ships those fixes for free.

## Contributing

We welcome contributions of all sizes.

1. Read `AGENT.md` (and `CLAUDE.md` if you use Claude) for repository conventions.
2. Fork the repo, then create a feature branch from `main` (`git checkout -b feat/<topic>`).
3. Set up your environment with `uv`:

   ```bash
   uv venv
   source .venv/bin/activate
   uv pip install -e ".[dev,anthropic]"
   uv run ruff check instructor examples tests
   uv run ruff format instructor examples tests
   uv run ty check
   uv run pytest tests/ -k "not llm and not openai"
   ```

4. Keep commits focused, follow the `type(scope): subject` conventional commit format, and open a PR using the templates in `.github/`.
5. For large features, discuss your plan in an issue or on [Discord](https://discord.gg/bD9YE9JArw) before writing a lot of code.

Check the [good first issues](https://github.com/instructor-ai/instructor/labels/good%20first%20issue) label if you want a scoped task.

## License

Instructor is released under the [MIT License](https://github.com/instructor-ai/instructor/blob/main/LICENSE).

## Community

- Join the [Discord server](https://discord.gg/bD9YE9JArw) for help, office hours, and release notes.
- Follow [@jxnlco on Twitter](https://twitter.com/jxnlco) for project updates.
- Watch or star the [GitHub repo](https://github.com/instructor-ai/instructor) to get notified about new releases.
- Share what you build—tag your tutorials, demos, or talks so we can highlight them in the blog.

---

<p align="center">
Built by the Instructor community. Special thanks to <a href="https://twitter.com/jxnlco">Jason Liu</a> and <a href="https://github.com/instructor-ai/instructor/graphs/contributors">all contributors</a>.
</p>