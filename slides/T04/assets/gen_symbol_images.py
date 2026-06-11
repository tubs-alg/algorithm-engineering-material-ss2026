"""
Generate section-title background symbol images for the T04 slide deck.

What this file contains
    A small driver around OpenAI's `images.generate` endpoint that turns each
    named prompt in `PROMPTS` into a PNG in this directory. Mirrors the T03
    generator (`week06-t03-lp-mip-modeling/slides/assets/gen_symbol_images.py`).

Why it exists
    T01/L01/L04/T02/T03 use OpenAI-generated symbolic photographs as low-opacity
    backgrounds for section-title slides. T04 should follow the same style.

How to use
    OPENAI_API_KEY is loaded from the repo `.env` via python-dotenv.

        uv run --with openai --with python-dotenv \\
            week08-t04-real-world-problems/slides/assets/gen_symbol_images.py
        # only some names, forced overwrite:
        uv run --with openai --with python-dotenv \\
            week08-t04-real-world-problems/slides/assets/gen_symbol_images.py \\
            --only assembly_line,logistics --overwrite
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
    "real_world": (
        "A heavy brass switchboard mounted on a dark workbench, three large "
        "polished dials side by side, each engraved with a tiny enamel label: "
        "'SHOP', 'ROSTER', 'ROUTES'. Each dial glows from within with a warm "
        "amber filament, all three currently lit. Faint coils of wire trail "
        "off the back of the panel into shadow. Conveys three different "
        "real-world combinatorial problems sharing one underlying control room."
    ),
    "assembly_line": (
        "A long dark factory bench seen at a low angle, three polished brass "
        "machine stations spaced along it like punctuation marks, each with a "
        "tiny amber pilot lamp. A single workpiece — a small precise brass "
        "block — sits on the second station mid-process, glowing faintly at "
        "its tooled edge. Thin guide rails connect the stations. Conveys jobs "
        "flowing across machines in a fixed routing through a job shop."
    ),
    "shift_planning": (
        "A tall dark wall-mounted board with a hand-drawn weekly grid in fine "
        "amber ink — seven columns headed Mon through Sun, three rows of "
        "shifts labelled 'EARLY', 'LATE', 'NIGHT'. Small polished brass tiles "
        "are slotted into a few of the cells; one tile glows faintly. A worn "
        "leather glove and a brass schedule punch rest on the small shelf "
        "below the board. Conveys assigning people to shifts over a rolling "
        "horizon."
    ),
    "logistics": (
        "A worn cream map laid across a dark drafting table, a polished brass "
        "compass pinned at one corner marking the depot, and a single amber "
        "ink line tracing a closed loop through six small brass map-pins set "
        "as stops on the route. The route line glows faintly at its current "
        "leg. A folded delivery manifest and a small brass odometer dial sit "
        "at the edge of the frame. Conveys planning a vehicle route that "
        "starts and ends at the depot and serves a set of clients."
    ),
    "gear": (
        "Three interlocking brass cogs of different sizes mounted on a dark "
        "panel, meshing teeth precisely aligned, a single jewelled bearing "
        "glowing amber at the center of the largest. Each cog bears a tiny "
        "engraved label barely legible at the rim: 'MODEL', 'SOLVE', 'SHIP'. "
        "Faint motion blur on one rotating wheel. Conveys a shared engineering "
        "workflow turning across three different problem families."
    ),
    "blueprint": (
        "A large rolled blueprint partly unfurled across a dark drafting "
        "table, its cyan-amber drawing lines depicting a stylised composite "
        "of a machine schedule, a roster grid, and a delivery route — three "
        "small motifs woven into one plan. A brass T-square, a pair of "
        "dividers, and a small amber lantern rest on the unrolled portion. "
        "Conveys the closing of a chapter and the plan moving forward to the "
        "next."
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
