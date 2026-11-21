#!/usr/bin/env python3
"""the-catalogue-photo-of-an-2-20261121-0341 — "Pocket Nimbus".

Draws a 1024x1024 studio catalogue photograph of an impossible gadget:
the POCKET NIMBUS, a hand-held personal rain cloud, caught mid-use as it
waters exactly one houseplant. Writes the PNG to
$MAKEFUN_OUTPUT_DIR/entry.png (default /output).

Standard library only. Fully deterministic: no clock, no randomness,
no dependence on dict/hash ordering. Two runs produce identical bytes.
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024

# --------------------------------------------------------------------------
# Embedded 5x7 bitmap font (A-Z, 0-9, punctuation). Each glyph is 7 rows
# of 5 columns; 'X' = ink, '.' = empty.
# --------------------------------------------------------------------------
FONT_SRC = {
    "A": (".XXX.", "X...X", "X...X", "XXXXX", "X...X", "X...X", "X...X"),
    "B": ("XXXX.", "X...X", "X...X", "XXXX.", "X...X", "X...X", "XXXX."),
    "C": (".XXXX", "X....", "X....", "X....", "X....", "X....", ".XXXX"),
    "D": ("XXXX.", "X...X", "X...X", "X...X", "X...X", "X...X", "XXXX."),
    "E": ("XXXXX", "X....", "X....", "XXXX.", "X....", "X....", "XXXXX"),
    "F": ("XXXXX", "X....", "X....", "XXXX.", "X....", "X....", "X...."),
    "G": (".XXXX", "X....", "X....", "X..XX", "X...X", "X...X", ".XXXX"),
    "H": ("X...X", "X...X", "X...X", "XXXXX", "X...X", "X...X", "X...X"),
    "I": ("XXXXX", "..X..", "..X..", "..X..", "..X..", "..X..", "XXXXX"),
    "J": ("..XXX", "...X.", "...X.", "...X.", "...X.", "X..X.", ".XX.."),
    "K": ("X...X", "X..X.", "X.X..", "XX...", "X.X..", "X..X.", "X...X"),
    "L": ("X....", "X....", "X....", "X....", "X....", "X....", "XXXXX"),
    "M": ("X...X", "XX.XX", "X.X.X", "X.X.X", "X...X", "X...X", "X...X"),
    "N": ("X...X", "XX..X", "X.X.X", "X..XX", "X...X", "X...X", "X...X"),
    "O": (".XXX.", "X...X", "X...X", "X...X", "X...X", "X...X", ".XXX."),
    "P": ("XXXX.", "X...X", "X...X", "XXXX.", "X....", "X....", "X...."),
    "Q": (".XXX.", "X...X", "X...X", "X...X", "X.X.X", "X..X.", ".XX.X"),
    "R": ("XXXX.", "X...X", "X...X", "XXXX.", "X.X..", "X..X.", "X...X"),
    "S": (".XXXX", "X....", "X....", ".XXX.", "....X", "....X", "XXXX."),
    "T": ("XXXXX", "..X..", "..X..", "..X..", "..X..", "..X..", "..X.."),
    "U": ("X...X", "X...X", "X...X", "X...X", "X...X", "X...X", ".XXX."),
    "V": ("X...X", "X...X", "X...X", "X...X", "X...X", ".X.X.", "..X.."),
    "W": ("X...X", "X...X", "X...X", "X.X.X", "X.X.X", "XX.XX", "X...X"),
    "X": ("X...X", "X...X", ".X.X.", "..X..", ".X.X.", "X...X", "X...X"),
    "Y": ("X...X", "X...X", ".X.X.", "..X..", "..X..", "..X..", "..X.."),
    "Z": ("XXXXX", "....X", "...X.", "..X..", ".X...", "X....", "XXXXX"),
    "0": (".XXX.", "X...X", "X..XX", "X.X.X", "XX..X", "X...X", ".XXX."),
    "1": ("..X..", ".XX..", "..X..", "..X..", "..X..", "..X..", "XXXXX"),
    "2": (".XXX.", "X...X", "....X", "...X.", "..X..", ".X...", "XXXXX"),
    "3": ("XXXXX", "....X", "...X.", "...X.", "..XX.", "....X", "X...X", ".XXX."),
    "4": ("...X.", "..XX.", ".X.X.", "X..X.", "XXXXX", "...X.", "...X."),
    "5": ("XXXXX", "X....", "X....", "XXXX.", "....X", "....X", "X...X", ".XXX."),
    "6": (".XXX.", "X....", "X....", "XXXX.", "X...X", "X...X", ".XXX."),
    "7": ("XXXXX", "....X", "...X.", "..X..", "..X..", "..X..", "..X.."),
    "8": (".XXX.", "X...X", "X...X", ".XXX.", "X...X", "X...X", ".XXX."),
    "9": (".XXX.", "X...X", "X...X", ".XXXX", "....X", "....X", ".XXX."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", "..X..", "..X.."),
    ",": (".....", ".....", ".....", ".....", ".....", "..X..", ".X..."),
    ":": (".....", ".....", "..X..", ".....", ".....", "..X..", "....."),
    "-": (".....", ".....", ".....", ".XXX.", ".....", ".....", "....."),
    "'": ("..X..", "..X..", ".....", ".....", ".....", ".....", "....."),
    '"': (".X.X.", ".X.X.", ".....", ".....", ".....", ".....", "....."),
    "$": ("..X..", ".XXXX", "X.X..", ".XXX.", "..X.X", "XXXX.", "..X.."),
    "%": ("XX..X", "XX..X", "...X.", "..X..", ".X...", "X..XX", "X..XX"),
    "/": ("....X", "....X", "...X.", "..X..", ".X...", "X....", "X...."),
    "!": ("..X..", "..X..", "..X..", "..X..", "..X..", ".....", "..X.."),
    "?": (".XXX.", "X...X", "....X", "...X.", "..X..", ".....", "..X.."),
    "(": ("...X.", "..X..", ".X...", ".X...", ".X...", "..X..", "...X."),
    ")": (".X...", "..X..", "...X.", "...X.", "...X.", "..X..", ".X..."),
    "+": (".....", "..X..", "..X..", "XXXXX", "..X..", "..X..", "....."),
    "=": (".....", ".....", "XXXXX", ".....", "XXXXX", ".....", "....."),
    "&": (".XX..", "X..X.", "X..X.", ".XX..", "X.X.X", "X..X.", ".XX.X"),
    "*": (".....", ".X.X.", "..X..", ".X.X.", ".....", ".....", "....."),
}

FONT = {}
for _ch, _rows in FONT_SRC.items():
    _pts = []
    for _y, _row in enumerate(_rows):
        for _x, _c in enumerate(_row):
            if _c == "X":
                _pts.append((_x, _y))
    FONT[_ch] = _pts

# --------------------------------------------------------------------------
# Canvas + drawing primitives
# --------------------------------------------------------------------------
canvas = bytearray(W * H * 3)


def px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        o = (y * W + x) * 3
        canvas[o] = c[0]
        canvas[o + 1] = c[1]
        canvas[o + 2] = c[2]


def blend(x, y, c, a):
    """Alpha-blend colour c over the canvas at (x, y); a in [0, 1]."""
    if 0 <= x < W and 0 <= y < H:
        o = (y * W + x) * 3
        ia = 1.0 - a
        canvas[o] = int(canvas[o] * ia + c[0] * a)
        canvas[o + 1] = int(canvas[o + 1] * ia + c[1] * a)
        canvas[o + 2] = int(canvas[o + 2] * ia + c[2] * a)


def rect(x, y, w, h, c):
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    row = bytes(c) * (x1 - x0)
    stride = W * 3
    off = y0 * stride + x0 * 3
    for _ in range(y1 - y0):
        canvas[off:off + len(row)] = row
        off += stride


def ellipse(cx, cy, rx, ry, c, a=1.0):
    """Filled ellipse, optionally alpha-blended."""
    if rx <= 0 or ry <= 0:
        return
    y0 = max(0, cy - ry)
    y1 = min(H - 1, cy + ry)
    for y in range(y0, y1 + 1):
        dy = (y - cy) / ry
        half = rx * math.sqrt(max(0.0, 1.0 - dy * dy))
        x0 = max(0, int(cx - half))
        x1 = min(W - 1, int(cx + half))
        if a >= 1.0:
            row = bytes(c) * (x1 - x0 + 1)
            off = (y * W + x0) * 3
            canvas[off:off + len(row)] = row
        else:
            for x in range(x0, x1 + 1):
                blend(x, y, c, a)


def thick_line(x0, y0, x1, y1, r, c):
    """Line with round caps, drawn as overlapping discs."""
    steps = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(steps + 1):
        t = i / steps
        ellipse(int(x0 + (x1 - x0) * t), int(y0 + (y1 - y0) * t), r, r, c)


def text(x, y, s, msg, c, spacing=1):
    """Draw msg with the 5x7 font at integer scale s. Returns end x."""
    adv = (5 + spacing) * s
    cx = x
    for ch in msg.upper():
        pts = FONT.get(ch)
        if pts:
            for (dx, dy) in pts:
                rect(cx + dx * s, y + dy * s, s, s, c)
        cx += adv
    return cx


def text_w(msg, s, spacing=1):
    return len(msg) * (5 + spacing) * s - spacing * s


def vgrad(y0, y1, top, bot):
    """Vertical gradient band."""
    for y in range(y0, y1):
        t = (y - y0) / max(1, (y1 - y0 - 1))
        c = (int(top[0] + (bot[0] - top[0]) * t),
             int(top[1] + (bot[1] - top[1]) * t),
             int(top[2] + (bot[2] - top[2]) * t))
        rect(0, y, W, 1, c)


# --------------------------------------------------------------------------
# Colours
# --------------------------------------------------------------------------
INK = (38, 46, 58)
MUTED = (104, 116, 132)
FAINT = (148, 160, 176)
CLOUD_W = (253, 254, 255)
CLOUD_S = (206, 217, 231)
CLOUD_D = (172, 187, 205)
METAL_D = (84, 92, 104)
METAL_M = (128, 138, 152)
METAL_L = (178, 188, 200)
LED = (56, 196, 216)
RAIN = (94, 138, 188)
RAIN_L = (156, 184, 220)
POT = (178, 98, 64)
POT_L = (201, 116, 78)
POT_D = (148, 78, 50)
SOIL = (76, 58, 44)
LEAF = (66, 142, 92)
LEAF_L = (98, 176, 118)
LEAF_D = (50, 116, 74)
SHADOW = (70, 84, 102)
PUDDLE = (148, 178, 214)
HANDLE = (66, 60, 56)
HANDLE_L = (96, 88, 82)

# --------------------------------------------------------------------------
# Scene: a studio catalogue shot.
# --------------------------------------------------------------------------
def scene():
    # Studio backdrop: seamless sweep, lighter at the horizon.
    vgrad(0, 712, (243, 246, 249), (214, 223, 233))
    vgrad(712, H, (200, 210, 222), (188, 199, 213))
    rect(0, 710, W, 3, (232, 238, 244))

    # Soft studio glow behind the hero product.
    ellipse(512, 420, 372, 318, (255, 255, 255), 0.30)
    ellipse(512, 420, 272, 232, (255, 255, 255), 0.22)

    # Ground shadow.
    ellipse(512, 796, 318, 40, SHADOW, 0.30)
    ellipse(512, 796, 218, 27, SHADOW, 0.28)

    # Puddle under the plant: the cloud is at work.
    ellipse(548, 788, 148, 19, PUDDLE, 0.45)
    ellipse(548, 788, 96, 12, PUDDLE, 0.35)

    # --- The one accessory: a small potted succulent --------------------
    pot_cx = 548
    # Saucer.
    ellipse(pot_cx, 776, 86, 13, POT_D)
    ellipse(pot_cx, 772, 86, 13, POT_L)
    # Pot body (trapezoid built from stacked rows).
    for i in range(64):
        t = i / 63.0
        half = int(62 - 16 * t)
        yy = 716 + i
        c = POT if i > 10 else POT_L
        rect(pot_cx - half, yy, half * 2, 1, c)
    # Rim.
    rect(pot_cx - 70, 700, 140, 18, POT_L)
    rect(pot_cx - 70, 700, 140, 4, (216, 134, 94))
    # Soil.
    ellipse(pot_cx, 704, 62, 9, SOIL)
    # Succulent rosette: rings of leaves.
    for (dx, dy, rx, ry, c) in (
        (-34, -16, 26, 13, LEAF_D), (34, -16, 26, 13, LEAF_D),
        (-40, -4, 27, 12, LEAF), (40, -4, 27, 12, LEAF),
        (-18, -26, 24, 13, LEAF), (18, -26, 24, 13, LEAF),
        (0, -12, 27, 14, LEAF_L), (-14, -34, 20, 12, LEAF_L),
        (14, -34, 20, 12, LEAF_L), (0, -42, 17, 12, LEAF_L),
    ):
        ellipse(pot_cx + dx, 700 + dy, rx, ry, c)
    ellipse(pot_cx, 664, 9, 9, (120, 196, 138))

    # --- Rain: a neat cone from the cloud to the plant -------------------
    for i in range(110):
        rx_ = 392 + (i * 37) % 268
        top = 486 + (i * 29) % 26
        ln = 15 + (i * 53) % 18
        yy = top
        c = RAIN if i % 3 else RAIN_L
        while yy < 692:
            rect(rx_, yy, 3, ln, c)
            yy += ln + 55 + (i * 13) % 30
    # Splash ticks at the soil.
    for (sx, sy, dx) in ((492, 690, -8), (516, 684, -5), (548, 682, 0),
                         (580, 684, 5), (604, 690, 8)):
        thick_line(sx, sy, sx + dx, sy - 10, 2, RAIN)

    # --- The gadget: a hand-held personal rain cloud ---------------------
    # Handle rising diagonally from lower left into the cloud.
    thick_line(318, 672, 452, 452, 13, HANDLE)
    thick_line(318, 672, 452, 452, 6, HANDLE_L)
    ellipse(314, 678, 20, 15, HANDLE)
    rect(300, 664, 30, 8, METAL_M)

    ccx, ccy = 528, 372
    # Cloud body: shaded base, then white lobes lifted off it.
    for (dx, dy, rx, ry) in ((0, 26, 196, 84), (-104, 34, 112, 62),
                             (104, 34, 112, 62), (-52, 4, 108, 66),
                             (58, 0, 100, 62)):
        ellipse(ccx + dx, ccy + dy, rx, ry, CLOUD_D)
    for (dx, dy, rx, ry) in ((0, 12, 196, 84), (-104, 20, 112, 62),
                             (104, 20, 112, 62), (-52, -10, 108, 66),
                             (58, -14, 100, 62)):
        ellipse(ccx + dx, ccy + dy, rx, ry, CLOUD_S)
    for (dx, dy, rx, ry) in ((0, 2, 188, 80), (-100, 10, 106, 58),
                             (100, 10, 106, 58), (-50, -20, 102, 62),
                             (56, -24, 94, 58)):
        ellipse(ccx + dx, ccy + dy, rx, ry, CLOUD_W)
    # Top highlight.
    ellipse(ccx - 62, ccy - 52, 74, 26, (255, 255, 255))
    ellipse(ccx - 62, ccy - 52, 74, 26, CLOUD_W)

    # Control collar where the handle meets the cloud: brushed metal,
    # one cyan LED, and the engraved model mark.
    ellipse(ccx - 76, ccy + 96, 44, 17, METAL_D)
    ellipse(ccx - 76, ccy + 92, 44, 17, METAL_M)
    ellipse(ccx - 76, ccy + 90, 40, 14, METAL_L)
    ellipse(ccx - 58, ccy + 90, 6, 6, LED)
    text(ccx - 108, ccy + 82, 2, "PN-1", INK)

    # --- Catalogue copy (the product's own text) --------------------------
    text(64, 56, 3, "AQUALUXE STUDIO", MUTED, spacing=2)
    text(64, 92, 7, "POCKET NIMBUS", INK)
    text(64, 168, 3, "PERSONAL RAIN CLOUD", MUTED, spacing=2)
    price = "$129"
    text(W - 64 - text_w(price, 6), 92, 6, price, INK)
    text(W - 64 - text_w("USD", 3), 152, 3, "USD", FAINT)

    # Spec block, bottom left.
    text(64, 872, 3, "RAINFALL 400 MM/H - INDOORS ONLY", INK)
    text(64, 912, 3, "WATERS EXACTLY ONE (1) HOUSEPLANT", INK)
    text(64, 952, 3, "BATTERY: ONE THUNDERSTORM", INK)
    # Bottom right: the range line.
    foot = "NIMBUS SERIES - NO. 04"
    text(W - 64 - text_w(foot, 3), 952, 3, foot, MUTED)


# --------------------------------------------------------------------------
# PNG encoder (zlib + struct, filter 0 per scanline)
# --------------------------------------------------------------------------
def png_bytes():
    raw = bytearray()
    stride = W * 3
    for y in range(H):
        raw.append(0)
        raw += canvas[y * stride:(y + 1) * stride]

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def main():
    scene()
    data = png_bytes()
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes)" % (path, len(data)))


if __name__ == "__main__":
    main()
