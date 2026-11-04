"""RoB meeting (calendar) and Initiative (rocket) pictogram variants, 64 grid, 1px."""
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent  # features/pictograms/explorations
SA = ('stroke="currentColor" stroke-width="1" stroke-linecap="butt" stroke-linejoin="miter" '
      'stroke-miterlimit="10" vector-effect="non-scaling-stroke"')
f = lambda v: f"{round(v, 2):g}"
st = lambda d: f'<path d="{d}" {SA}/>'
tn = lambda d: f'<path opacity="0.15" d="{d}" fill="currentColor"/>'
circ = lambda cx, cy, r: f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" {SA}/>'
circ_t = lambda cx, cy, r: f'<circle opacity="0.15" cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="currentColor"/>'
svg = lambda parts: ('<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">'
                     + "".join(parts) + "</svg>")


def rect(x0, y0, x1, y1):
    return f"M{f(x0)} {f(y0)}H{f(x1)}V{f(y1)}H{f(x0)}Z"


# ------------------------------------------------------------------ calendar
def calendar(x0, x1, y0, y1, rings, cut=None, header=19):
    """Library-style calendar: rounded frame (r3), notched top edge where the
    binding rings sit, tinted header strip. `rings` = left x of each 4-wide ring.
    `cut` = (stop_y_on_right_edge, stop_x_on_bottom_edge) to break the frame
    around an overlapping badge in the bottom-right corner."""
    r = 3
    tint, strokes = [], []
    # header tint, notched under each ring
    d = f"M{f(x0 + 0.5 + r - 0.5)} {f(y0 + 0.5)}"
    pts = [f"M{f(x0 + 3.5)} {f(y0 + 0.5)}"]
    t = f"M{f(x1 - 3)} {f(y0 + 0.5)}A2.5 2.5 0 0 1 {f(x1 - 0.5)} {f(y0 + 3)}V{header}H{f(x0 + 0.5)}V{f(y0 + 3)}A2.5 2.5 0 0 1 {f(x0 + 3)} {f(y0 + 0.5)}"
    for rx in rings:
        t += f"H{f(rx - 0.5)}V{f(y0 + 5.5)}H{f(rx + 4.5)}V{f(y0 + 0.5)}"
    t += "Z"
    tint.append(tn(t))
    # frame: open path from the last ring, round the frame, back to the first ring
    first, last = rings[0], rings[-1]
    if cut:
        sy, sx = cut
        strokes.append(st(f"M{f(x1)} {f(sy)}V{f(y0 + r)}A3 3 0 0 0 {f(x1 - r)} {f(y0)}H{f(last + 5)}"))
        strokes.append(st(f"M{f(first - 1)} {f(y0)}H{f(x0 + r)}A3 3 0 0 0 {f(x0)} {f(y0 + r)}"
                          f"V{f(y1 - r)}A3 3 0 0 0 {f(x0 + r)} {f(y1)}H{f(sx)}"))
    else:
        strokes.append(st(f"M{f(first - 1)} {f(y0)}H{f(x0 + r)}A3 3 0 0 0 {f(x0)} {f(y0 + r)}"
                          f"V{f(y1 - r)}A3 3 0 0 0 {f(x0 + r)} {f(y1)}H{f(x1 - r)}"
                          f"A3 3 0 0 0 {f(x1)} {f(y1 - r)}V{f(y0 + r)}A3 3 0 0 0 {f(x1 - r)} {f(y0)}H{f(last + 5)}"))
    for a, b in zip(rings, rings[1:]):
        strokes.append(st(f"M{f(a + 5)} {f(y0)}H{f(b - 1)}"))
    for rx in rings:  # 4×10 binding rings, straddling the top edge
        strokes.append(st(rect(rx, y0 - 5, rx + 4, y0 + 5)))
    return tint, strokes


def arrowhead(tip, direction, length=4, half=3):
    """Open chevron at `tip`, pointing along `direction` (unit vector)."""
    dx, dy = direction
    bx, by = -dx, -dy
    px, py = -dy, dx
    w1 = (tip[0] + length * bx + half * px, tip[1] + length * by + half * py)
    w2 = (tip[0] + length * bx - half * px, tip[1] + length * by - half * py)
    return st(f"M{f(w1[0])} {f(w1[1])}L{f(tip[0])} {f(tip[1])}L{f(w2[0])} {f(w2[1])}")


def on_circle(cx, cy, r, deg):
    a = math.radians(deg)
    return cx + r * math.cos(a), cy + r * math.sin(a)


def person(cx, head_cy, head_r=3, shoulder=5.5):
    """Library-style person: circle head over a shoulder arc."""
    base = head_cy + head_r + shoulder + 0.5
    return [circ(cx, head_cy, head_r),
            st(f"M{f(cx - shoulder)} {f(base)}A{f(shoulder)} {f(shoulder)} 0 0 1 {f(cx + shoulder)} {f(base)}")]


P = {}

# ---- RoB 1: weekly — the same weekday highlighted every week ---------------
tint, strokes = calendar(0.5, 63.5, 8.5, 59.5, rings=[10.5, 49.5])
cells, wed = [], []
for yi, y in enumerate((25.5, 36.5, 47.5)):
    for xi, x in enumerate((6.5, 17.5, 28.5, 39.5, 50.5)):
        cells.append(rect(x, y, x + 7, y + 7))
        if xi == 2:
            wed.append(rect(x + 0.5, y + 0.5, x + 6.5, y + 6.5))
band = rect(27, 19, 37, 59)            # the same weekday, every week
P["rob-weekly"] = svg(tint + [tn(band)] + strokes + [st("".join(cells)),
                      st("M30 39.5L31.5 41L34 38.5")])

# ---- RoB 2: recurring — a cycle around the team ----------------------------
tint, strokes = calendar(0.5, 63.5, 8.5, 59.5, rings=[10.5, 49.5])
cx, cy, r = 32, 39.5, 13
a_end = on_circle(cx, cy, r, -25)
b_end = on_circle(cx, cy, r, 155)
loop = [st(f"M{f(cx - r)} {f(cy)}A{r} {r} 0 0 1 {f(a_end[0])} {f(a_end[1])}"),
        st(f"M{f(cx + r)} {f(cy)}A{r} {r} 0 0 1 {f(b_end[0])} {f(b_end[1])}"),
        arrowhead(a_end, (-math.sin(math.radians(-25)), math.cos(math.radians(-25)))),
        arrowhead(b_end, (-math.sin(math.radians(155)), math.cos(math.radians(155))))]
P["rob-recurring"] = svg(tint + [circ_t(cx, cy, 9.5)] + strokes + loop + person(cx, 35.5, 3, 5.5))

# ---- RoB 3: decisions — agenda calendar, a speech bubble with a check -------
tint, strokes = calendar(0.5, 47.5, 8.5, 47.5, rings=[8.5, 34.5], cut=(29.5, 25.5))
agenda = [st("M7 25.5H41"), st("M7 31.5H24"), st("M7 37.5H24")]
bubble = ("M31.5 32.5H60.5A3 3 0 0 1 63.5 35.5V52.5A3 3 0 0 1 60.5 55.5H42L33.5 62.5L36 55.5"
          "H31.5A3 3 0 0 1 28.5 52.5V35.5A3 3 0 0 1 31.5 32.5Z")
P["rob-decisions"] = svg(tint + [tn(bubble)] + strokes + agenda +
                         [st(bubble), st("M38.5 44L43.5 49L53.5 39")])


# ------------------------------------------------------------------ rocket
class Xf:
    """Affine transform: scale s, rotate deg (clockwise on screen), then move."""
    def __init__(self, tx, ty, s=1.0, deg=0.0):
        self.tx, self.ty, self.s = tx, ty, s
        a = math.radians(deg)
        self.c, self.n = math.cos(a), math.sin(a)

    def __call__(self, x, y):
        x, y = x * self.s, y * self.s
        return (self.tx + x * self.c - y * self.n, self.ty + x * self.n + y * self.c)

    def path(self, segs):
        out = []
        for cmd, *pts in segs:
            if cmd == "Z":
                out.append("Z"); continue
            q = [self(*p) for p in pts]
            out.append(cmd + " ".join(f"{f(x)} {f(y)}" for x, y in q))
        return "".join(out)


# rocket in local coordinates: nose tip at (0,0), axis down +y
BODY = [("M", (-7.5, 42.5)), ("L", (-7.5, 20)), ("C", (-7.5, 10), (-4, 3.5), (0, 0)),
        ("C", (4, 3.5), (7.5, 10), (7.5, 20)), ("L", (7.5, 42.5)), ("Z",)]
SHADE = [("M", (0, 1)), ("C", (3.5, 4.2), (7, 10.4), (7, 20)), ("L", (7, 42)), ("L", (0, 42)), ("Z",)]
FIN_L = [("M", (-7.5, 31)), ("L", (-14.5, 39)), ("L", (-14.5, 46.5)), ("L", (-7.5, 42.5))]
FIN_R = [("M", (7.5, 31)), ("L", (14.5, 39)), ("L", (14.5, 46.5)), ("L", (7.5, 42.5))]
NOZZLE = [("M", (-3.5, 42.5)), ("L", (-3.5, 46.5)), ("L", (3.5, 46.5)), ("L", (3.5, 42.5))]
FLAME = [("M", (-2.5, 46.5)), ("Q", (-2.5, 52), (0, 56.5)), ("Q", (2.5, 52), (2.5, 46.5))]


def rocket(xf, window=True):
    tints = [tn(xf.path(SHADE)), tn(xf.path(FLAME + [("Z",)]))]
    strokes = [st(xf.path(BODY)), st(xf.path(FIN_L)), st(xf.path(FIN_R)),
               st(xf.path(NOZZLE)), st(xf.path(FLAME))]
    if window:
        wx, wy = xf(0, 21)
        strokes.append(circ(wx, wy, 4 * xf.s))
    return tints, strokes


# ---- Initiative 1: launch — rocket lifting off, speed lines and sparkles ----
t, s = rocket(Xf(32, 1))
speed = [st("M20.5 50V60"), st("M43.5 50V60"), st("M26.5 58V63.5"), st("M37.5 58V63.5")]
spark = [st("M8.5 9.5V17.5M4.5 13.5H12.5"), st("M55.5 19.5V25.5M52.5 22.5H58.5")]
P["init-launch"] = svg(t + s + speed + spark)

# ---- Initiative 2: growth — rocket climbing past rising key-result bars -----
t, s = rocket(Xf(51.5, 1.5, 0.8))
bars = [st("M2.5 62.5V46.5H11.5V62.5"), st("M15.5 62.5V36.5H24.5V62.5"),
        st("M28.5 62.5V24.5H37.5V62.5"), st("M0.5 62.5H63.5")]
speed = [st("M47.5 45V54"), st("M55.5 45V54")]
P["init-growth"] = svg([tn(rect(29, 25, 37, 62))] + t + s + bars + speed)

# ---- Initiative 3: milestones — rocket on a trajectory through checkpoints --
xf = Xf(59, 5, 0.85, 45)              # nose top-right, pointing up-right
t, s = rocket(xf)
tip = xf(0, 56.5)                     # flame tip; the trajectory starts just behind it
end = (tip[0] - 2, tip[1] + 2)
p0, c = (3, 61.5), (6, 44)
mid = (0.25 * p0[0] + 0.5 * c[0] + 0.25 * end[0], 0.25 * p0[1] + 0.5 * c[1] + 0.25 * end[1])
path = st(f"M{f(p0[0])} {f(p0[1])}Q{f(c[0])} {f(c[1])} {f(end[0])} {f(end[1])}")
dot = lambda x, y: f'<circle cx="{f(x)}" cy="{f(y)}" r="2" fill="currentColor"/>'
miles = [dot(*p0), dot(*mid)]
spark = [st("M14.5 6.5V14.5M10.5 10.5H18.5")]
P["init-milestones"] = svg(t + s + [path] + miles + spark)

for k, v in P.items():
    folder = HERE / ("rob-meetings" if k.startswith("rob-") else "initiatives")
    (folder / f"{k}.svg").write_text(v + "\n")
print(" ".join(P))
