#!/usr/bin/env python3
"""flow_video.py -- video of one field of a moving-cylinder case (one frame per saved time).

Usage (user packages are needed, so no -I):
    /usr/bin/python3 -E -P scripts/viz/flow_video.py <case_dir> <label> <t_from> <t_to>
        [--field vorticity|pressure|velocity] [--fps 20] [--out-root results/videos]
        [--frames-dir DIR] [--keep-frames]

The saved times of <case_dir> inside [t_from, t_to] are the frames (make a dense-output case with
scripts/run/make_video_case.sh). View, window, fields and colour LIMITS are those of flow_snapshots.py
(imported). The colour STYLE differs from the stills: black background, black-centred diverging scale
(cyan/blue negative, red/yellow positive) for vorticity and pressure, viridis for speed, light-grey cylinder.
Motion cues (fixed in the picture): dashed line at y = 0, a y/D ruler with a pointer that follows the cylinder
centre, and a crosshair on the cylinder that stays aligned with x and y (the model has no rotation).
Frames are rendered as PNG into --frames-dir (default ~/work_scratch/p02/video/frames_<label>_<field>),
encoded with /usr/bin/ffmpeg (H.264, yuv420p) into <out-root>/<label>_<field>.mp4, and deleted after a
successful encode unless --keep-frames.
"""
import argparse
import os
import shutil
import subprocess
import sys

import numpy as np
import pyvista as pv
from matplotlib.colors import LinearSegmentedColormap

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flow_snapshots import FIELDS, XC, YC, HALF_HEIGHT, read_time  # same view and colour limits as the stills

pv.OFF_SCREEN = True
SIZE = (1344, 768)   # 1.75 : 1 like the stills (1400 x 800), multiples of 16 for the encoder
BG = "black"
DISC = "#e6e6e6"
MARK = "#202020"
FG = "white"
DIV = LinearSegmentedColormap.from_list(
    "black_diverging", [(0.0, "#35e8ff"), (0.25, "#1f5bff"), (0.5, "#000000"), (0.75, "#ff2d1f"), (1.0, "#ffe14d")])
CMAP = {"vorticity": DIV, "pressure": DIV, "velocity": "viridis"}
RX = -4.5            # x of the y ruler
TICKS = [-1.0, -0.5, 0.0, 0.5, 1.0]


def dashed_line_y0():
    xs = np.arange(-6.0, 15.0, 0.5)
    n = len(xs)
    pts = np.array([[x, 0.0, 0.3] for x in xs] + [[x + 0.25, 0.0, 0.3] for x in xs])
    d = pv.PolyData(pts)
    d.lines = np.hstack([[2, i, i + n] for i in range(n)])
    return d


def main():
    ap = argparse.ArgumentParser(description="video of one field of a moving-cylinder case")
    ap.add_argument("case")
    ap.add_argument("label")
    ap.add_argument("t_from", type=float)
    ap.add_argument("t_to", type=float)
    ap.add_argument("--field", choices=list(FIELDS), default="vorticity")
    ap.add_argument("--fps", type=int, default=20)
    ap.add_argument("--out-root", default="results/videos")
    ap.add_argument("--frames-dir", default=None)
    ap.add_argument("--keep-frames", action="store_true")
    a = ap.parse_args()

    foam = os.path.join(a.case, "case.foam")
    if not os.path.exists(foam):
        open(foam, "w").close()
    r = pv.OpenFOAMReader(foam)
    r.enable_all_cell_arrays()
    r.enable_all_point_arrays()
    r.enable_all_patch_arrays()

    times = [t for t in r.time_values if a.t_from <= t <= a.t_to and t > 0]
    if len(times) < 2:
        sys.exit("fewer than 2 saved times in [%g, %g]; saved: %s" % (a.t_from, a.t_to, list(r.time_values)[:10]))
    dts = np.diff(times)
    print("frames: %d   t = %g .. %g   spacing %.4f .. %.4f" % (len(times), times[0], times[-1], dts.min(), dts.max()))

    fdir = a.frames_dir or os.path.expanduser("~/work_scratch/p02/video/frames_%s_%s" % (a.label, a.field))
    if os.path.exists(fdir):
        shutil.rmtree(fdir)
    os.makedirs(fdir)
    f = FIELDS[a.field]

    dash = dashed_line_y0()
    ruler = [pv.Line((RX, -1.1, 0.3), (RX, 1.1, 0.3))] + [pv.Line((RX - 0.15, y, 0.3), (RX + 0.15, y, 0.3)) for y in TICKS]
    tick_pts = np.array([[RX - 0.95, y, 0.3] for y in TICKS] + [[RX, 1.45, 0.3]])
    tick_lab = ["-1", "-0.5", "0", "0.5", "1", "y / D"]

    for i, t in enumerate(times):
        g, cx, cy = read_time(r, t)
        g.point_data["|U|"] = np.linalg.norm(g.point_data["U"], axis=1)
        d = g.compute_derivative(scalars="U", vorticity=True)
        g.point_data["wz"] = d["vorticity"][:, 2]
        p = pv.Plotter(off_screen=True, window_size=SIZE)
        p.set_background(BG)
        p.add_mesh(g, scalars=f["key"], cmap=CMAP[a.field], clim=f["clim"], show_edges=False, lighting=False,
                   scalar_bar_args=dict(title=" ", vertical=False, position_x=0.3, position_y=0.04,
                                        width=0.4, height=0.06, color=FG))
        p.add_mesh(dash, color=FG, line_width=1.5, lighting=False)
        for ln in ruler:
            p.add_mesh(ln, color=FG, line_width=2, lighting=False)
        p.add_point_labels(tick_pts, tick_lab, font_size=12, text_color=FG, shape=None, show_points=False,
                           always_visible=True)
        pointer = pv.Circle(radius=0.11, resolution=40)
        pointer.translate((RX, cy, 0.35), inplace=True)
        p.add_mesh(pointer, color="#39ff14", lighting=False)
        disc = pv.Circle(radius=0.5, resolution=120)
        disc.translate((cx, cy, 0.2), inplace=True)
        p.add_mesh(disc, color=DISC, lighting=False)
        p.add_mesh(pv.Line((cx - 0.35, cy, 0.25), (cx + 0.35, cy, 0.25)), color=MARK, line_width=3, lighting=False)
        p.add_mesh(pv.Line((cx, cy - 0.35, 0.25), (cx, cy + 0.35, 0.25)), color=MARK, line_width=3, lighting=False)
        p.camera.parallel_projection = True
        p.camera.focal_point = (XC, YC, 0.05)
        p.camera.position = (XC, YC, 50.0)
        p.camera.up = (0, 1, 0)
        p.camera.parallel_scale = HALF_HEIGHT
        p.add_text("%s   %s   t = %.1f   cylinder y = %+.3f D" % (a.label, f["caption"], t, cy),
                   position="upper_left", font_size=12, color=FG)
        p.screenshot(os.path.join(fdir, "%04d.png" % i))
        p.close()
        if i % 10 == 0 or i == len(times) - 1:
            print("  frame %d / %d   t = %.2f   cylinder y = %+.3f" % (i + 1, len(times), t, cy), flush=True)

    os.makedirs(a.out_root, exist_ok=True)
    mp4 = os.path.join(a.out_root, "%s_%s.mp4" % (a.label, a.field))
    cmd = ["/usr/bin/ffmpeg", "-y", "-loglevel", "error", "-framerate", str(a.fps),
           "-i", os.path.join(fdir, "%04d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", mp4]
    rc = subprocess.run(cmd).returncode
    if rc != 0:
        sys.exit("ffmpeg failed (exit %d); frames kept in %s" % (rc, fdir))
    if not a.keep_frames:
        shutil.rmtree(fdir)
    print("saved %s  (%.2f MB, %d frames at %d fps)" % (mp4, os.path.getsize(mp4) / 1e6, len(times), a.fps))


if __name__ == "__main__":
    main()
