#!/usr/bin/env python3
"""spectrum_y.py -- amplitude spectrum of the cross-flow displacement y(t) of a spring-mounted run.

Usage:  spectrum_y.py <case_dir> <t0> <t1> <fn>

Reads   the body state from the logs exactly as body_motion.py does (log chunks + log.foamRun).
Does    in the window [t0, t1]: subtract the mean of y, apply a Hann window, zero-pad (x8 or more) and take
        the real FFT. Amplitude spectrum A(f) = 2*|FFT|/sum(window), so a pure sin(2 pi f t) of amplitude a
        gives a peak of height a (Hann scalloping up to 15 % for a frequency between two raw bins is reduced
        by the zero padding).
Prints  the window, the raw frequency resolution 1/(t1-t0) and the Hann main-lobe half-width 2/(t1-t0),
        the strongest peaks (local maxima above 5 % of the largest, f < 1), and the largest amplitude within
        +-0.005 of the spring's natural frequency fn, with its ratio to the strongest peak.
Peaks closer together than about 4/(t1-t0) are not resolved separately.
Read-only; writes nothing.
"""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import body_motion as bm


def main():
    if len(sys.argv) < 5:
        sys.exit(__doc__)
    case = sys.argv[1].rstrip("/")
    t0, t1, fn = float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
    t, x, y = bm.read_state(bm.chunk_logs(case))
    dts = np.diff(t)
    dt = float(np.median(dts))
    if np.max(dts) > 1.5 * dt:
        print("WARNING: gap in the state record, largest step %.4f (median %.4f)" % (np.max(dts), dt))
    m = (t >= t0) & (t <= t1)
    if m.sum() < 100:
        sys.exit("too few samples in the window (%d)" % m.sum())
    yw = y[m] - np.mean(y[m])
    n = len(yw)
    w = np.hanning(n)
    nfft = 8 * 2 ** int(np.ceil(np.log2(n)))
    spec = np.fft.rfft(yw * w, nfft)
    f = np.fft.rfftfreq(nfft, dt)
    a = 2.0 * np.abs(spec) / w.sum()
    span = t[m][-1] - t[m][0]
    print("window [%g, %g]: %d samples, dt %.5f, span %.2f, raw resolution %.4f, Hann main-lobe half-width %.4f"
          % (t0, t1, n, dt, span, 1.0 / span, 2.0 / span))
    sel = f < 1.0
    fs, as_ = f[sel], a[sel]
    peaks = [i for i in range(1, len(as_) - 1) if as_[i] > as_[i - 1] and as_[i] >= as_[i + 1] and as_[i] > 0.05 * as_.max()]
    peaks.sort(key=lambda i: -as_[i])
    print("strongest peaks (frequency, amplitude):")
    for i in peaks[:6]:
        print("   f = %.4f   A = %.5f" % (fs[i], as_[i]))
    near = (fs >= fn - 0.005) & (fs <= fn + 0.005)
    amax = as_[near].max()
    print("largest amplitude within +-0.005 of fn = %.4f:  A = %.5f   (%.1f %% of the strongest peak %.5f)"
          % (fn, amax, 100.0 * amax / as_.max(), as_.max()))


if __name__ == "__main__":
    main()
