from __future__ import annotations

import asyncio
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .openai_client import OpenAIGrader, OpenAIImageClient
from .prompting import build_prompt, refine_prompt
from .store import load_index, load_slides, load_spec, save_index, save_slides
from .utils import ensure_dir, ordered_slides, save_json


@dataclass
class RunConfig:
    run_root: Path
    image_model: str
    grader_model: str
    image_quality: str
    image_background: str
    max_attempts: int
    concurrency: int


class RunState:
    def __init__(self, run_root: Path) -> None:
        self.run_root = run_root
        self.slides = load_slides(run_root)
        self.spec = load_spec(run_root)
        self.index = load_index(run_root)
        self.lock = asyncio.Lock()

    async def save(self) -> None:
        async with self.lock:
            save_slides(self.run_root, self.slides)
            save_index(self.run_root, self.index)


async def generate_all(config: RunConfig) -> None:
    state = RunState(config.run_root)
    slides = ordered_slides(state.slides.get("slides", []))
    if not slides:
        raise RuntimeError("No slides found. Run 'outline' and 'draft' first.")

    image_client = OpenAIImageClient()
    grader = OpenAIGrader()
    semaphore = asyncio.Semaphore(config.concurrency)

    tasks = [
        asyncio.create_task(
            _process_slide(
                config=config,
                state=state,
                slide=slide,
                image_client=image_client,
                grader=grader,
                semaphore=semaphore,
            )
        )
        for slide in slides
    ]
    await asyncio.gather(*tasks)


async def _process_slide(
    *,
    config: RunConfig,
    state: RunState,
    slide: dict[str, Any],
    image_client: OpenAIImageClient,
    grader: OpenAIGrader,
    semaphore: asyncio.Semaphore,
) -> None:
    slide_id = slide["id"]
    attempt_dir = config.run_root / "attempts" / slide_id
    ensure_dir(attempt_dir)

    index_entry = state.index.setdefault("slides", {}).setdefault(
        slide_id,
        {
            "title": slide.get("title"),
            "final_image": None,
            "attempts": [],
        },
    )

    final_path = config.run_root / "final" / f"{slide_id}.png"
    if slide.get("status") == "approved" and final_path.exists():
        index_entry["final_image"] = str(final_path.relative_to(config.run_root))
        return

    base_prompt = slide.get("prompt") or build_prompt(state.spec, slide)
    rubric = slide.get("rubric") or []
    if not rubric:
        raise RuntimeError(f"Slide {slide_id} is missing a rubric.")

    attempt = 0
    current_prompt = base_prompt
    while True:
        attempt += 1
        if config.max_attempts > 0 and attempt > config.max_attempts:
            raise RuntimeError(f"Slide {slide_id} exceeded max attempts ({config.max_attempts}).")

        attempt_name = f"attempt_{attempt:03d}"
        image_path = attempt_dir / f"{attempt_name}.png"
        metadata_path = attempt_dir / f"{attempt_name}.json"

        async with semaphore:
            image_bytes = await image_client.generate_image(
                model=config.image_model,
                prompt=current_prompt,
                size=slide.get("image_size") or state.spec.get("image_size", "1536x1024"),
                quality=config.image_quality,
                background=config.image_background,
            )

        image_path.write_bytes(image_bytes)

        async with semaphore:
            grade = await grader.grade_image(
                model=config.grader_model,
                rubric=rubric,
                prompt=current_prompt,
                slide_title=slide.get("title", slide_id),
                image_bytes=image_bytes,
            )

        metadata = {
            "prompt": current_prompt,
            "rubric": rubric,
            "grade": {
                "pass": grade.passed,
                "score": grade.score,
                "failures": grade.failures,
                "improvements": grade.improvements,
                "summary": grade.summary,
            },
        }
        save_json(metadata_path, metadata)

        index_entry["attempts"].append(
            {
                "file": str(image_path.relative_to(config.run_root)),
                "metadata": str(metadata_path.relative_to(config.run_root)),
                "pass": grade.passed,
                "score": grade.score,
                "failures": grade.failures,
                "summary": grade.summary,
            }
        )

        if grade.passed:
            final_path = config.run_root / "final" / f"{slide_id}.png"
            shutil.copyfile(image_path, final_path)
            index_entry["final_image"] = str(final_path.relative_to(config.run_root))
            slide["status"] = "approved"
            await state.save()
            return

        slide["status"] = "retrying"
        improvements = grade.improvements or grade.failures
        current_prompt = refine_prompt(base_prompt, improvements)
        await state.save()
