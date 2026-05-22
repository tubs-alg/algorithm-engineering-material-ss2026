# T03 Section Background Symbol Prompts

Prompts for generating section-title background images in the L01/T01/L04/T02
style. Images are used at ~30% opacity over `#2d4059`, so keep contrast high
and the subject readable even when dimmed.

Shared style suffix (appended to every prompt by the generator):

> Cinematic symbolic photograph, single hero object centered slightly off-axis,
> deep black background, warm amber/orange rim lighting with soft sparks and
> glow, photorealistic, dramatic shallow depth of field, 16:9 aspect ratio,
> generous negative space around the subject for title overlay, moody and
> slightly metallic.

---

## symbol_lpmip.png  *(Welcome / overall T03 cover)*

A heavy sheet of cream paper laid on a dark workbench, bearing a freshly hand-
written linear program in fine amber ink — a left-aligned `min c^T x`, an
indented `s.t. A x ≤ b`, `x ≥ 0`, `x ∈ Z^n` trailing off at the bottom — and
beside it a polished brass straightedge, a draftsman's triangle, and a tiny
glowing filament tube standing upright like a punctuation mark. Conveys the
craft of writing linear and mixed-integer models by hand before the solver
runs.

## symbol_mathopt.png  *(Speaking to the solver)*

A small brass speaking-tube mounted on a dark wooden panel, its bell aimed
toward the viewer, an amber filament glowing softly inside the throat. A
single neatly engraved label reads "MathOpt". Four thin brass cables fan out
from the back of the mount into shadow, each terminating in a faintly lit
nameplate — `GLOP`, `HIGHS`, `GUROBI`, `CP-SAT` — barely legible at the edge
of the frame. Conveys one shared interface fanning out to many solver
backends.

## symbol_lp_preserving.png  *(Efficient Reformulations / keeping LP)*

A dark surface holding two cream cards side by side. The left card shows a
hand-written `max |x - y|` in fine amber ink, neatly crossed out with a
single line. The right card shows a clean rewritten form — `t`, with
`t ≥ x - y`, `t ≥ y - x` — glowing slightly brighter, as if endorsed. A
brass-tipped fountain pen rests across both. Conveys reformulating a non-
linear expression into a linear one without giving up LP structure.

## symbol_bigm.png  *(Big-M warning)*

A heavy brass cog stamped with an oversized capital `M`, mounted on a dark
plinth and connected by a single taut amber wire to a small glowing
indicator lamp labelled `z`. Around the base of the plinth, fine sparks
betray the strain — the wire is doing too much work. A small enamel warning
plate at the corner reads "handle with care". Conveys the Big-M trick:
a single large constant that activates or disables a constraint, fragile
under careless tuning.

## symbol_logic.png  *(Adding Logic — AND/OR/implication on binaries)*

A small dark electrical-engineering desk holding three polished brass
binary switches arranged in a row, each labelled with a tiny enamel plate
`y₁`, `y₂`, `y₃`. Thin amber wires connect them through a single glowing
gate-shaped junction in the middle, and a fourth wire leaves the gate as
the result. One switch is up, the others down. Conveys assembling logical
combinations of binary decision variables.

## symbol_activation.png  *(Complex Domains / semi-continuous & segmented)*

A polished brass dimmer dial mounted on a dark control panel, its needle
parked exactly at zero against a tick mark labelled "off". A second tick
mark, far to the right, reads "L" and the arc between them is engraved with
the word `forbidden`, softly shadowed. A small amber indicator lamp wired
to the dial is dark. Conveys a variable that is either exactly zero or
lives inside an allowed band, never in between.

## symbol_pwla.png  *(Piecewise-linear approximation)*

A dark drafting board holding a single sheet of cream paper. On the paper,
a smooth curving amber ink line of a non-linear function is overlaid by a
sharp brass chain of four straight segments riveted together at glowing
breakpoints, hugging the curve closely. A tiny pair of brass dividers rests
on one of the breakpoints. Conveys approximating a smooth function with a
linked chain of linear pieces.

## symbol_strong_weak.png  *(Strong vs weak formulations)*

A dark workbench holding two transparent glass display cubes side by side.
Inside the left cube, a tight brass cage hugs a single small glowing amber
sphere — the integer optimum — with almost no air around it. Inside the
right cube, a much larger, slack brass cage contains the same sphere but
with wide empty space, the bars loose and faintly bent outward. Tiny
engraved plaques read "tight" and "loose". Conveys two formulations of the
same problem whose LP relaxations differ wildly in how tightly they enclose
the integer optimum.

## symbol_clockwork.png  *(See you next time)*

(Reused from T01/T02; regenerate only if needed.) An intricate exposed
clockwork mechanism, brass gears interlocking in perfect order, a single
jewelled escapement glowing amber at the center, faint motion blur on one
rotating wheel. Conveys time, closure, and "see you next time."
