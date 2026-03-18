import os

import instructor
import pytest
from pydantic import BaseModel

REASONING_MODEL = os.getenv("ANTHROPIC_REASONING_MODEL", "")


class Answer(BaseModel):
    answer: float


@pytest.mark.skipif(
    not REASONING_MODEL,
    reason="ANTHROPIC_REASONING_MODEL environment variable not set",
)
def test_reasoning():
    client = instructor.from_provider(
        REASONING_MODEL,
        mode=instructor.Mode.ANTHROPIC_REASONING_TOOLS,
    )
    response = client.chat.completions.create(
        response_model=Answer,
        messages=[
            {
                "role": "user",
                "content": "Which is larger, 9.11 or 9.8? Think carefully about decimal places.",
            },
        ],
        temperature=1,  # Required when thinking is enabled
        max_tokens=2000,
        thinking={"type": "enabled", "budget_tokens": 1024},
        max_retries=3,  # Retry if the model gets it wrong
    )

    # Assertions to validate the response
    assert isinstance(response, Answer)
    assert response.answer == 9.8
