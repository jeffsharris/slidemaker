from __future__ import annotations

import datetime as dt
from pathlib import Path

import img2pdf

from .store import load_slides
from .utils import ensure_dir, ordered_slides


def export_pdf(run_root: Path, output_path: Path | None = None) -> Path:
    slides = load_slides(run_root).get("slides", [])
    ordered = ordered_slides(slides)
    final_dir = run_root / "final"

    image_paths: list[Path] = []
    missing: list[str] = []
    for slide in ordered:
        slide_id = slide.get("id", "")
        if not slide_id:
            continue
        image_path = final_dir / f"{slide_id}.png"
        if image_path.exists():
            image_paths.append(image_path)
        else:
            missing.append(slide_id)

    if missing:
        missing_list = ", ".join(missing)
        raise SystemExit(f"Missing final images for: {missing_list}")
    if not image_paths:
        raise SystemExit("No final images found to export")

    if output_path is None:
        timestamp = dt.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_dir = run_root / "exports"
        ensure_dir(output_dir)
        output_path = output_dir / f"slides_{timestamp}.pdf"
    else:
        ensure_dir(output_path.parent)

    pdf_bytes = img2pdf.convert([str(path) for path in image_paths])
    output_path.write_bytes(pdf_bytes)
    return output_path
