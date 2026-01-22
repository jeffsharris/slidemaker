from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

from .pipeline import RunConfig, generate_all
from .prompting import build_prompt, build_rubric, slide_id
from .report import build_report
from .store import (
    ensure_run_dirs,
    load_slides,
    load_spec,
    run_dir,
    save_outline,
    save_slides,
    save_spec,
)
from .utils import chunk_lines, ensure_dir, read_text, size_from_aspect


def main() -> None:
    parser = argparse.ArgumentParser(prog="slidemaker")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a new run directory")
    init_parser.add_argument("--topic", required=True)
    init_parser.add_argument("--aspect-ratio", required=True)
    init_parser.add_argument("--run", help="Optional run id")

    outline_parser = subparsers.add_parser("outline", help="Create slides from intake notes")
    outline_parser.add_argument("--run", required=True)
    outline_parser.add_argument("--notes", help="Path to intake.md")

    draft_parser = subparsers.add_parser("draft", help="Draft prompts and rubrics")
    draft_parser.add_argument("--run", required=True)
    draft_parser.add_argument("--overwrite", action="store_true")

    generate_parser = subparsers.add_parser("generate", help="Generate and grade slides")
    generate_parser.add_argument("--run", required=True)
    generate_parser.add_argument("--concurrency", type=int, default=4)
    generate_parser.add_argument("--max-attempts", type=int, default=8)
    generate_parser.add_argument("--image-model", default="gpt-image-1.5")
    generate_parser.add_argument("--grader-model", default="gpt-5.1")
    generate_parser.add_argument("--quality", default="auto", choices=["auto", "low", "medium", "high"])
    generate_parser.add_argument("--background", default="opaque", choices=["opaque", "transparent", "auto"])

    report_parser = subparsers.add_parser("report", help="Generate HTML report")
    report_parser.add_argument("--run", required=True)

    args = parser.parse_args()
    base_dir = Path.cwd()

    if args.command == "init":
        run_id = args.run or _default_run_id(args.topic)
        paths = ensure_run_dirs(base_dir, run_id)
        spec = {
            "topic": args.topic,
            "aspect_ratio": args.aspect_ratio,
            "image_size": size_from_aspect(args.aspect_ratio),
            "audience": "",
            "tone": "",
            "visual_style": "",
            "color_palette": "",
            "constraints": [],
            "allow_text": False,
        }
        save_spec(paths["root"], spec)

        intake_path = paths["root"] / "intake.md"
        if not intake_path.exists():
            intake_template = _intake_template(spec)
            intake_path.write_text(intake_template, encoding="utf-8")

        slides = {"spec": spec, "slides": []}
        save_slides(paths["root"], slides)
        print(f"Run created: {paths['root']}")
        return

    if args.command == "outline":
        run_root = run_dir(base_dir, args.run)
        notes_path = Path(args.notes) if args.notes else run_root / "intake.md"
        if not notes_path.exists():
            raise SystemExit(f"Missing intake notes: {notes_path}")
        outline = build_outline(read_text(notes_path))
        save_outline(run_root, outline)

        slides = load_slides(run_root)
        slides["spec"] = load_spec(run_root)
        slides["slides"] = outline["slides"]
        save_slides(run_root, slides)
        print(f"Outline created with {len(outline['slides'])} slides")
        return

    if args.command == "draft":
        run_root = run_dir(base_dir, args.run)
        slides = load_slides(run_root)
        spec = load_spec(run_root)
        updated = 0
        for slide in slides.get("slides", []):
            if args.overwrite or not slide.get("prompt"):
                slide["prompt"] = build_prompt(spec, slide)
            if args.overwrite or not slide.get("rubric"):
                slide["rubric"] = build_rubric(spec, slide)
            updated += 1
        slides["spec"] = spec
        save_slides(run_root, slides)
        print(f"Drafted prompts/rubrics for {updated} slides")
        return

    if args.command == "generate":
        run_root = run_dir(base_dir, args.run)
        config = RunConfig(
            run_root=run_root,
            image_model=args.image_model,
            grader_model=args.grader_model,
            image_quality=args.quality,
            image_background=args.background,
            max_attempts=args.max_attempts,
            concurrency=args.concurrency,
        )
        ensure_dir(run_root)
        ensure_dir(run_root / "attempts")
        ensure_dir(run_root / "final")
        import asyncio

        asyncio.run(generate_all(config))
        print("Generation complete")
        return

    if args.command == "report":
        run_root = run_dir(base_dir, args.run)
        slides = load_slides(run_root).get("slides", [])
        report_path = build_report(run_root, slides)
        print(f"Report written to {report_path}")
        return


def _default_run_id(topic: str) -> str:
    timestamp = dt.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_{_slug(topic)}"


def _slug(text: str) -> str:
    return "_".join("".join(ch for ch in part if ch.isalnum()).lower() for part in text.split())


def _intake_template(spec: dict[str, str]) -> str:
    return (
        "# Intake\n\n"
        f"Topic: {spec.get('topic', '')}\n"
        f"Aspect ratio: {spec.get('aspect_ratio', '')}\n\n"
        "## High-level brief\n"
        "Write a concise description of the presentation intent and arc.\n\n"
        "## Stream of consciousness\n"
        "List slide ideas or rough sequence notes.\n"
        "- Slide idea 1\n"
        "- Slide idea 2\n"
    )


def build_outline(intake_text: str) -> dict[str, list[dict[str, str]]]:
    lines = intake_text.splitlines()
    bullets = [line.lstrip("- ") for line in lines if line.strip().startswith("-")]
    if not bullets:
        bullets = chunk_lines(lines)
    slides = []
    for idx, bullet in enumerate(bullets, start=1):
        title = bullet.strip()
        slide = {
            "id": slide_id(idx, title),
            "title": title,
            "intent": title,
            "notes": "",
            "prompt": "",
            "rubric": [],
            "image_size": "",
            "status": "pending",
        }
        slides.append(slide)
    return {"slides": slides}


if __name__ == "__main__":
    main()
