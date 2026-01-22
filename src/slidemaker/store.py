from __future__ import annotations

from pathlib import Path
from typing import Any

from .utils import ensure_dir, load_json, save_json


RUNS_DIR_NAME = "runs"


def runs_root(base_dir: Path) -> Path:
    return base_dir / RUNS_DIR_NAME


def run_dir(base_dir: Path, run_id: str) -> Path:
    return runs_root(base_dir) / run_id


def latest_run_id(base_dir: Path) -> str:
    root = runs_root(base_dir)
    if not root.exists():
        raise SystemExit("No runs directory found")
    candidates = [path for path in root.iterdir() if path.is_dir()]
    if not candidates:
        raise SystemExit("No runs available")
    latest = max(candidates, key=lambda path: path.stat().st_mtime)
    return latest.name


def ensure_run_dirs(base_dir: Path, run_id: str) -> dict[str, Path]:
    root = run_dir(base_dir, run_id)
    attempts = root / "attempts"
    final = root / "final"
    ensure_dir(root)
    ensure_dir(attempts)
    ensure_dir(final)
    return {"root": root, "attempts": attempts, "final": final}


def load_spec(run_root: Path) -> dict[str, Any]:
    return load_json(run_root / "spec.json", {})


def save_spec(run_root: Path, spec: dict[str, Any]) -> None:
    save_json(run_root / "spec.json", spec)


def load_slides(run_root: Path) -> dict[str, Any]:
    return load_json(run_root / "slides.json", {"slides": []})


def save_slides(run_root: Path, slides: dict[str, Any]) -> None:
    save_json(run_root / "slides.json", slides)


def load_index(run_root: Path) -> dict[str, Any]:
    return load_json(run_root / "index.json", {"slides": {}})


def save_index(run_root: Path, index: dict[str, Any]) -> None:
    save_json(run_root / "index.json", index)


def load_outline(run_root: Path) -> dict[str, Any]:
    return load_json(run_root / "outline.json", {"slides": []})


def save_outline(run_root: Path, outline: dict[str, Any]) -> None:
    save_json(run_root / "outline.json", outline)
