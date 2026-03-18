import os

import instructor

models = [os.getenv("ANTHROPIC_MODEL")] if os.getenv("ANTHROPIC_MODEL") else []
modes = [
    instructor.Mode.ANTHROPIC_TOOLS,
]
