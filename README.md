# slidemaker

Generate a sequence of slide images using GPT-image-1.5, then automatically grade each image with GPT-5.1 against a slide-specific rubric until it passes. The tool stores every attempt for traceability and outputs a simple HTML gallery for review.

## Requirements

- Python 3.10+
- `OPENAI_API_KEY` set in your shell

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Quick start

```bash
# 1) Initialize a run
slidemaker init --topic "Your topic" --aspect-ratio "16:9"

# 2) Fill in the intake notes
# Edit runs/<run_id>/intake.md with the brief + stream of consciousness.

# 3) Create an outline from the notes
slidemaker outline --run <run_id>

# 4) Draft prompts + rubrics (deterministic template)
slidemaker draft --run <run_id>

# 5) Review/edit slides.json to improve prompts/rubrics if needed
# (This is where a coding agent can refine content.)

# 6) Generate and grade images until each slide passes
slidemaker generate --run <run_id> --concurrency 4 --max-attempts 8

# 7) Build a simple HTML gallery
slidemaker report --run <run_id>
```

## How it works

- **Spec & intake**: `init` creates a run directory with `spec.json` and an `intake.md` template.
- **Outline**: `outline` parses the stream-of-consciousness into slide stubs in `slides.json`.
- **Draft prompts**: `draft` fills in prompts/rubrics using deterministic templates based on the spec + slide notes.
- **Generation**: `generate` calls GPT-image-1.5 to produce images and GPT-5.1 to grade them against the rubric.
- **Traceability**: All attempts are stored under `attempts/`, with `index.json` tracking prompts, failures, and final selections.
- **Output**: Final images are copied to `final/` and a `report.html` gallery is generated for viewing.

## Run directory structure

```
runs/
  <run_id>/
    spec.json
    intake.md
    outline.json
    slides.json
    index.json
    attempts/
      01_topic/
        attempt_001.png
        attempt_001.json
    final/
      01_topic.png
    report.html
```

## Defaults and sizing

GPT-image-1.5 supports these sizes: `1024x1024`, `1536x1024` (landscape), `1024x1536` (portrait), or `auto`.

The tool maps aspect ratios to a supported size:

- `16:9` or other landscape -> `1536x1024`
- `4:3` or square -> `1024x1024`
- `3:4` or portrait -> `1024x1536`

Override per-run or per-slide by setting `image_size` in `spec.json` or `slides.json`.

## Notes

- Prompt/rubric generation is local and deterministic (no model call). You can edit `slides.json` to improve them.
- Set `--max-attempts 0` to keep retrying until every slide passes.
- The grading loop uses GPT-5.1 vision to decide pass/fail and recommend prompt refinements.
