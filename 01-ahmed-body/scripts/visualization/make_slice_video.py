#!/usr/bin/env python3
"""Time-evolution video of Cp and Ux/U_inf on a y-normal slice.

Reads postProcessing/cutPlaneSurface/<t>/cutPlane.vtk (point data p, U),
renders two stacked panels with a fixed camera and fixed colour limits,
and pipes raw frames to ffmpeg. No experimental data is used.
"""
import argparse
import os
import subprocess
import sys

import numpy as np
import pyvista as pv
from PIL import Image, ImageDraw, ImageFont

pv.OFF_SCREEN = True

W = 1600           # panel width (px)
PH = 400           # panel height (px)
HEAD_H = 64        # header strip
CAP_H = 52         # caption strip above each panel
BG = "#7f7f7f"     # background = body hole colour

LABELS = {
    "Cp": (
        "PRESSURE     Cp = p / (0.5 U_inf^2)",
        "red = high pressure (flow brought to rest: nose stagnation)  |  "
        "blue = low pressure (suction where the flow speeds up)  |  "
        "white = free-stream pressure",
    ),
    "Ux": (
        "STREAMWISE VELOCITY     Ux / U_inf",
        "yellow = faster than free stream  |  green = free-stream speed  |  "
        "blue / teal = slow flow (wake, separated layer)  |  "
        "purple = reversed flow (toward the nose)",
    ),
}

FONT_DIR = "/usr/share/fonts/truetype/dejavu/"


def font(size, bold=False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    try:
        return ImageFont.truetype(FONT_DIR + name, size)
    except OSError:
        return ImageFont.load_default()


def strip(h, lines):
    """White strip W x h; lines = [(text, font, y)]."""
    img = Image.new("RGB", (W, h), "white")
    d = ImageDraw.Draw(img)
    for text, f, y in lines:
        d.text((16, y), text, font=f, fill="black")
    return np.asarray(img)


def list_times(case):
    root = os.path.join(case, "postProcessing", "cutPlaneSurface")
    out = []
    for d in os.listdir(root):
        try:
            t = float(d)
        except ValueError:
            continue
        f = os.path.join(root, d, "cutPlane.vtk")
        if os.path.isfile(f):
            out.append((t, f))
    out.sort()
    return out


def render(path, t, args):
    m = pv.read(path)
    p = np.asarray(m.point_data["p"])
    U = np.asarray(m.point_data["U"])
    m.point_data["Cp"] = p / (0.5 * args.uinf**2)
    m.point_data["Ux"] = U[:, 0] / args.uinf

    zspan = args.zmax - args.zmin
    xspan = zspan * W / PH
    cx = args.xmin + xspan / 2.0
    cz = 0.5 * (args.zmin + args.zmax)
    cy = float(np.mean(m.points[:, 1]))

    pl = pv.Plotter(off_screen=True, shape=(2, 1), window_size=(W, 2 * PH),
                    border=False)
    specs = [
        ("Cp", "RdBu_r", [-1.2, 1.2], " ", 7),
        ("Ux", "viridis", [-0.4, 1.4], "  ", 10),   # unique titles (see note)
    ]
    for row, (name, cmap, clim, title, nlab) in enumerate(specs):
        pl.subplot(row, 0)
        pl.set_background(BG)
        pl.add_mesh(
            m, scalars=name, cmap=cmap, clim=clim, lighting=False,
            show_edges=False,
            scalar_bar_args=dict(
                title=title, vertical=True, position_x=0.93, position_y=0.06,
                height=0.74, width=0.04, label_font_size=11, color="black",
                n_labels=nlab, fmt="%.1f",
            ),
        )
        pl.camera.parallel_projection = True
        pl.camera.position = (cx, cy - 10.0, cz)
        pl.camera.focal_point = (cx, cy, cz)
        pl.camera.up = (0.0, 0.0, 1.0)
        pl.camera.parallel_scale = zspan / 2.0
    img = pl.screenshot(return_img=True)
    pl.close()
    top, bot = img[:PH], img[PH:2 * PH]

    f_title, f_sub = font(22, True), font(14)
    f_cap_b, f_cap = font(16, True), font(13)
    t_ms = t * 1000.0
    t_conv = t * args.uinf / args.L
    head = strip(HEAD_H, [
        (f"{args.title}     t = {t_ms:6.1f} ms   ({t_conv:5.2f} L/U_inf)",
         f_title, 8),
        ("Slice on the y-normal plane; fixed colour scales for every frame.",
         f_sub, 40),
    ])

    def cap(key):
        a, b = LABELS[key]
        return strip(CAP_H, [(a, f_cap_b, 6), (b, f_cap, 30)])

    return np.vstack([head, cap("Cp"), top, cap("Ux"), bot])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True)
    ap.add_argument("--out", help="output mp4")
    ap.add_argument("--png", help="write a single test PNG instead of a video")
    ap.add_argument("--t", type=float, help="time for --png (nearest)")
    ap.add_argument("--title", default=None)
    ap.add_argument("--fps", type=int, default=12)
    ap.add_argument("--hold-last", type=int, default=18)
    ap.add_argument("--stride", type=int, default=1)
    ap.add_argument("--uinf", type=float, default=60.0)
    ap.add_argument("--L", type=float, default=1.044)
    ap.add_argument("--xmin", type=float, default=-0.4)
    ap.add_argument("--zmin", type=float, default=0.0)
    ap.add_argument("--zmax", type=float, default=0.9)
    args = ap.parse_args()
    if args.title is None:
        args.title = os.path.basename(os.path.abspath(args.case))

    frames = list_times(args.case)
    if not frames:
        sys.exit("no cutPlane.vtk frames found")

    if args.png:
        t0 = args.t if args.t is not None else frames[-1][0]
        t, f = min(frames, key=lambda tf: abs(tf[0] - t0))
        Image.fromarray(render(f, t, args)).save(args.png)
        print(f"wrote {args.png} (t = {t})")
        return

    if not args.out:
        sys.exit("--out required for video")
    frames = frames[::args.stride]
    t, f = frames[0]
    first = render(f, t, args)
    h, w = first.shape[:2]
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo",
           "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(args.fps),
           "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-crf", "18", args.out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    ff.stdin.write(first.tobytes())
    last = first
    for i, (t, f) in enumerate(frames[1:], 1):
        last = render(f, t, args)
        ff.stdin.write(last.tobytes())
        if i % 25 == 0:
            print(f"  frame {i + 1}/{len(frames)}  t = {t}", flush=True)
    for _ in range(args.hold_last):
        ff.stdin.write(last.tobytes())
    ff.stdin.close()
    ff.wait()
    print(f"wrote {args.out}: {len(frames)} frames + {args.hold_last} hold, "
          f"{w}x{h}, {args.fps} fps")


if __name__ == "__main__":
    main()
