# slidemaker agent guide

This repo provides a CLI workflow for generating slide image sequences with GPT-image-1.5 and automated grading by GPT-5.1 vision. As an agent, you are responsible for shaping prompts/rubrics in `slides.json` before running generation.

## Workflow overview

1) Initialize a run
```
slidemaker init --topic "<topic>" --aspect-ratio "16:9"
```

2) Fill in `runs/<run_id>/intake.md`
- High-level presentation brief
- Stream-of-consciousness slide ideas

3) Build the outline
```
slidemaker outline --run <run_id>
```

4) Draft prompts + rubrics (template-based)
```
slidemaker draft --run <run_id>
```

5) Refine `runs/<run_id>/slides.json`
- Improve prompts and rubrics based on the intended narrative
- Ensure slide ordering is correct
- Keep visual style and constraints cohesive

6) Generate and grade
```
slidemaker generate --run <run_id> --concurrency 4 --max-attempts 8
```
Use `--max-attempts 0` to keep retrying until all slides pass.

7) Build the gallery
```
slidemaker report --run <run_id>
```

8) Export a full-bleed PDF
```
slidemaker export-pdf --run <run_id>
```
Omit `--run` to use the latest run directory.

## Tips for better results

- Be explicit about composition, layout, and placement if the concept depends on structure.
- Use a consistent visual style in every slide prompt (medium, palette, lighting, mood).
- Keep rubrics short and objective; each criterion should be visible in the image.
- If a slide fails repeatedly, tighten the prompt with specific changes and reduce ambiguity.

## Files to know

- `runs/<run_id>/spec.json` - presentation-level constraints (aspect ratio, style, audience)
- `runs/<run_id>/slides.json` - slide list with prompts/rubrics
- `runs/<run_id>/index.json` - attempt log and grading outcomes
- `runs/<run_id>/final/` - approved images for the deck
- `runs/<run_id>/exports/` - versioned PDF exports
- `runs/<run_id>/report.html` - static viewer
- `runs/<run_id>/critiques/` - saved critique logs and layout feedback

## Critique logging

When receiving large critiques or structural feedback, save them as Markdown under
`runs/<run_id>/critiques/` with a timestamped filename. Keep the full history.
