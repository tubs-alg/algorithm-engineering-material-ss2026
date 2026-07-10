"""
Generate section-title background symbol images for the L13 slide deck.

What this file contains
    A small driver around OpenAI's `images.generate` endpoint that turns each
    named prompt in `PROMPTS` into a PNG in this directory. Mirrors the T05
    generator (`week09-t05-benchmarking-tuning/slides/assets/gen_symbol_images.py`).

Why it exists
    The course decks use AI-generated symbolic photographs as low-opacity
    backgrounds for section-divider slides. L13 follows the same style. The
    names below match the `background-image="assets/symbol_*.png"` references
    on the section-divider slides of this deck.

How to use
    OPENAI_API_KEY is loaded from the repo `.env` via python-dotenv.

        uv run --with openai --with python-dotenv \\
            week12-l13-robust-multi-objective/slides/assets/gen_symbol_images.py
        # only some names, forced overwrite:
        uv run --with openai --with python-dotenv \\
            week12-l13-robust-multi-objective/slides/assets/gen_symbol_images.py \\
            --only robust,stochastic --overwrite
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
    # _00-intro -> # Beyond min f(x)
    "standard_model": (
        "A pristine brass plaque engraved with a single short formula, mounted "
        "on a dark laboratory wall, but the plaque is slightly cracked down one "
        "corner and a faint amber light leaks through the crack. A small brass "
        "caliper hangs beneath it. Conveys an elegant standard model that no "
        "longer quite contains reality."
    ),
    # _01-what-is-better -> # Part I: Multiple Objectives
    "conflicting_objectives": (
        "An intricate brass balance apparatus with three small pans suspended "
        "at different heights, each pan holding a different token: a tiny "
        "clock, a gear, and a coin. The beams tilt in conflicting directions, "
        "no configuration level. Warm amber glow catches the pan that hangs "
        "lowest. Conveys several objectives that cannot all be satisfied at "
        "once."
    ),
    # _02-one-solution -> # One Solution
    "preferences": (
        "A row of graduated brass calibration weights on a dark velvet-lined "
        "tray, one weight lifted and held mid-air by a fine mechanical clamp "
        "above a scale pan, glowing softly amber. Engraved numerals on each "
        "weight are barely legible. Conveys deliberately choosing how much "
        "each concern counts before committing to a single answer."
    ),
    # _03-many-solutions -> # Many Solutions
    "alternatives": (
        "A dark gallery shelf holding a curved row of small polished brass "
        "mechanisms, each a slightly different variant of the same machine, "
        "arranged along a gentle arc from tall and narrow to short and wide. "
        "One mid-row variant glows warm amber under a spotlight. Conveys a "
        "frontier of alternative trade-off solutions presented for a human to "
        "choose from."
    ),
    # _04-fragile-forecasts -> # Part II: The World Is Uncertain
    "uncertain_world": (
        "A tall stack of freshly printed newspapers tied with twine on a dark "
        "loading dock at dawn, faint amber street light raking across the top "
        "sheet, the headline out of focus. A small brass counting tally lies "
        "on top of the stack. Conveys committing to a quantity before knowing "
        "the demand the day will bring."
    ),
    # _05-diagnosis -> # Diagnose the Uncertainty
    "diagnosis": (
        "A brass magnifying loupe resting on a dark technical blueprint of a "
        "long pipeline of connected chambers, one chamber circled in glowing "
        "amber grease pencil, a fine fracture visible only under the loupe. "
        "Conveys locating exactly where a system disagrees with reality "
        "before prescribing a fix."
    ),
    # _06-robust -> # Robust Optimization
    "robust": (
        "A compact brass mechanism enclosed in a heavy protective cage of "
        "riveted metal bands, standing on a dark bench while small metal "
        "shards and sparks glance off the cage without reaching the mechanism "
        "inside, which glows calm amber. Conveys a decision protected against "
        "every plausible blow within its armor's rating."
    ),
    # _07-stochastic -> # Stochastic Optimization
    "stochastic": (
        "A tall brass Galton board on a dark bench, small polished spheres "
        "cascading through the pin lattice mid-fall with slight motion blur, "
        "collecting into softly amber-lit bins that form a bell-shaped heap. "
        "One sphere catches the light mid-bounce. Conveys decisions evaluated "
        "across a whole distribution of outcomes rather than one path."
    ),
    # _08-synthesis -> # Choosing a Posture
    "synthesis": (
        "An antique brass signpost on a dark plain with four engraved "
        "pointing arms aimed in different directions, each arm bearing a "
        "small distinct emblem: a single dot, a shield, a pair of dice, and a "
        "circular arrow. The nearest arm glows warm amber. Conveys choosing "
        "deliberately among distinct postures toward an uncertain future."
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
