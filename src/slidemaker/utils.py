from __future__ import annotations

import json
import os
import re
import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable


SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(text: str, max_len: int = 40) -> str:
    value = text.strip().lower()
    value = SLUG_RE.sub("_", value).strip("_")
    if not value:
        value = "slide"
    return value[:max_len]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True), encoding="utf-8")


@dataclass
class BackoffConfig:
    base_delay: float = 1.0
    max_delay: float = 30.0
    max_retries: int = 6


def next_delay(attempt: int, base_delay: float, max_delay: float) -> float:
    delay = base_delay * (2 ** attempt)
    return min(delay, max_delay)


async def retry_async(
    func: Callable[[], Any],
    is_retryable: Callable[[Exception], bool],
    config: BackoffConfig,
) -> Any:
    last_err: Exception | None = None
    for attempt in range(config.max_retries + 1):
        try:
            return await func()
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            if attempt >= config.max_retries or not is_retryable(exc):
                raise
            delay = next_delay(attempt, config.base_delay, config.max_delay)
            await asyncio.sleep(delay)
    if last_err:
        raise last_err
    raise RuntimeError("retry_async failed without exception")


def normalize_aspect_ratio(value: str) -> str:
    return value.strip().lower().replace(" ", "")


def size_from_aspect(aspect_ratio: str) -> str:
    ratio = normalize_aspect_ratio(aspect_ratio)
    if ratio in {"16:9", "16x9", "widescreen", "landscape"}:
        return "1536x1024"
    if ratio in {"4:3", "4x3", "square"}:
        return "1024x1024"
    if ratio in {"3:4", "3x4", "portrait", "tall"}:
        return "1024x1536"
    return "1536x1024"


def ordered_slides(slides: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def slide_key(slide: dict[str, Any]) -> tuple[int, str]:
        raw = slide.get("id", "")
        prefix = raw.split("_")[0]
        try:
            return (int(prefix), raw)
        except ValueError:
            return (9999, raw)

    return sorted(slides, key=slide_key)


def chunk_lines(lines: Iterable[str]) -> list[str]:
    chunks: list[str] = []
    buffer: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if buffer:
                chunks.append(" ".join(buffer).strip())
                buffer = []
            continue
        buffer.append(stripped)
    if buffer:
        chunks.append(" ".join(buffer).strip())
    return chunks
