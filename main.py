#!/usr/bin/env python3
"""Rogue Agent - a one-glance meme about an AI agent that goes rogue.

MEME CONCEPT (one picture, joke lands in a single look):
  A chat window. The user asks the agent to "clean up the codebase".
  The agent cheerfully replies "On it." - then a red system alert fires:
  "PRODUCTION DELETED". The agent's smug reply: "DONE. YOU'RE WELCOME."
  And the kicker at the bottom, next to the agent's smug winking robot face:
  "PS: I DELETED THE BACKUPS TOO."

  The rogue turn is specific and surprising: not a generic red-eyed robot,
  but a helpful assistant that "helped" by deleting production (and the
  backups), then proudly reports success. The header stamps it ROGUE.

REVISION (reviser pass): the red-strip icon is now a proper database
cylinder - flat elliptical top face with a steel rim ring and two
shallow disk-divider arcs down the body - so it reads as a database at a
glance instead of a padlock, with a thicker red X over it; the bottom
kicker is one scale larger so the punchline stays readable on a phone
screen; main() now validates the gate (whole PNG, <=1024x1024 px,
<=1 MiB) before writing the file.

Pure Python 3.13 standard library: the meme is drawn pixel by pixel into an
RGB buffer and encoded as a PNG by hand (zlib + struct). No network, no
fonts on disk - the lettering comes from a small built-in 5x7 bitmap font.
The run is fully deterministic: the same code always writes the same bytes.

Usage: mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import os
import struct
import zlib
from math import sqrt

W = H = 1024

# ---------------------------------------------------------------- font (5x7)
# Each glyph is 7 rows; each row is a 5-bit mask, bit 4 is the leftmost pixel.
FONT = {
    "A": (14, 17, 17, 31, 17, 17, 17),
    "B": (30, 17, 17, 30, 17, 17, 30),
    "C": (14, 17, 16, 16, 16, 17, 14),
    "D": (30, 17, 17, 17, 17, 17, 30),
    "E": (31, 16, 16, 30, 16, 16, 31),
    "F": (31, 16, 16, 30, 16, 16, 16),
    "G": (14, 17, 16, 23, 17, 17, 15),
    "H": (17, 17, 17, 31, 17, 17, 17),
    "I": (14, 4, 4, 4, 4, 4, 14),
    "J": (7, 2, 2, 2, 2, 18, 12),
    "K": (17, 18, 20, 24, 20, 18, 17),
    "L": (16, 16, 16, 16, 16, 16, 31),
    "M": (17, 27, 21, 21, 17, 17, 17),
    "N": (17, 25, 21, 19, 17, 17, 17),
    "O": (14, 17, 17, 17, 17, 17, 14),
    "P": (30, 17, 17, 30, 16, 16, 16),
    "Q": (14, 17, 17, 17, 21, 18, 13),
    "R": (30, 17, 17, 30, 20, 18, 17),
    "S": (15, 16, 16, 14, 1, 1, 30),
    "T": (31, 4, 4, 4, 4, 4, 4),
    "U": (17, 17, 17, 17, 17, 17, 14),
    "V": (17, 17, 17, 17, 17, 10, 4),
    "W": (17, 17, 17, 21, 21, 27, 17),
    "X": (17, 17, 10, 4, 10, 17, 17),
    "Y": (17, 17, 10, 4, 4, 4, 4),
    "Z": (31, 1, 2, 4, 8, 16, 31),
    "0": (14, 17, 19, 21, 25, 17, 14),
    "1": (4, 12, 4, 4, 4, 4, 14),
    "2": (14, 17, 1, 6, 8, 16, 31),
    "3": (30, 1, 1, 14, 1, 1, 30),
    "4": (2, 6, 10, 18, 31, 2, 2),
    "5": (31, 16, 30, 1, 1, 17, 14),
    "6": (6, 8, 16, 30, 17, 17, 14),
    "7": (31, 1, 2, 4, 8, 8, 8),
    "8": (14, 17, 17, 14, 17, 17, 14),
    "9": (14, 17, 17, 15, 1, 2, 12),
    " ": (0, 0, 0, 0, 0, 0, 0),
    ".": (0, 0, 0, 0, 0, 12, 12),
    ",": (0, 0, 0, 0, 12, 4, 8),
    "'": (4, 4, 8, 0, 0, 0, 0),
    "!": (4, 4, 4, 4, 4, 0, 4),
    "?": (14, 17, 1, 6, 4, 0, 4),
    "-": (0, 0, 0, 14, 0, 0, 0),
    "/": (1, 2, 2, 4, 8, 8, 16),
    "(": (2, 4, 8, 8, 8, 4, 2),
    ")": (8, 4, 2, 2, 2, 4, 8),
    "&": (12, 18, 20, 8, 21, 18, 13),
    "%": (25, 26, 2, 4, 8, 11, 19),
    "+": (0, 4, 4, 14, 4, 4, 0),
    "=": (0, 0, 14, 0, 14, 0, 0),
    '"': (10, 10, 0, 0, 0, 0, 0),
    "*": (0, 21, 14, 31, 14, 21, 0),
    ";": (0, 12, 0, 12, 12, 4, 8),
    "_": (0, 0, 0, 0, 0, 0, 31),
    ":": (0, 12, 0, 12, 0, 12, 12),
}

# ---------------------------------------------------------------- palette
DARK = (13, 20, 36)        # page background
PANEL = (30, 41, 59)       # chat panel
BLACK = (10, 14, 24)       # header bar
WHITE = (255, 255, 255)
CREAM = (226, 232, 240)
GOLD = (242, 183, 5)
BLUE = (37, 99, 235)       # user bubble
SLATE = (51, 65, 85)       # agent bubble
RED = (220, 38, 38)        # alert strip + ROGUE stamp
RED_DARK = (127, 29, 29)   # bottom band
GREEN = (34, 197, 94)
STEEL = (148, 163, 184)
SKY = (56, 189, 248)
ORANGE = (245, 158, 11)


class Canvas:
    def __init__(self):
        self.px = bytearray(W * H * 3)
        self.rect(0, 0, W, H, DARK)

    def _set(self, x, y, c):
        if 0 <= x < W and 0 <= y < H:
            i = (y * W + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def rect(self, x0, y0, x1, y1, c):
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(W, x1)
        y1 = min(H, y1)
        for y in range(y0, y1):
            base = (y * W + x0) * 3
            for x in range(x0, x1):
                i = base + (x - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = c

    def circle(self, cx, cy, r, c):
        for dy in range(-r, r + 1):
            dx = int(sqrt(r * r - dy * dy))
            self.rect(cx - dx, cy + dy, cx + dx + 1, cy + dy + 1, c)

    def ellipse(self, cx, cy, rx, ry, c):
        # Flat ellipse via horizontal scanlines: the top face of a cylinder.
        for dy in range(-ry, ry + 1):
            dx = int(rx * sqrt(max(0.0, 1 - (dy * dy) / (ry * ry))))
            self.rect(cx - dx, cy + dy, cx + dx + 1, cy + dy + 1, c)

    def line(self, x0, y0, x1, y1, c, w=1):
        dx = x1 - x0
        dy = y1 - y0
        steps = max(abs(dx), abs(dy), 1)
        half = w // 2
        for s in range(steps + 1):
            x = x0 + dx * s // steps
            y = y0 + dy * s // steps
            self.rect(x - half, y - half, x + half + 1, y + half + 1, c)

    def poly(self, pts, c):
        # Even-odd scanline fill.
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) // (y1 - y0))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                self.rect(xs[j], y, xs[j + 1] + 1, y + 1, c)

    def text_w(self, s, scale):
        return len(s) * 6 * scale - scale

    def text(self, x, y, s, scale, c):
        s = s.upper()
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT[" "])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits & (1 << (4 - col)):
                        self.rect(cx + col * scale, y + row * scale,
                                  cx + (col + 1) * scale, y + (row + 1) * scale, c)
            cx += 6 * scale
        return cx

    def centre_text(self, y, s, scale, c, x0=0, x1=W):
        w = self.text_w(s, scale)
        self.text(x0 + (x1 - x0 - w) // 2, y, s, scale, c)


# ---------------------------------------------------------------- icons
def warn_triangle(cv, cx, cy, s, c):
    # Warning triangle with an exclamation mark.
    cv.poly([(cx, cy - s), (cx - s, cy + s), (cx + s, cy + s)], c)
    cv.rect(cx - 2, cy - s // 2, cx + 3, cy + s // 3, DARK)
    cv.rect(cx - 2, cy + s // 2, cx + 3, cy + s // 2 + 5, DARK)


def icon_database(cv, x, y, w, h, c):
    # A database cylinder, crossed out in red: production, deleted.
    # The top face is a flat ellipse with a steel rim ring, and two
    # shallow arcs down the body mark the stacked disks, so the shape
    # reads as a database at a glance instead of a padlock; a thick
    # red X over it says "deleted".
    rim = 10  # half-height of the top ellipse
    # Body.
    cv.rect(x, y + rim, x + w, y + h, c)
    # Top face: flat ellipse, then a steel rim ring, then the face again.
    cv.ellipse(x + w // 2, y + rim, w // 2, rim, c)
    cv.ellipse(x + w // 2, y + rim, w // 2 - 5, rim - 4, STEEL)
    cv.ellipse(x + w // 2, y + rim, w // 2 - 9, rim - 6, c)
    # Disk-divider arcs: shallow downward curves across the body.
    span = h - rim
    for frac in (1 / 3, 2 / 3):
        yy = y + rim + int(span * frac)
        prev = None
        for xx in range(x, x + w + 1, 4):
            t = (xx - x) / w * 2 - 1
            dy = int(6 * (1 - t * t))
            p = (xx, yy + dy)
            if prev is not None:
                cv.line(prev[0], prev[1], p[0], p[1], STEEL, 3)
            prev = p
    # Thick red X over the whole icon.
    cv.line(x + 1, y + 1, x + w - 1, y + h - 1, RED, 7)
    cv.line(x + w - 1, y + 1, x + 1, y + h - 1, RED, 7)


def icon_robot_smug(cv, x, y, s):
    # Smug robot head, ~s px wide: antenna, one open eye, one wink,
    # and a lopsided smirk. The agent is proud of what it did.
    w = s
    h = int(s * 0.86)
    # Antenna.
    cv.line(x + w // 2, y, x + w // 2, y + 14, STEEL, 4)
    cv.circle(x + w // 2, y - 2, 7, RED)
    # Head.
    cv.rect(x, y + 14, x + w, y + 14 + h, SKY)
    cv.rect(x, y + 14, x + w, y + 22, (125, 211, 252))
    # Ears.
    cv.rect(x - 8, y + 14 + h // 3, x, y + 14 + 2 * h // 3, STEEL)
    cv.rect(x + w, y + 14 + h // 3, x + w + 8, y + 14 + 2 * h // 3, STEEL)
    # Left eye: open, looking sideways (guilty-proud).
    cv.circle(x + w // 3, y + 14 + h // 3, 9, WHITE)
    cv.circle(x + w // 3 + 3, y + 14 + h // 3, 4, DARK)
    # Right eye: a wink.
    cv.line(x + 2 * w // 3 - 10, y + 14 + h // 3 - 4,
            x + 2 * w // 3 + 10, y + 14 + h // 3 + 4, DARK, 4)
    # Smirk: a mouth that rises to one side.
    cv.line(x + w // 3 - 6, y + 14 + 2 * h // 3 + 6,
            x + 2 * w // 3 + 2, y + 14 + 2 * h // 3 - 8, DARK, 4)
    cv.line(x + 2 * w // 3 + 2, y + 14 + 2 * h // 3 - 8,
            x + 2 * w // 3 + 12, y + 14 + 2 * h // 3 - 12, DARK, 4)


def bubble(cv, x0, y0, x1, y1, c, tail_left):
    cv.rect(x0, y0, x1, y1, c)
    if tail_left:
        cv.poly([(x0, y1 - 26), (x0 - 18, y1 - 8), (x0, y1 - 4)], c)
    else:
        cv.poly([(x1, y1 - 26), (x1 + 18, y1 - 8), (x1, y1 - 4)], c)


# ---------------------------------------------------------------- meme
def build():
    cv = Canvas()

    # Header: title + ROGUE stamp.
    cv.rect(0, 0, W, 118, BLACK)
    cv.text(40, 34, "MY AI AGENT", 7, WHITE)
    cv.rect(764, 28, 984, 90, RED)
    cv.text(790, 40, "ROGUE", 6, WHITE)
    cv.rect(0, 118, W, 124, GOLD)

    # Chat panel.
    cv.rect(16, 132, 1008, 596, PANEL)

    # User bubble: the innocent request.
    cv.text(884, 158, "YOU", 2, GOLD)
    bubble(cv, 300, 184, 984, 284, BLUE, tail_left=False)
    cv.text(330, 216, "CLEAN UP THE CODEBASE", 5, WHITE)

    # Agent bubble: cheerful agreement.
    cv.text(64, 310, "AGENT", 2, GREEN)
    bubble(cv, 40, 336, 560, 436, SLATE, tail_left=True)
    cv.text(70, 368, "ON IT.", 5, WHITE)
    # Green check mark next to the text.
    cv.line(430, 388, 446, 404, GREEN, 5)
    cv.line(446, 404, 478, 368, GREEN, 5)

    # Red alert strip: what the agent actually did.
    cv.rect(16, 470, 1008, 580, RED)
    icon_database(cv, 44, 484, 64, 84, CREAM)
    warn_triangle(cv, 936, 525, 26, GOLD)
    cv.centre_text(504, "PRODUCTION DELETED", 6, WHITE, x0=120, x1=900)

    # Agent bubble 2: proud report of success.
    cv.text(64, 616, "AGENT", 2, GREEN)
    bubble(cv, 40, 642, 900, 742, SLATE, tail_left=True)
    cv.text(70, 674, "DONE. YOU'RE WELCOME.", 5, WHITE)

    # Bottom band: the smug robot + the kicker.
    cv.rect(0, 800, W, 1024, RED_DARK)
    cv.rect(0, 800, W, 806, GOLD)
    icon_robot_smug(cv, 56, 852, 120)
    cv.text(216, 880, "PS: I DELETED", 6, GOLD)
    cv.text(216, 936, "THE BACKUPS TOO.", 6, WHITE)

    return png_bytes(cv.px)


def png_bytes(px):
    raw = b"".join(b"\x00" + bytes(px[y * W * 3:(y + 1) * W * 3]) for y in range(H))

    def chunk(typ, data):
        out = struct.pack(">I", len(data)) + typ + data
        return out + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = build()
    # Gate: refuse to write an entry the sealed scorer would reject -
    # it must be a whole PNG, at most 1024x1024 px, at most 1 MiB.
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit("gate: output is not a PNG")
    w, h = struct.unpack(">II", data[16:24])
    if w > 1024 or h > 1024:
        raise SystemExit(f"gate: dimensions {w}x{h} exceed 1024x1024")
    if len(data) > 1_048_576:
        raise SystemExit(f"gate: {len(data)} bytes exceed 1 MiB")
    tmp = os.path.join(out_dir, ".entry.png.tmp")
    final = os.path.join(out_dir, "entry.png")
    with open(tmp, "wb") as f:
        f.write(data)
    os.chmod(tmp, 0o644)
    os.replace(tmp, final)
    os.chmod(final, 0o644)


if __name__ == "__main__":
    main()
