"""Generate the SVG assets used by the profile README.

    python assets/src/build.py

Everything is plain SVG + CSS animation, so it renders natively on GitHub
(no external fonts, scripts or services). Edit the palette or content here
and re-run instead of hand-editing the output files.
"""

from __future__ import annotations

import math
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent.parent

# Palette
INK = "#0B0B0F"
GRAPHITE = "#17171E"
VIOLET = "#8B6CFF"
WHITE = "#F0EFF7"
MUTED = "#A2A0B3"
CYAN = "#72D7E8"

SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"

COS30 = math.cos(math.radians(30))


# --------------------------------------------------------------------------
# Isometric helpers
# --------------------------------------------------------------------------

class Iso:
    def __init__(self, ox: float, oy: float):
        self.ox, self.oy = ox, oy

    def p(self, x: float, y: float, z: float = 0) -> tuple[float, float]:
        return (self.ox + (x - y) * COS30, self.oy + (x + y) * 0.5 - z)

    def poly(self, pts) -> str:
        return " ".join(f"{a:.1f},{b:.1f}" for a, b in (self.p(*q) for q in pts))

    def path(self, pts) -> str:
        xy = [self.p(*q) for q in pts]
        return "M" + " L".join(f"{a:.1f},{b:.1f}" for a, b in xy)


def box(iso: Iso, x, y, z, w, d, h, *, rim=True, top="url(#gTop)", tone=1.0) -> str:
    """Isometric box; (x, y, z) is the back-top-left corner on the ground plane."""
    x2, y2, z2 = x + w, y + d, z + h
    top_face = [(x, y, z2), (x2, y, z2), (x2, y2, z2), (x, y2, z2)]
    right_face = [(x2, y, z), (x2, y2, z), (x2, y2, z2), (x2, y, z2)]   # faces +x (screen right)
    left_face = [(x, y2, z), (x2, y2, z), (x2, y2, z2), (x, y2, z2)]    # faces +y (screen left)
    o = [
        f'<polygon points="{iso.poly(left_face)}" fill="url(#gLeft)" stroke="#2B2B36" stroke-width="0.8" opacity="{tone}"/>',
        f'<polygon points="{iso.poly(right_face)}" fill="url(#gRight)" stroke="#2B2B36" stroke-width="0.8" opacity="{tone}"/>',
        f'<polygon points="{iso.poly(top_face)}" fill="{top}" stroke="#3A3A48" stroke-width="0.8"/>',
        # front vertical edge highlight
        f'<path d="{iso.path([(x2, y2, z), (x2, y2, z2)])}" stroke="#4A4A5C" stroke-width="0.8"/>',
    ]
    if rim:
        # violet rim light on the back edges (light source sits behind the objects)
        o.append(
            f'<path d="{iso.path([(x, y2, z2), (x, y, z2), (x2, y, z2)])}" fill="none" '
            f'stroke="{VIOLET}" stroke-width="1.4" stroke-linecap="round" filter="url(#glow)" class="rim"/>'
        )
        o.append(
            f'<path d="{iso.path([(x2, y, z2), (x2, y, z + h * 0.15)])}" fill="none" '
            f'stroke="url(#gRimV)" stroke-width="1.2"/>'
        )
    return "\n".join(o)


def defs_common() -> str:
    return f"""
  <linearGradient id="gTop" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#34343F"/><stop offset=".55" stop-color="#23232C"/><stop offset="1" stop-color="#1A1A21"/>
  </linearGradient>
  <linearGradient id="gTopV" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#3A3550"/><stop offset=".6" stop-color="#25232F"/><stop offset="1" stop-color="#1B1A22"/>
  </linearGradient>
  <linearGradient id="gLeft" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#17171D"/><stop offset="1" stop-color="#0E0E12"/>
  </linearGradient>
  <linearGradient id="gRight" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#24242D"/><stop offset=".35" stop-color="#2E2E39"/>
    <stop offset=".42" stop-color="#1D1D25"/><stop offset="1" stop-color="#141419"/>
  </linearGradient>
  <linearGradient id="gRimV" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{VIOLET}" stop-opacity=".9"/><stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/>
  </linearGradient>
  <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur stdDeviation="1.6" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="soft" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur stdDeviation="22"/>
  </filter>"""


# --------------------------------------------------------------------------
# Banner
# --------------------------------------------------------------------------

def banner() -> str:
    W, H = 1200, 420
    iso = Iso(715, 182)

    # Floor grid (isometric), faded by a radial mask
    grid = []
    for i in range(-14, 15):
        g = i * 40
        grid.append(f'<path d="{iso.path([(g, -560), (g, 560)])}"/>')
        grid.append(f'<path d="{iso.path([(-560, g), (560, g)])}"/>')

    # Module layout (world coordinates)
    core = (-70, -70)       # compute core, centre
    rack = (-60, 150)       # server module, screen-left
    sensor = (160, -40)     # vision / sensor module, screen-right
    node_a = (-250, 60)
    node_b = (40, -290)
    node_c = (230, 170)

    # Ground traces between modules (axis-aligned so they read as PCB routing)
    traces = [
        [(0, 70), (0, 110), (-20, 110), (-20, 150)],                 # core -> rack
        [(70, 0), (120, 0), (120, 0), (160, 0)],                     # core -> sensor
        [(-60, 200), (-150, 200), (-150, 90), (-226, 90)],           # rack -> node a
        [(0, -70), (0, -150), (53, -150), (53, -264)],               # core -> node b
        [(205, 50), (205, 120), (254, 120), (254, 170)],             # sensor -> node c
        [(30, 250), (120, 250), (120, 194), (230, 194)],             # rack -> node c
    ]
    trace_base, trace_pulse = [], []
    for k, t in enumerate(traces):
        d = iso.path([(a, b, 0) for a, b in t])
        trace_base.append(f'<path d="{d}"/>')
        color = CYAN if k == 4 else VIOLET
        trace_pulse.append(
            f'<path d="{d}" stroke="{color}" class="pulse p{k}" pathLength="100"/>'
        )

    # Pads where traces meet modules
    pads = []
    for t in traces:
        for a, b in (t[0], t[-1]):
            cx, cy = iso.p(a, b)
            pads.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="3.4" ry="2"/>')

    # Core: three stacked slabs + die
    cx, cy = core
    core_parts = [
        box(iso, cx, cy, 0, 140, 140, 20, rim=False, tone=1),
        box(iso, cx + 12, cy + 12, 30, 116, 116, 14, rim=True),
        box(iso, cx + 26, cy + 26, 52, 88, 88, 12, rim=True, top="url(#gTopV)"),
    ]
    # die pattern on the top slab
    dz = 64
    die = []
    for i in range(5):
        for j in range(5):
            x0, y0 = cx + 36 + i * 14, cy + 36 + j * 14
            die.append(
                f'<polygon points="{iso.poly([(x0, y0, dz), (x0 + 9, y0, dz), (x0 + 9, y0 + 9, dz), (x0, y0 + 9, dz)])}" '
                f'class="cell c{(i * 3 + j * 2) % 5}"/>'
            )
    # spacer pillars between slabs
    pillars = []
    for (px, py) in [(cx + 20, cy + 20), (cx + 120, cy + 20), (cx + 120, cy + 120), (cx + 20, cy + 120)]:
        pillars.append(f'<path d="{iso.path([(px, py, 20), (px, py, 30)])}" stroke="#4A4A5C" stroke-width="2"/>')

    # Rack: tall unit with blade slots on its left face
    rx, ry = rack
    rack_parts = [box(iso, rx, ry, 0, 80, 100, 128)]
    slots = []
    for s in range(6):
        z = 18 + s * 18
        slots.append(
            f'<path d="{iso.path([(rx + 10, ry + 100, z), (rx + 58, ry + 100, z)])}" stroke="#2E2E3A" stroke-width="5" stroke-linecap="round"/>'
        )
        lx, ly = iso.p(rx + 68, ry + 100, z)
        slots.append(f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="1.6" class="led l{s % 3}"/>')

    # Sensor: low housing with a lens stack on top
    sx, sy = sensor
    sensor_parts = [box(iso, sx, sy, 0, 90, 90, 46)]
    lx, ly = iso.p(sx + 45, sy + 45, 46)
    lens = f"""
    <g transform="translate({lx:.1f},{ly:.1f})">
      <ellipse cx="0" cy="0" rx="34" ry="19.6" fill="#101015" stroke="#3A3A48"/>
      <path d="M-34,0 L-34,-10 A34,19.6 0 0 1 34,-10 L34,0 A34,19.6 0 0 1 -34,0 Z" fill="#1C1C24"/>
      <ellipse cx="0" cy="-10" rx="34" ry="19.6" fill="url(#gTop)" stroke="{VIOLET}" stroke-opacity=".7" stroke-width="1.2" filter="url(#glow)"/>
      <ellipse cx="0" cy="-10" rx="22" ry="12.7" fill="#08080B" stroke="#3A3A48"/>
      <ellipse cx="0" cy="-10" rx="13" ry="7.5" fill="url(#gLens)"/>
      <ellipse cx="-5" cy="-13" rx="4" ry="2.2" fill="{WHITE}" opacity=".55"/>
      <ellipse cx="0" cy="-10" rx="13" ry="7.5" fill="none" stroke="{CYAN}" stroke-opacity=".35" class="scan"/>
    </g>"""

    nodes = [box(iso, a, b, 0, 26, 26, 22) for a, b in (node_a, node_b, node_c)]

    # Ambient dust
    dust = []
    for k, (x, y, r) in enumerate([(330, 120, 1.2), (460, 70, 0.9), (900, 90, 1.1), (1010, 210, 0.8),
                                   (800, 330, 1.0), (420, 300, 0.9), (610, 60, 0.7), (1080, 120, 0.9)]):
        dust.append(f'<circle cx="{x}" cy="{y}" r="{r}" class="dust d{k % 4}"/>')

    cs = f"""
    .grid path {{ stroke: {MUTED}; stroke-width: .6; opacity: .07; fill: none; }}
    .traces path {{ stroke: #2A2A36; stroke-width: 2; fill: none; stroke-linejoin: round; }}
    .traces .pulse {{ stroke-width: 2.2; stroke-dasharray: 6 94; stroke-linecap: round;
                      animation: flow 5.5s linear infinite; filter: url(#glow); }}
    .p1 {{ animation-delay: -1.2s !important; }} .p2 {{ animation-delay: -2.7s !important; animation-duration: 7s !important; }}
    .p3 {{ animation-delay: -3.9s !important; }} .p4 {{ animation-delay: -.6s !important; animation-duration: 6.5s !important; }}
    .p5 {{ animation-delay: -4.4s !important; animation-duration: 8s !important; }}
    @keyframes flow {{ from {{ stroke-dashoffset: 100; }} to {{ stroke-dashoffset: 0; }} }}
    .pads ellipse {{ fill: #3A3A48; }}
    .float {{ animation: float 7s ease-in-out infinite; }}
    .float2 {{ animation: float 9s ease-in-out -3s infinite; }}
    @keyframes float {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-5px); }} }}
    .rim {{ animation: rim 6s ease-in-out infinite; }}
    @keyframes rim {{ 0%, 100% {{ stroke-opacity: .65; }} 50% {{ stroke-opacity: 1; }} }}
    .cell {{ fill: #2A2738; animation: cell 4.8s ease-in-out infinite; }}
    .c1 {{ animation-delay: -1s; }} .c2 {{ animation-delay: -2s; }} .c3 {{ animation-delay: -3s; }} .c4 {{ animation-delay: -4s; }}
    @keyframes cell {{ 0%, 70%, 100% {{ fill: #2A2738; }} 82% {{ fill: {VIOLET}; }} }}
    .led {{ fill: {VIOLET}; animation: led 3s steps(1) infinite; }}
    .l1 {{ animation-delay: -1s; }} .l2 {{ animation-delay: -2s; fill: {CYAN}; }}
    @keyframes led {{ 0%, 60% {{ opacity: .25; }} 61%, 100% {{ opacity: 1; }} }}
    .halo {{ animation: halo 8s ease-in-out infinite; }}
    @keyframes halo {{ 0%, 100% {{ opacity: .32; }} 50% {{ opacity: .5; }} }}
    .scan {{ animation: scan 4s ease-in-out infinite; transform-box: fill-box; transform-origin: center; }}
    @keyframes scan {{ 0%, 100% {{ transform: scale(1); opacity: .2; }} 50% {{ transform: scale(1.35); opacity: .6; }} }}
    .dust {{ fill: {MUTED}; animation: dust 10s ease-in-out infinite; }}
    .d1 {{ animation-delay: -2.5s; }} .d2 {{ animation-delay: -5s; }} .d3 {{ animation-delay: -7.5s; }}
    @keyframes dust {{ 0%, 100% {{ opacity: .08; transform: translateY(0); }} 50% {{ opacity: .45; transform: translateY(-8px); }} }}
    .label {{ font: 500 11px {MONO}; fill: {MUTED}; letter-spacing: .14em; }}
    .label b {{ fill: {VIOLET}; font-weight: 500; }}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
    """

    # module call-out labels
    def callout(wx, wy, wz, text, dx, dy):
        px, py = iso.p(wx, wy, wz)
        tx, ty = px + dx, py + dy
        anchor = "end" if dx < 0 else "start"
        return (
            f'<path d="M{px:.1f},{py:.1f} L{tx:.1f},{ty:.1f} L{tx + (-1 if dx < 0 else 1) * 14:.1f},{ty:.1f}" '
            f'stroke="{MUTED}" stroke-opacity=".35" fill="none"/>'
            f'<circle cx="{px:.1f}" cy="{py:.1f}" r="2" fill="{VIOLET}"/>'
            f'<text x="{tx + (-1 if dx < 0 else 1) * 20:.1f}" y="{ty + 4:.1f}" text-anchor="{anchor}" class="label">{text}</text>'
        )

    callouts = [
        callout(rx, ry + 60, 110, "INFRA", -90, 10),
        callout(cx + 114, cy + 40, 64, "BACKEND · AI", 130, -8),
        callout(sx + 90, sy + 50, 30, "VISION · EDGE", 60, 30),
    ]

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">
<title id="t">MohammadHossein Saeidi</title>
<desc id="d">A dark graphite scene of connected, precision-machined technology modules (an infrastructure rack, a compute core and a vision sensor) lit with a violet rim light, with signals pulsing along circuit traces between them.</desc>
<defs>{defs_common()}
  <radialGradient id="gBg" cx=".58" cy=".55" r=".7">
    <stop offset="0" stop-color="{GRAPHITE}"/><stop offset="1" stop-color="{INK}"/>
  </radialGradient>
  <radialGradient id="gHalo" cx=".5" cy=".5" r=".5">
    <stop offset="0" stop-color="{VIOLET}" stop-opacity=".55"/><stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="gLens" cx=".35" cy=".35" r=".8">
    <stop offset="0" stop-color="#4B3F8F"/><stop offset=".5" stop-color="#1A1630"/><stop offset="1" stop-color="#050507"/>
  </radialGradient>
  <radialGradient id="gFade" cx=".58" cy=".6" r=".55">
    <stop offset="0" stop-color="#fff"/><stop offset=".7" stop-color="#fff" stop-opacity=".4"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
  </radialGradient>
  <mask id="mFade"><rect width="{W}" height="{H}" fill="url(#gFade)"/></mask>
  <linearGradient id="gVignette" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{INK}" stop-opacity="0"/><stop offset=".75" stop-color="{INK}" stop-opacity="0"/><stop offset="1" stop-color="{INK}" stop-opacity=".9"/>
  </linearGradient>
  <clipPath id="frame"><rect width="{W}" height="{H}" rx="18"/></clipPath>
</defs>
<style>{cs}</style>
<g clip-path="url(#frame)">
  <rect width="{W}" height="{H}" fill="url(#gBg)"/>
  <ellipse cx="{iso.p(0, 0)[0]:.0f}" cy="{iso.p(0, 0)[1] + 10:.0f}" rx="330" ry="150" fill="url(#gHalo)" class="halo" filter="url(#soft)"/>
  <g class="grid" mask="url(#mFade)">{''.join(grid)}</g>
  <g class="traces">{''.join(trace_base)}{''.join(trace_pulse)}</g>
  <g class="pads">{''.join(pads)}</g>
  <g class="float2">{''.join(nodes)}</g>
  <g>{''.join(rack_parts)}{''.join(slots)}</g>
  <g class="float">{''.join(core_parts)}{''.join(pillars)}{''.join(die)}</g>
  <g class="float2">{''.join(sensor_parts)}{lens}</g>
  <g>{''.join(callouts)}</g>
  <g>{''.join(dust)}</g>
  <rect width="{W}" height="{H}" fill="url(#gVignette)"/>
  <text x="44" y="56" class="label"><tspan style="fill:{VIOLET}">●</tspan>  MH—S / SYSTEMS</text>
  <text x="44" y="{H - 38}" class="label">SOFTWARE  ·  INFRASTRUCTURE  ·  INTELLIGENT SYSTEMS</text>
  <text x="{W - 44}" y="56" text-anchor="end" class="label">v.2026</text>
  <rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="18" fill="none" stroke="#FFFFFF" stroke-opacity=".06"/>
</g>
</svg>
"""


# --------------------------------------------------------------------------
# Divider
# --------------------------------------------------------------------------

def divider() -> str:
    W, H = 1200, 12
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="presentation">
<defs>
  <linearGradient id="g" x1="0" x2="1">
    <stop offset="0" stop-color="{MUTED}" stop-opacity="0"/><stop offset=".5" stop-color="{VIOLET}"/><stop offset="1" stop-color="{MUTED}" stop-opacity="0"/>
  </linearGradient>
</defs>
<style>.p {{ animation: p 6s ease-in-out infinite; }} @keyframes p {{ 0%, 100% {{ opacity: .45; }} 50% {{ opacity: 1; }} }}
@media (prefers-reduced-motion: reduce) {{ .p {{ animation: none; }} }}</style>
<rect y="5.5" width="{W}" height="1" fill="url(#g)" class="p"/>
<rect x="{W / 2 - 3}" y="3" width="6" height="6" transform="rotate(45 {W / 2} 6)" fill="{VIOLET}"/>
</svg>
"""


# --------------------------------------------------------------------------
# Project cards
# --------------------------------------------------------------------------

def card(*, kicker: str, title: str, lines: list[str], chips: list[str], glyph: str, accent: str = VIOLET) -> str:
    W, H = 590, 236
    chip_svg, x = [], 28
    for c in chips:
        w = 13 + len(c) * 7.2
        chip_svg.append(
            f'<g transform="translate({x:.0f},{H - 50})"><rect width="{w:.0f}" height="24" rx="12" fill="{INK}" stroke="#2E2E3A"/>'
            f'<text x="{w / 2:.1f}" y="16" text-anchor="middle" class="chip">{escape(c)}</text></g>'
        )
        x += w + 8
    body = "".join(
        f'<text x="28" y="{110 + i * 22}" class="body">{escape(line)}</text>' for i, line in enumerate(lines)
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(title)}">
<defs>{defs_common()}
  <linearGradient id="gCard" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{GRAPHITE}"/><stop offset="1" stop-color="{INK}"/>
  </linearGradient>
  <linearGradient id="gEdge" x1="0" x2="1">
    <stop offset="0" stop-color="{accent}" stop-opacity="0"/><stop offset=".5" stop-color="{accent}"/><stop offset="1" stop-color="{accent}" stop-opacity="0"/>
  </linearGradient>
</defs>
<style>
  .kicker {{ font: 500 11px {MONO}; fill: {accent}; letter-spacing: .14em; }}
  .title {{ font: 600 25px {SANS}; fill: {WHITE}; letter-spacing: -.01em; }}
  .body {{ font: 400 14px {SANS}; fill: {MUTED}; }}
  .chip {{ font: 500 11px {MONO}; fill: {WHITE}; opacity: .85; }}
  .arrow {{ font: 400 18px {SANS}; fill: {MUTED}; }}
  .edge {{ animation: e 7s ease-in-out infinite; }}
  @keyframes e {{ 0%, 100% {{ opacity: .35; }} 50% {{ opacity: 1; }} }}
  .float {{ animation: f 7s ease-in-out infinite; }}
  @keyframes f {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-3px); }} }}
  .rim {{ stroke-opacity: .9; }}
  @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
</style>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="url(#gCard)" stroke="#FFFFFF" stroke-opacity=".08"/>
<rect x="40" y="0" width="{W - 80}" height="1.2" fill="url(#gEdge)" class="edge"/>
<g class="float">{glyph}</g>
<text x="28" y="44" class="kicker">{escape(kicker)}</text>
<text x="28" y="78" class="title">{escape(title)}</text>
{body}
{''.join(chip_svg)}
<text x="{W - 30}" y="46" text-anchor="end" class="arrow">↗</text>
</svg>
"""


def glyph_agent() -> str:
    """Three stacked slabs: an agent pipeline / service stack."""
    iso = Iso(488, 92)
    return "".join([
        box(iso, -30, -30, 0, 60, 60, 10, rim=False),
        box(iso, -24, -24, 16, 48, 48, 10),
        box(iso, -18, -18, 32, 36, 36, 10, top="url(#gTopV)"),
    ])


def glyph_vision() -> str:
    """Sensor block with a lens: computer vision."""
    iso = Iso(488, 100)
    b = box(iso, -30, -30, 0, 60, 60, 26)
    lx, ly = iso.p(0, 0, 26)
    return b + (
        f'<g transform="translate({lx:.1f},{ly:.1f})">'
        f'<ellipse rx="22" ry="12.7" fill="#08080B" stroke="{CYAN}" stroke-opacity=".6" filter="url(#glow)"/>'
        f'<ellipse rx="12" ry="6.9" fill="#1A1630"/><ellipse cx="-4" cy="-2.5" rx="3" ry="1.7" fill="{WHITE}" opacity=".5"/></g>'
    )


def main() -> None:
    files = {
        "banner.svg": banner(),
        "divider.svg": divider(),
        "card-research-assistant.svg": card(
            kicker="AI AGENT  ·  FULL STACK",
            title="Research Assistant",
            lines=[
                "An AI research agent behind a chat interface, with",
                "persistent sessions. FastAPI + LangGraph backend,",
                "SvelteKit frontend, shipped as a Compose stack.",
            ],
            chips=["FastAPI", "LangGraph", "PostgreSQL", "SvelteKit", "Docker"],
            glyph=glyph_agent(),
        ),
        "card-reid.svg": card(
            kicker="COMPUTER VISION  ·  EDGE AI",
            title="One-Shot Person ReID",
            lines=[
                "Enrol a person from one photo, then find them in",
                "live streams. Face-based identity that survives a",
                "change of clothes, with Unknown as a real answer.",
            ],
            chips=["YOLO26", "BoT-SORT", "ONNX", "OpenCV", "Jetson"],
            glyph=glyph_vision(),
            accent=CYAN,
        ),
    }
    for name, svg in files.items():
        (OUT / name).write_text(svg, encoding="utf-8")
        print(f"wrote assets/{name}  ({len(svg) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
