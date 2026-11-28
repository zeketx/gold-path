#!/usr/bin/env python3
"""Generate the Gold Path footer illustration.

Original procedural artwork: a winding road receding toward a horizon,
rendered as a grayscale scene and then dithered to the site brand gold.

No third-party photographs, stock, or trademarks are used. The output is
a two-color indexed PNG (white + gold) owned by this repository.

Usage:
    python3 scripts/generate-footer-path.py
    python3 scripts/generate-footer-path.py --method bayer
    python3 scripts/generate-footer-path.py --method fs
    python3 scripts/generate-footer-path.py --method clustered
"""

from __future__ import annotations

import argparse
import math
import os
import struct
import zlib

# Brand gold from styles.css --accent (the ink used on light grounds).
GOLD = (0x9A, 0x6F, 0x00)
WHITE = (0xFF, 0xFF, 0xFF)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "assets", "footer-gold-path.png")

WIDTH = 1600
HEIGHT = 720


def bayer_matrix(n: int) -> list[list[int]]:
    matrix = [[0]]
    while len(matrix) < n:
        size = len(matrix)
        nxt = [[0] * (size * 2) for _ in range(size * 2)]
        for y in range(size):
            for x in range(size):
                value = matrix[y][x]
                nxt[y][x] = 4 * value
                nxt[y][x + size] = 4 * value + 2
                nxt[y + size][x] = 4 * value + 3
                nxt[y + size][x + size] = 4 * value + 1
        matrix = nxt
    return matrix


BAYER8 = bayer_matrix(8)


def hash2(ix: int, iz: int) -> float:
    n = (ix * 374761393 + iz * 668265263) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    return (n & 0xFFFFFF) / 0xFFFFFF


def noise2(x: float, z: float) -> float:
    ix, iz = math.floor(x), math.floor(z)
    fx, fz = x - ix, z - iz
    sx = fx * fx * (3.0 - 2.0 * fx)
    sz = fz * fz * (3.0 - 2.0 * fz)
    n00 = hash2(ix, iz)
    n10 = hash2(ix + 1, iz)
    n01 = hash2(ix, iz + 1)
    n11 = hash2(ix + 1, iz + 1)
    nx0 = n00 + (n10 - n00) * sx
    nx1 = n01 + (n11 - n01) * sx
    return nx0 + (nx1 - nx0) * sz


def fbm(x: float, z: float, octaves: int = 4) -> float:
    total = 0.0
    amp = 0.5
    freq = 1.0
    for _ in range(octaves):
        total += amp * noise2(x * freq, z * freq)
        freq *= 2.02
        amp *= 0.5
    return total


def hill_profile(x_norm: float, seed: float) -> float:
    return (
        0.52
        + 0.30 * math.sin(x_norm * 6.1 + seed)
        + 0.20 * math.sin(x_norm * 13.4 + seed * 1.7)
        + 0.12 * math.sin(x_norm * 2.4 + seed * 0.5)
        + 0.06 * math.sin(x_norm * 22.0 + seed * 2.3)
    )


def road_x(v: float) -> float:
    """Screen-space centre of the path. v=0 at the horizon, v=1 at the bottom."""
    vanish = 0.60
    sway = (
        0.20 * math.sin(v * math.pi * 1.55 + 0.55)
        + 0.07 * math.sin(v * math.pi * 3.1 + 1.2)
    )
    return vanish + sway * (0.18 + 0.82 * v)


def road_half(v: float) -> float:
    """Perspective half-width in screen units (fraction of image width)."""
    return 0.005 + 0.155 * (v ** 1.42)


def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return lo if v < lo else hi if v > hi else v


def render_values(w: int, h: int) -> list[list[float]]:
    """Return a 0..1 buffer, where 1 is full gold ink."""
    horizon = int(h * 0.40)
    values = [[0.0] * w for _ in range(h)]

    # --- Sky stays nearly white so footer copy sits on a clean ground ---
    for y in range(horizon):
        t = y / max(horizon, 1)
        for x in range(w):
            cloud = fbm(x / w * 3.4 + 2.0, t * 2.0 + 9.0, 3)
            puff = clamp((cloud - 0.58) * 3.4) * 0.07 * t
            values[y][x] = puff

    # Hills with a dip where the path meets the sky. Each column ends on its own
    # y so the range is not a ruler-straight horizon stroke.
    for x in range(w):
        xn = x / w
        far = hill_profile(xn, 1.15)
        near = hill_profile(xn + 0.22, 3.8)
        dip = math.exp(-((xn - 0.60) ** 2) / 0.055)
        jitter = (hash2(x, 17) - 0.5) * 7.0
        far_y = int(horizon - (26 + 64 * far) * (1.0 - 0.62 * dip) + jitter)
        near_y = int(horizon - (12 + 36 * near) * (1.0 - 0.40 * dip) + jitter * 0.45)
        far_face = 16 + int(20 * far)
        near_face = 12 + int(14 * near)
        for y in range(max(0, far_y), min(h, far_y + far_face)):
            fall = (y - far_y) / max(far_face, 1)
            fade = 1.0 - fall * fall
            shade = (0.12 + 0.08 * fall + 0.06 * fbm(xn * 8.0, y * 0.04, 2)) * fade
            shade *= 0.55 + 0.45 * (1.0 - dip * 0.7)
            if shade > values[y][x]:
                values[y][x] = shade
        for y in range(max(0, near_y), min(h, near_y + near_face)):
            fall = (y - near_y) / max(near_face, 1)
            fade = 1.0 - fall * fall
            shade = (0.18 + 0.08 * fall) * fade
            shade *= 0.60 + 0.40 * (1.0 - dip * 0.5)
            if shade > values[y][x]:
                values[y][x] = shade

    # --- Ground plane with a perspective winding road ---
    for y in range(horizon, h):
        v = (y - horizon) / max(h - horizon, 1)
        fog = clamp(1.0 - math.exp(-v * 4.2))
        cx = road_x(v)
        half = road_half(v)
        row = values[y]
        for x in range(w):
            xn = x / w
            dist = abs(xn - cx)

            ground_n = fbm(xn * 6.5 + v * 1.4, v * 8.0 + 3.0, 4)
            ridge = fbm(xn * 2.2, v * 3.5 + 1.0, 3)
            grass = 0.20 + 0.30 * ground_n + 0.12 * ridge + 0.18 * (v ** 1.5)

            if dist < half:
                u = dist / max(half, 1e-6)
                # One solid ribbon of gold, slightly darker at the rim.
                ink = 0.80 + 0.12 * (u ** 3)
            else:
                shoulder = math.exp(-((dist - half) ** 2) / (0.0022 + half * 0.014))
                ink = grass + 0.10 * shoulder

            ink *= fog
            ink *= clamp(v / 0.08)
            row[x] = clamp(max(row[x] * clamp(1.0 - v * 8.0), ink))

    # Cypress silhouettes along the path — original geometry, not photographs.
    tree_vs = [0.18, 0.24, 0.31, 0.38, 0.46, 0.55, 0.64, 0.74, 0.84, 0.94]
    for idx, v in enumerate(tree_vs):
        cx = road_x(v)
        half = road_half(v)
        side = -1.0 if idx % 2 == 0 else 1.0
        sx = (cx + side * (half * 1.85 + 0.018 + (idx % 3) * 0.01)) * w
        sy = horizon + v * (h - horizon)
        th = (58.0 + (idx % 3) * 18.0) * (0.18 + 0.82 * v)
        tw = th * 0.23
        if th < 8:
            continue
        top = int(sy - th)
        base = min(h - 1, int(sy + th * 0.05))
        for py in range(max(0, top), base + 1):
            t = (py - top) / max(th, 1)
            crown_half = tw * (0.08 + 0.92 * (t ** 1.45))
            trunk_half = max(1.2, tw * 0.10 * t)
            for px in range(max(0, int(sx - crown_half - 1)), min(w, int(sx + crown_half + 2))):
                dx = abs(px - sx)
                in_crown = dx <= crown_half and t < 0.90
                in_trunk = dx <= trunk_half and t >= 0.84
                if in_crown or in_trunk:
                    shade = (0.74 + 0.12 * t) * clamp((v - 0.10) / 0.16)
                    if shade > values[py][px]:
                        values[py][px] = shade

    return values


def dither_clustered(values: list[list[float]], cell: int = 4) -> list[list[int]]:
    """Round-dot clustered ordered dither (halftone screen at 22°)."""
    h = len(values)
    w = len(values[0])
    ang = math.radians(22.0)
    cos_a, sin_a = math.cos(ang), math.sin(ang)
    max_r = cell * 0.70
    out = [[0] * w for _ in range(h)]
    half = cell * 0.5
    for y in range(h):
        row_v = values[y]
        row_o = out[y]
        cy = (y % cell) + 0.5 - half
        for x in range(w):
            cx = (x % cell) + 0.5 - half
            rx = cx * cos_a - cy * sin_a
            ry = cx * sin_a + cy * cos_a
            dist = math.hypot(rx, ry)
            radius = (row_v[x] ** 0.86) * max_r
            row_o[x] = 1 if dist <= radius and row_v[x] > 0.012 else 0
    return out


def dither_bayer(values: list[list[float]]) -> list[list[int]]:
    h = len(values)
    w = len(values[0])
    n = 8
    scale = float(n * n)
    out = [[0] * w for _ in range(h)]
    for y in range(h):
        row_v = values[y]
        row_o = out[y]
        my = y % n
        for x in range(w):
            threshold = (BAYER8[my][x % n] + 0.5) / scale
            row_o[x] = 1 if row_v[x] > threshold else 0
    return out


def dither_fs(values: list[list[float]]) -> list[list[int]]:
    h = len(values)
    w = len(values[0])
    buf = [row[:] for row in values]
    out = [[0] * w for _ in range(h)]
    for y in range(h):
        row = buf[y]
        nxt = buf[y + 1] if y + 1 < h else None
        for x in range(w):
            old = clamp(row[x])
            new = 1.0 if old >= 0.5 else 0.0
            out[y][x] = 1 if new > 0.5 else 0
            err = old - new
            if x + 1 < w:
                row[x + 1] += err * 7 / 16
            if nxt is not None:
                if x > 0:
                    nxt[x - 1] += err * 3 / 16
                nxt[x] += err * 5 / 16
                if x + 1 < w:
                    nxt[x + 1] += err * 1 / 16
    return out


def write_png_indexed(path: str, bits: list[list[int]], palette: list[tuple[int, int, int]]) -> None:
    h = len(bits)
    w = len(bits[0])

    def chunk(tag: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    raw = bytearray()
    for row in bits:
        raw.append(0)  # filter None
        raw.extend(row)

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 3, 0, 0, 0)
    plte = b"".join(struct.pack("BBB", *c) for c in palette)
    idat = zlib.compress(bytes(raw), 9)

    png = b"".join(
        [
            b"\x89PNG\r\n\x1a\n",
            chunk(b"IHDR", ihdr),
            chunk(b"PLTE", plte),
            chunk(b"IDAT", idat),
            chunk(b"IEND", b""),
        ]
    )
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(png)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--method",
        choices=("clustered", "bayer", "fs"),
        default="clustered",
        help="Dither: clustered-dot halftone (default), Bayer 8x8, or Floyd–Steinberg",
    )
    parser.add_argument("--out", default=OUT)
    args = parser.parse_args()

    values = render_values(WIDTH, HEIGHT)
    if args.method == "bayer":
        bits = dither_bayer(values)
    elif args.method == "fs":
        bits = dither_fs(values)
    else:
        bits = dither_clustered(values, cell=4)

    write_png_indexed(args.out, bits, [WHITE, GOLD])
    size = os.path.getsize(args.out)
    print(f"Wrote {args.out} ({size} bytes, {WIDTH}x{HEIGHT}, method={args.method})")
    if size > 150_000:
        print("WARNING: asset is over 150 KB; re-run with a smaller canvas or clustered dither.")


if __name__ == "__main__":
    main()
