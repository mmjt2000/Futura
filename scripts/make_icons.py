"""Génère les icônes PWA (192 et 512 px) sans dépendance externe.

À relancer si l'identité visuelle change :

    python scripts/make_icons.py

Les fichiers sont écrits dans static/icons/.
"""
import os
import struct
import zlib

OUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "icons"
)

PINK = (244, 114, 182)
BLUE = (56, 189, 248)
WHITE = (255, 255, 255)


def rounded(x, y, size, radius):
    """Vrai si le pixel est dans le carré à coins arrondis."""
    if radius <= x < size - radius or radius <= y < size - radius:
        return True
    cx = radius if x < radius else size - radius - 1
    cy = radius if y < radius else size - radius - 1
    return (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2


def letter_f(x, y, size):
    """« F » construit avec trois rectangles, proportions relatives."""
    left = 0.30 * size
    right = 0.62 * size
    top = 0.26 * size
    bottom = 0.74 * size
    thickness = 0.10 * size
    bar_mid = 0.46 * size
    bar_mid_end = 0.56 * size

    vertical = left <= x <= left + thickness and top <= y <= bottom
    top_bar = left <= x <= right and top <= y <= top + thickness
    mid_bar = left <= x <= bar_mid_end and bar_mid <= y <= bar_mid + thickness
    return vertical or top_bar or mid_bar


def make_icon(size, path):
    radius = int(size * 0.18)
    rows = []
    for y in range(size):
        row = bytearray()
        row.append(0)  # filtre PNG « None »
        for x in range(size):
            if not rounded(x, y, size, radius):
                row.extend((0, 0, 0, 0))
                continue
            t = (x + y) / (2 * size)
            r = int(PINK[0] + (BLUE[0] - PINK[0]) * t)
            g = int(PINK[1] + (BLUE[1] - PINK[1]) * t)
            b = int(PINK[2] + (BLUE[2] - PINK[2]) * t)
            if letter_f(x, y, size):
                r, g, b = WHITE
            row.extend((r, g, b, 255))
        rows.append(bytes(row))

    raw = b"".join(rows)

    def chunk(tag, data):
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9))
    png += chunk(b"IEND", b"")

    with open(path, "wb") as f:
        f.write(png)
    return len(png)


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    for dimension in (192, 512):
        target = os.path.join(OUT_DIR, f"icon-{dimension}.png")
        written = make_icon(dimension, target)
        print(f"{target} ({written} octets)")
