"""
Generate section-title background symbol images for the T06 slide deck.

What this file contains
    A small driver around OpenAI's `images.generate` endpoint that turns each
    named prompt in `PROMPTS` into a PNG in this directory. Mirrors the T05
    generator (`week09-t05-benchmarking-tuning/slides/assets/gen_symbol_images.py`).

Why it exists
    T01/L01/L04/T02/T03/T04/T05 use OpenAI-generated symbolic photographs as
    low-opacity backgrounds for section-title slides. T06 follows the same
    style. The six names below match the `background-image="assets/symbol_*.png"`
    references on the section-divider slides of this deck.

How to use
    OPENAI_API_KEY is loaded from the repo `.env` via python-dotenv.

        uv run --with openai --with python-dotenv \\
            week12-t06-tdd/slides/assets/gen_symbol_images.py
        # only some names, forced overwrite:
        uv run --with openai --with python-dotenv \\
            week12-t06-tdd/slides/assets/gen_symbol_images.py \\
            --only tdd,debugging --overwrite
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
    # _00-intro -> # Coding Patterns, TDD & Debugging
    "coding_patterns_tdd": (
        "A brass wax-seal stamp caught mid-press onto a rolled technical "
        "blueprint, the imprint glowing faint amber as it sets, the die face "
        "engraved with a tiny checkmark. Loose drafting instruments rest "
        "nearby in shadow. Conveys the difference between code that has been "
        "verified and code that merely runs."
    ),
    # _02-good-code-properties -> # What Good Optimization Code Looks Like
    "good_code": (
        "A cutaway brass instrument on a dark stand, its case opened to "
        "reveal several distinct internal gear layers stacked and meshing "
        "cleanly, each layer catching a thin rim of amber light, no wires "
        "crossing between layers. Conveys software built in clean, "
        "independently inspectable layers."
    ),
    # _03-coding-patterns -> # Coding Patterns
    "patterns": (
        "An open wooden case of interchangeable brass module blocks of "
        "varying shape resting in fitted velvet slots, one block lifted and "
        "glowing amber as it is fitted into a larger waiting mechanism on "
        "the bench. Conveys a toolbox of reusable structural patterns for "
        "building a model."
    ),
    # _04-testing-tdd -> # Test-Driven Optimization
    "tdd": (
        "A brass twin-lens signal lamp on a dark control panel, the left "
        "lens dark red and unlit, the right lens glowing warm amber-green as "
        "it just switched on, a small mechanical lever beside it caught "
        "mid-throw. Conveys the red-to-green rhythm of writing a failing "
        "test before making it pass."
    ),
    # _05-debugging-explainability -> # Debugging & Explaining Infeasibility
    "debugging": (
        "A brass magnifying loupe held over a dense tangle of interlocking "
        "gears on a dark bench, all gears dim except one small culprit gear "
        "isolated under the lens and glowing bright amber, jammed against its "
        "neighbor. Conveys isolating the one small part responsible for the "
        "whole mechanism failing."
    ),
    # _06-wrap-up -> # Wrap-up
    "wrapup": (
        "A brass wax-seal stamp resting beside its finished impression on a "
        "rolled blueprint, the seal now cooled to a steady warm amber glow, "
        "echoing the opening image but at rest, completed. Conveys the "
        "tutorial's arc closing on trustworthy, finished work."
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
