"""
Generate section-title background symbol images for the T05 slide deck.

What this file contains
    A small driver around OpenAI's `images.generate` endpoint that turns each
    named prompt in `PROMPTS` into a PNG in this directory. Mirrors the T03/T04
    generators (`week08-t04-real-world-problems/slides/assets/gen_symbol_images.py`).

Why it exists
    T01/L01/L04/T02/T03/T04 use OpenAI-generated symbolic photographs as
    low-opacity backgrounds for section-title slides. T05 follows the same style.
    The eight names below match the `background-image="assets/symbol_*.png"`
    references on the section-divider slides of this deck.

How to use
    OPENAI_API_KEY is loaded from the repo `.env` via python-dotenv.

        uv run --with openai --with python-dotenv \\
            week09-t05-benchmarking-tuning/slides/assets/gen_symbol_images.py
        # only some names, forced overwrite:
        uv run --with openai --with python-dotenv \\
            week09-t05-benchmarking-tuning/slides/assets/gen_symbol_images.py \\
            --only log,optuna --overwrite
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
    # _00-intro -> # Benchmarking & Parameter Tuning
    "benchmarking_tuning": (
        "A precise brass stopwatch resting on a dark workbench beside three "
        "small polished tuning dials, the stopwatch face glowing faintly amber "
        "and its single hand frozen mid-sweep. One dial is turned slightly and "
        "lit from within. Thin engraved tick marks ring both instruments. "
        "Conveys measuring whether a change is truly faster, and then tuning "
        "the machine to make it faster on purpose."
    ),
    # _01-benchmarking-pitfalls -> # Benchmarking is Hard
    "pitfalls": (
        "A heavy brass balance scale on a dark bench, its two pans holding two "
        "near-identical small brass blocks that look equal at a glance, the "
        "beam tipping almost imperceptibly toward one side. A faint amber glow "
        "under the lower pan hints the result could flip. A single loose weight "
        "lies just off the pan in shadow. Conveys how an apparent benchmarking "
        "win can be a measurement trap rather than a real improvement."
    ),
    # _02-benchmarking-visualization -> # The Plot Portfolio
    "plots": (
        "A dark drafting table with a sheet of fine amber graph paper, a single "
        "rising survival curve plotted in glowing amber ink climbing toward the "
        "right, small brass plotting pins marking data points along it. A brass "
        "French curve and a fine pen rest on the sheet. Conveys turning raw "
        "solver runs into the right plot that reveals which method actually wins."
    ),
    # _02b-study-design -> # Designing the Study
    "study": (
        "A dark wooden specimen cabinet with a shallow drawer pulled open, "
        "revealing a neat row of small labelled brass instance tokens of "
        "varying size set in velvet, one token lifted out and glowing amber "
        "under inspection. A brass magnifier and a tiny index card rest on the "
        "cabinet top. Conveys carefully selecting the set of benchmark "
        "instances a study will run on."
    ),
    # _03-reading-the-log -> # Reading the Solver Log
    "log": (
        "A vintage brass teletype machine on a dark desk feeding a long narrow "
        "paper tape that curls forward, a few monospaced lines of figures "
        "glowing faint amber where the light catches them. A brass loupe rests "
        "on the tape over one highlighted line. Conveys reading the solver's "
        "running log line by line to see what it actually did."
    ),
    # _04-tuning-search -> # From Guessing to Searching
    "tuning": (
        "A dark instrument panel with a row of polished brass adjustment knobs, "
        "most dim, one knob caught mid-turn and glowing bright amber as a fine "
        "needle gauge above it swings toward a peak. Faint engraved value marks "
        "ring each knob. Conveys moving from guessing parameter values by hand "
        "to searching for the setting that maximizes performance."
    ),
    # _05-optuna-tutorial -> # A Short Optuna Tutorial
    "optuna": (
        "A small self-operating brass apparatus on a dark bench: a slender "
        "mechanical arm tipped with a glowing amber stylus poised over a "
        "contoured brass response surface, having just selected the next point "
        "to probe, faint dotted trails marking earlier samples. A single "
        "jewelled bearing glows at the arm's pivot. Conveys an automated "
        "optimization framework choosing the next trial to evaluate."
    ),
    # _06-wrap-up -> # The Loop
    "wrapup": (
        "Three interlocking brass cogs of different sizes mounted on a dark "
        "panel forming one continuous loop, teeth precisely meshed, each cog "
        "bearing a tiny engraved label barely legible at the rim: 'MEASURE', "
        "'READ', 'TUNE'. A single jewelled bearing glows warm amber at the "
        "center and faint motion blur softens one rotating wheel. Conveys the "
        "three parts of the tutorial as one repeating cycle."
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
    ap.add_argument("--only", default="",
                    help="Comma-separated subset of names to generate (default: all).")
    ap.add_argument("--overwrite", action="store_true",
                    help="Re-render even if the target PNG already exists.")
    ap.add_argument("--model", default="gpt-image-1",
                    help="OpenAI image model (default: gpt-image-1).")
    ap.add_argument("--size", default="1536x1024",
                    help="Image size (default: 1536x1024).")
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
