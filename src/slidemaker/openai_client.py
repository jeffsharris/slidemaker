from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any

from openai import AsyncOpenAI
from openai import APIConnectionError, APIError, APITimeoutError, RateLimitError

from .utils import BackoffConfig, retry_async


class RetryableParseError(Exception):
    pass


@dataclass
class GradeResult:
    passed: bool
    score: float
    failures: list[str]
    improvements: list[str]
    summary: str


def _is_retryable(exc: Exception) -> bool:
    if isinstance(exc, (RateLimitError, APIConnectionError, APITimeoutError)):
        return True
    if isinstance(exc, RetryableParseError):
        return True
    if isinstance(exc, APIError):
        status = getattr(exc, "status_code", None)
        return status is not None and status >= 500
    return False


def _extract_base64(result: Any) -> str:
    data = getattr(result, "data", None)
    if data and len(data) > 0:
        item = data[0]
        base64_data = getattr(item, "b64_json", None)
        if base64_data:
            return base64_data
    if hasattr(result, "model_dump"):
        payload = result.model_dump()
    else:
        payload = result
    try:
        return payload["data"][0]["b64_json"]
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("Image API response missing base64 data") from exc


class OpenAIImageClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.backoff = BackoffConfig()

    async def generate_image(
        self,
        *,
        model: str,
        prompt: str,
        size: str,
        quality: str,
        background: str,
    ) -> bytes:
        async def _call() -> bytes:
            result = await self.client.images.generate(
                model=model,
                prompt=prompt,
                size=size,
                quality=quality,
                background=background,
            )
            base64_data = _extract_base64(result)
            return base64.b64decode(base64_data)

        return await retry_async(_call, _is_retryable, self.backoff)


class OpenAIGrader:
    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.backoff = BackoffConfig()

    async def grade_image(
        self,
        *,
        model: str,
        rubric: list[str],
        prompt: str,
        slide_title: str,
        image_bytes: bytes,
    ) -> GradeResult:
        rubric_text = "\n".join(f"- {item}" for item in rubric)
        instructions = (
            "You are a strict visual grader. Evaluate the image against every rubric item. "
            "Return JSON only and follow the schema."
        )
        content = [
            {
                "type": "input_text",
                "text": (
                    "Slide title: "
                    f"{slide_title}\n\n"
                    "Prompt used: "
                    f"{prompt}\n\n"
                    "Rubric:\n"
                    f"{rubric_text}\n\n"
                    "Output a pass/fail plus specific failures and improvements."
                ),
            },
            {
                "type": "input_image",
                "image_url": f"data:image/png;base64,{base64.b64encode(image_bytes).decode('ascii')}",
            },
        ]

        async def _call() -> GradeResult:
            response = await self.client.responses.create(
                model=model,
                instructions=instructions,
                input=[{"role": "user", "content": content}],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "slide_grade",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "pass": {"type": "boolean"},
                                "score": {"type": "number"},
                                "failures": {"type": "array", "items": {"type": "string"}},
                                "improvements": {"type": "array", "items": {"type": "string"}},
                                "summary": {"type": "string"},
                            },
                            "required": ["pass", "score", "failures", "improvements", "summary"],
                            "additionalProperties": False,
                        },
                        "strict": True,
                    }
                },
                max_output_tokens=300,
            )
            try:
                payload = json.loads(response.output_text)
            except json.JSONDecodeError:
                text = response.output_text or ""
                start = text.find("{")
                end = text.rfind("}")
                if start != -1 and end != -1 and end > start:
                    try:
                        payload = json.loads(text[start : end + 1])
                    except json.JSONDecodeError as exc:
                        raise RetryableParseError("Failed to parse grader JSON") from exc
                else:
                    raise RetryableParseError("Grader output missing JSON object")
            return GradeResult(
                passed=payload["pass"],
                score=float(payload["score"]),
                failures=list(payload["failures"]),
                improvements=list(payload["improvements"]),
                summary=str(payload["summary"]),
            )

        return await retry_async(_call, _is_retryable, self.backoff)
