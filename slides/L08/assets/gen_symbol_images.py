"""
Generate section-title background symbol images for the L08 slide deck.

Driver around OpenAI's `images.generate` endpoint that turns each named prompt
in `symbol_image_prompts.md` into a PNG in this directory. Prompts are inlined
below so re-runs stay reproducible without re-parsing the markdown.

Usage:
    uv run --with openai --with python-dotenv \
        week07-l08-graph-algorithms/slides/assets/gen_symbol_images.py
    # only some names, force overwrite:
    uv run --with openai --with python-dotenv \
        week07-l08-graph-algorithms/slides/assets/gen_symbol_images.py \
        --only flow,matching --overwrite

OPENAI_API_KEY is loaded from the nearest `.env` via python-dotenv. Adapted
from week06-t03-lp-mip-modeling/slides/assets/gen_symbol_images.py.
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
    "l08": (
        "A dark workbench holding a constellation of small polished brass "
        "spheres connected by taut amber filaments into an irregular network "
        "- a few nodes are larger and faintly glowing as hubs, others are "
        "smaller and connected by only one or two strands. A magnifier with "
        "a brass rim rests at the edge of the frame, hinting at inspection. "
        "Conveys 'graphs and networks' as the lecture theme: nodes joined "
        "by edges, structure waiting to be analyzed."
    ),
    "graphs": (
        "A dark surface holding a single open leather-bound notebook. On the "
        "visible page, an elegant amber-ink diagram shows a small graph: "
        "four nodes joined by weighted edges, with hand-written labels - "
        "'V', 'E', 'w(u,v)' - in the margin. A brass-tipped fountain pen "
        "rests across the gutter, and a tiny glowing filament lamp sits "
        "behind the notebook as a soft halo. Conveys the formal vocabulary "
        "of graphs: vertices, edges, and weights."
    ),
    "shortest_path": (
        "A dark map laid flat on a workbench, faintly engraved with a "
        "network of roads. A continuous taut amber thread runs from a brass "
        "pin labelled 's' to another brass pin labelled 't', following the "
        "shortest path through a few glowing junctions. Two or three "
        "alternative routes are visible as faint dim threads in the "
        "background, clearly longer. A small brass compass rests at the "
        "corner. Conveys finding the minimum-cost route between two "
        "specific endpoints."
    ),
    "matching": (
        "A dark velvet-lined display tray holding four polished brass keys "
        "on the left and four matching brass locks on the right, each pair "
        "linked by a single taut amber filament glowing softly. The "
        "filaments do not cross; every key is paired with exactly one lock. "
        "One key at the edge remains unpaired, its filament dim. Conveys "
        "pairing up items from two sides such that each is matched at most "
        "once."
    ),
    "flow": (
        "A dark industrial scene with a heavy brass pipe junction at the "
        "centre, fed by a single thicker amber-glowing inlet on the left "
        "and branching into three thinner outlet pipes on the right of "
        "varying diameters. A faint glowing fluid is visible inside the "
        "pipes, fuller in the wider outlets, tapering in the narrowest. A "
        "small brass pressure gauge mounted on the central junction reads "
        "partway up its dial. Conveys pushing as much flow as the pipes "
        "allow from a source through a capacitated network."
    ),
    "mst": (
        "A dark workbench holding a constellation of small polished brass "
        "beads scattered like cities on a map, joined by a minimal skeleton "
        "of taut amber filaments - exactly enough threads to connect every "
        "bead, no closed loops anywhere. A pair of fine brass tweezers "
        "rests at the edge, as if the skeleton had just been assembled "
        "bead-by-bead. A few unused, slack filaments lie cut off to the "
        "side. Conveys connecting all nodes with the cheapest possible "
        "loop-free set of edges."
    ),
    "crates": (
        "A dark warehouse loading dock at night, four stacks of weathered "
        "wooden shipping crates arranged at different positions, some stacks "
        "tall and some short - hinting at surpluses and shortages. A heavy "
        "brass-trimmed delivery truck with its rear shutter half-open sits "
        "between two of the stacks, a single crate caught mid-transfer on a "
        "hand truck, glowing faintly amber. Faint amber route lines hover "
        "between the stacks like ghost trajectories. Conveys moving "
        "reusable containers between depots under limited truck capacity."
    ),
    "clockwork": (
        "An intricate exposed clockwork mechanism, brass gears interlocking "
        "in perfect order, a single jewelled escapement glowing amber at "
        "the center, faint motion blur on one rotating wheel. Conveys "
        "time, closure, and 'see you next time.'"
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
