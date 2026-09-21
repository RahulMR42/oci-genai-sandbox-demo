"""OCI's OpenAI-compatible Responses API adapter."""

from __future__ import annotations

from dataclasses import dataclass

import httpx
from openai import OpenAI


@dataclass(frozen=True)
class OciOpenAIConfig:
    region: str
    compartment_id: str
    project_id: str
    model: str
    api_key: str

    @property
    def base_url(self) -> str:
        return f"https://inference.generativeai.{self.region}.oci.oraclecloud.com/openai/v1"


def run_prompt(config: OciOpenAIConfig, prompt: str) -> str:
    """Run one OCI Responses API request and return only the generated text."""
    client = OpenAI(
        base_url=config.base_url,
        api_key=config.api_key,
        project=config.project_id,
        # OCI endpoints are reached directly in this environment; avoid inheriting a proxy.
        http_client=httpx.Client(trust_env=False),
    )
    response = client.responses.create(model=config.model, input=prompt)
    return response.output_text or "OCI returned no text output."
