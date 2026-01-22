from __future__ import annotations

from pathlib import Path
from typing import Any

from .utils import ordered_slides, write_text


def build_report(run_root: Path, slides: list[dict[str, Any]]) -> Path:
    ordered = ordered_slides(slides)
    rows = []
    for slide in ordered:
        slide_id = slide.get("id")
        title = slide.get("title", slide_id)
        image_path = run_root / "final" / f"{slide_id}.png"
        if not image_path.exists():
            continue
        rows.append(
            f"<figure><img src=\"{image_path.relative_to(run_root)}\" alt=\"{title}\"/>"
            f"<figcaption><strong>{slide_id}</strong> - {title}</figcaption></figure>"
        )

    html = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>SlideMaker Report</title>
  <style>
    body { font-family: "Georgia", serif; margin: 24px; background: #f4f1ec; color: #222; }
    h1 { font-size: 28px; margin-bottom: 16px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 18px; }
    figure { margin: 0; background: #fff; border: 1px solid #ddd; padding: 12px; box-shadow: 0 8px 20px rgba(0,0,0,0.06); }
    img { width: 100%; height: auto; display: block; }
    figcaption { margin-top: 8px; font-size: 14px; }
  </style>
</head>
<body>
  <h1>SlideMaker Report</h1>
  <section class="grid">
    {rows}
  </section>
</body>
</html>
""".strip().format(rows="\n".join(rows))

    report_path = run_root / "report.html"
    write_text(report_path, html)
    return report_path
