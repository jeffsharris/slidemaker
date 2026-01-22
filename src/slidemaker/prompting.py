from __future__ import annotations

from typing import Any

from .utils import slugify


def _spec_line(spec: dict[str, Any], key: str, label: str) -> str | None:
    value = spec.get(key)
    if not value:
        return None
    if isinstance(value, list):
        value = ", ".join(str(item) for item in value if item)
    return f"{label}: {value}"


def build_prompt(spec: dict[str, Any], slide: dict[str, Any]) -> str:
    parts: list[str] = []
    topic = spec.get("topic")
    if topic:
        parts.append(f"Presentation topic: {topic}.")

    title = slide.get("title")
    if title:
        parts.append(f"Slide title concept: {title}.")

    intent = slide.get("intent") or slide.get("notes")
    if intent:
        parts.append(f"Core idea: {intent}.")

    style_bits = []
    for key, label in (
        ("visual_style", "Visual style"),
        ("color_palette", "Color palette"),
        ("tone", "Tone"),
        ("audience", "Audience"),
    ):
        line = _spec_line(spec, key, label)
        if line:
            style_bits.append(line)
    if style_bits:
        parts.append("Style notes: " + " | ".join(style_bits) + ".")

    constraints = spec.get("constraints") or []
    allow_text = spec.get("allow_text")
    if allow_text is False:
        constraints = list(constraints) + ["No text or lettering in the image"]
    if constraints:
        parts.append("Constraints: " + "; ".join(str(c) for c in constraints) + ".")

    aspect = spec.get("aspect_ratio")
    if aspect:
        parts.append(f"Composition: designed for a {aspect} slide layout.")

    parts.append("Render as a single, cohesive visual with a clean focal point.")
    return " ".join(parts)


def build_rubric(spec: dict[str, Any], slide: dict[str, Any]) -> list[str]:
    rubric: list[str] = []
    intent = slide.get("intent") or slide.get("notes") or slide.get("title")
    if intent:
        rubric.append(f"The image clearly communicates: {intent}.")
    topic = spec.get("topic")
    if topic:
        rubric.append(f"The visual feels consistent with the presentation topic: {topic}.")

    visual_style = spec.get("visual_style")
    if visual_style:
        rubric.append(f"The style matches: {visual_style}.")

    allow_text = spec.get("allow_text")
    if allow_text is False:
        rubric.append("No visible text, labels, or lettering.")

    aspect = spec.get("aspect_ratio")
    if aspect:
        rubric.append(f"Composition fits a {aspect} slide without awkward cropping.")

    rubric.append("The composition is focused and avoids unrelated or distracting elements.")
    return rubric


def refine_prompt(base_prompt: str, improvements: list[str]) -> str:
    if not improvements:
        return base_prompt
    improvements_text = "; ".join(improvements)
    return f"{base_prompt} Refinements: {improvements_text}."


def slide_id(index: int, title: str) -> str:
    slug = slugify(title)
    return f"{index:02d}_{slug}"
