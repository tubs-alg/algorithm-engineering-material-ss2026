"""
Generate section-title background symbol images for the T03 slide deck.

What this file contains
    A small driver around OpenAI's `images.generate` endpoint that turns each
    named prompt in `symbol_image_prompts.md` into a PNG in this directory.
    Non-goals: parsing prompts from the markdown file (prompts are inlined
    here so that re-running stays reproducible) and any post-processing.

Why it exists
    T01/L01/L04/T02 use OpenAI-generated symbolic photographs as low-opacity
    backgrounds for section-title slides. T03 should follow the same style.

How to use
    OPENAI_API_KEY is loaded from the repo `.env` via python-dotenv.

        uv run --with openai --with python-dotenv \
            week06-t03-lp-mip-modeling/slides/assets/gen_symbol_images.py
        # only some names, forced overwrite:
        uv run --with openai --with python-dotenv \
            week06-t03-lp-mip-modeling/slides/assets/gen_symbol_images.py \
            --only lpmip,bigm --overwrite

When it should change
    Add/remove an entry in `PROMPTS` when a section is added/removed, or edit
    a prompt and re-run with `--only <name> --overwrite` to regenerate one
    image. The shared cinematic style suffix lives in `STYLE_SUFFIX`.
"""
from __future__ import annotations

import argparse
import base64
import os
import sys
from pathlib import Path

STYLE_SUFFIX = (
    " Cinematic symbolic photograph, single hero object centered slightly "
    "off-axis, deep black background, warm amber/orange rim lighting with "
    "soft sparks and glow, photorealistic, dramatic shallow depth of field, "
    "16:9 aspect ratio, generous negative space around the subject for title "
    "overlay, moody and slightly metallic."
)

PROMPTS: dict[str, str] = {
    "lpmip": (
        "A heavy sheet of cream paper laid on a dark workbench, bearing a "
        "freshly hand-written linear program in fine amber ink — a "
        "left-aligned 'min c^T x', an indented 's.t. A x <= b', 'x >= 0', "
        "'x in Z^n' trailing off at the bottom — and beside it a polished "
        "brass straightedge, a draftsman's triangle, and a tiny glowing "
        "filament tube standing upright like a punctuation mark. Conveys "
        "the craft of writing linear and mixed-integer models by hand "
        "before the solver runs."
    ),
    "mathopt": (
        "A small brass speaking-tube mounted on a dark wooden panel, its "
        "bell aimed toward the viewer, an amber filament glowing softly "
        "inside the throat. A single neatly engraved label reads 'MathOpt'. "
        "Four thin brass cables fan out from the back of the mount into "
        "shadow, each terminating in a faintly lit nameplate — 'GLOP', "
        "'HIGHS', 'GUROBI', 'CP-SAT' — barely legible at the edge of the "
        "frame. Conveys one shared interface fanning out to many solver "
        "backends."
    ),
    "lp_preserving": (
        "A dark surface holding two cream cards side by side. The left card "
        "shows a hand-written 'max |x - y|' in fine amber ink, neatly "
        "crossed out with a single line. The right card shows a clean "
        "rewritten form — 't', with 't >= x - y', 't >= y - x' — glowing "
        "slightly brighter, as if endorsed. A brass-tipped fountain pen "
        "rests across both. Conveys reformulating a non-linear expression "
        "into a linear one without giving up LP structure."
    ),
    "bigm": (
        "A heavy brass cog stamped with an oversized capital 'M', mounted "
        "on a dark plinth and connected by a single taut amber wire to a "
        "small glowing indicator lamp labelled 'z'. Around the base of the "
        "plinth, fine sparks betray the strain — the wire is doing too "
        "much work. A small enamel warning plate at the corner reads "
        "'handle with care'. Conveys the Big-M trick: a single large "
        "constant that activates or disables a constraint, fragile under "
        "careless tuning."
    ),
    "logic": (
        "A small dark electrical-engineering desk holding three polished "
        "brass binary switches arranged in a row, each labelled with a "
        "tiny enamel plate 'y1', 'y2', 'y3'. Thin amber wires connect "
        "them through a single glowing gate-shaped junction in the "
        "middle, and a fourth wire leaves the gate as the result. One "
        "switch is up, the others down. Conveys assembling logical "
        "combinations of binary decision variables."
    ),
    "activation": (
        "A polished brass dimmer dial mounted on a dark control panel, "
        "its needle parked exactly at zero against a tick mark labelled "
        "'off'. A second tick mark, far to the right, reads 'L' and the "
        "arc between them is engraved with the word 'forbidden', softly "
        "shadowed. A small amber indicator lamp wired to the dial is "
        "dark. Conveys a variable that is either exactly zero or lives "
        "inside an allowed band, never in between."
    ),
    "pwla": (
        "A dark drafting board holding a single sheet of cream paper. On "
        "the paper, a smooth curving amber ink line of a non-linear "
        "function is overlaid by a sharp brass chain of four straight "
        "segments riveted together at glowing breakpoints, hugging the "
        "curve closely. A tiny pair of brass dividers rests on one of "
        "the breakpoints. Conveys approximating a smooth function with a "
        "linked chain of linear pieces."
    ),
    "strong_weak": (
        "A dark workbench holding two transparent glass display cubes "
        "side by side. Inside the left cube, a tight brass cage hugs a "
        "single small glowing amber sphere — the integer optimum — with "
        "almost no air around it. Inside the right cube, a much larger, "
        "slack brass cage contains the same sphere but with wide empty "
        "space, the bars loose and faintly bent outward. Tiny engraved "
        "plaques read 'tight' and 'loose'. Conveys two formulations of "
        "the same problem whose LP relaxations differ wildly in how "
        "tightly they enclose the integer optimum."
    ),
    "clockwork": (
        "An intricate exposed clockwork mechanism, brass gears "
        "interlocking in perfect order, a single jewelled escapement "
        "glowing amber at the center, faint motion blur on one rotating "
        "wheel. Conveys time, closure, and 'see you next time.'"
    ),
}


def _load_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        candidate = parent / ".env"
        if candidate.exists():
            load_dotenv(candidate)
            return
    load_dotenv()


def generate(name: str, prompt: str, out_path: Path, *, model: str, size: str) -> None:
    from openai import OpenAI

    client = OpenAI()
    full_prompt = prompt.strip() + "\n\n" + STYLE_SUFFIX.strip()
    print(f"[{name}] requesting…", flush=True)
    resp = client.images.generate(
        model=model,
        prompt=full_prompt,
        size=size,
        n=1,
    )
    b64 = resp.data[0].b64_json
    if not b64:
        raise RuntimeError(f"no b64 image returned for {name}")
    out_path.write_bytes(base64.b64decode(b64))
    print(f"[{name}] wrote {out_path}", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--only",
        default="",
        help="Comma-separated subset of names to generate (default: all).",
    )
    ap.add_argument(
        "--overwrite",
        action="store_true",
        help="Re-render even if the target PNG already exists.",
    )
    ap.add_argument(
        "--model",
        default="gpt-image-1",
        help="OpenAI image model (default: gpt-image-1).",
    )
    ap.add_argument(
        "--size",
        default="1536x1024",
        help="Image size, must be supported by the model (default: 1536x1024).",
    )
    args = ap.parse_args()

    _load_env()
    if not os.environ.get("OPENAI_API_KEY"):
        print("error: OPENAI_API_KEY not set (and no .env found)", file=sys.stderr)
        return 2

    out_dir = Path(__file__).resolve().parent
    selected = (
        [n.strip() for n in args.only.split(",") if n.strip()]
        if args.only
        else list(PROMPTS)
    )
    unknown = [n for n in selected if n not in PROMPTS]
    if unknown:
        print(f"error: unknown prompt names: {unknown}", file=sys.stderr)
        print(f"available: {list(PROMPTS)}", file=sys.stderr)
        return 2

    for name in selected:
        out_path = out_dir / f"symbol_{name}.png"
        if out_path.exists() and not args.overwrite:
            print(f"[{name}] exists, skipping (use --overwrite to redo)")
            continue
        generate(name, PROMPTS[name], out_path, model=args.model, size=args.size)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
