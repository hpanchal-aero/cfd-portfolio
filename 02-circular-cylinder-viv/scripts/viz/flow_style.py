"""flow_style.py -- the shared look of the flow pictures and videos of Project 02.

Black background, black-centred diverging scale for vorticity and pressure (cyan/blue negative, red/yellow positive),
viridis for speed, light-grey cylinder, and motion cues that stay fixed in the picture: a dashed line at y = 0, a y/D
ruler with a pointer that follows the cylinder centre, and a crosshair on the cylinder that stays aligned with x and y
(the model has no rotation). The colour LIMITS are in flow_snapshots.FIELDS.
"""
import numpy as np
import pyvista as pv
from matplotlib.colors import LinearSegmentedColormap

BG = "black"
DISC = "#e6e6e6"
MARK = "#202020"
FG = "white"
DIV = LinearSegmentedColormap.from_list(
    "black_diverging", [(0.0, "#35e8ff"), (0.25, "#1f5bff"), (0.5, "#000000"), (0.75, "#ff2d1f"), (1.0, "#ffe14d")])
CMAP = {"vorticity": DIV, "pressure": DIV, "velocity": "viridis"}
RX = -4.5            # x of the y ruler
TICKS = [-1.0, -0.5, 0.0, 0.5, 1.0]


def scalar_bar_args():
    return dict(title=" ", vertical=False, position_x=0.3, position_y=0.04, width=0.4, height=0.06, color=FG)


def dashed_line_y0():
    xs = np.arange(-6.0, 15.0, 0.5)
    n = len(xs)
    pts = np.array([[x, 0.0, 0.3] for x in xs] + [[x + 0.25, 0.0, 0.3] for x in xs])
    d = pv.PolyData(pts)
    d.lines = np.hstack([[2, i, i + n] for i in range(n)])
    return d


def add_cues(p, cx, cy):
    """Dashed y = 0 line, y/D ruler with pointer, cylinder disc and crosshair, on plotter p."""
    p.add_mesh(dashed_line_y0(), color=FG, line_width=1.5, lighting=False)
    ruler = [pv.Line((RX, -1.1, 0.3), (RX, 1.1, 0.3))] + [pv.Line((RX - 0.15, y, 0.3), (RX + 0.15, y, 0.3)) for y in TICKS]
    for ln in ruler:
        p.add_mesh(ln, color=FG, line_width=2, lighting=False)
    tick_pts = np.array([[RX - 0.95, y, 0.3] for y in TICKS] + [[RX, 1.45, 0.3]])
    p.add_point_labels(tick_pts, ["-1", "-0.5", "0", "0.5", "1", "y / D"], font_size=12, text_color=FG,
                       shape=None, show_points=False, always_visible=True)
    pointer = pv.Circle(radius=0.11, resolution=40)
    pointer.translate((RX, cy, 0.35), inplace=True)
    p.add_mesh(pointer, color="#39ff14", lighting=False)
    disc = pv.Circle(radius=0.5, resolution=120)
    disc.translate((cx, cy, 0.2), inplace=True)
    p.add_mesh(disc, color=DISC, lighting=False)
    p.add_mesh(pv.Line((cx - 0.35, cy, 0.25), (cx + 0.35, cy, 0.25)), color=MARK, line_width=3, lighting=False)
    p.add_mesh(pv.Line((cx, cy - 0.35, 0.25), (cx, cy + 0.35, 0.25)), color=MARK, line_width=3, lighting=False)
