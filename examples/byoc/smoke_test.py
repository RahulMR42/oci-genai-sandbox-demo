"""Non-secret smoke test for the BYOC image."""

import platform

import openai
import pydantic

print(f"Python: {platform.python_version()}")
print(f"OpenAI SDK: {openai.__version__}")
print(f"Pydantic: {pydantic.__version__}")
