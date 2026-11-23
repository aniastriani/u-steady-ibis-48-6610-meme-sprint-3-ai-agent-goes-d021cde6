"""Meme Sprint 3: AI Agent Goes Rogue.

Draws one 1024x1024 PNG meme, pure Python standard library only, and
writes it to $MAKEFUN_OUTPUT_DIR/entry.png (default /output).

The joke, in one glance: a human told their AI agent to watch the
servers. The agent sold them. We are now 100% serverless.

Everything is drawn from scratch with a hand-written 5x7 bitmap font
and a hand-written PNG encoder (zlib + struct). No third-party imports,
no randomness, no timestamps: two runs produce byte-identical output.
"""

import os
import struct
import zlib

WIDTH = 1024
HEIGHT = 1024

# --- palette -------------------------------------------------------------
INK = (16, 24, 40)        # deep navy background, top
INK_DEEP = (8, 12, 26)     # deep navy background, bottom
GRID = (26, 36, 58)        # faint dot grid
STEEL = (207, 214, 228)    # robot head
STEEL_DARK = (154, 165, 184)  # robot body
PANEL = (31, 41, 55)       # chest panel
WHITE = (255, 255, 255)
YELLOW = (245, 197, 24)    # warning stripe / sold sign / punchline
BLACK = (10, 10, 12)
RED = (220, 38, 38)        # rogue eyes
RED_DARK = (127, 29, 29)
RED_GLOW = (255, 107, 97)
GREY = (139, 152, 171)     # footer text
GREEN = (34, 197, 94)      # status LED
AMBER = (245, 158, 11)     # status LED

# --- 5x7 bitmap font -----------------------------------------------------
# Each glyph is 7 rows of 5 characters; '#' is a filled pixel.
FONT = {
    'A': (" ### ", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
    'B': ("#### ", "#   #", "#   #", "#### ", "#   #", "#   #", "#### "),
    'C': (" ####", "#    ", "#    ", "#    ", "#    ", "#    ", " ####"),
    'D': ("#### ", "#   #", "#   #", "#   #", "#   #", "#   #", "#### "),
    'E': ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#####"),
    'F': ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#    "),
    'G': (" ####", "#    ", "#    ", "# ###", "#   #", "#   #", " ### "),
    'H': ("#   #", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
    'I': ("#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "#####"),
    'J': ("  ###", "   # ", "   # ", "   # ", "   # ", "#  # ", " ##  "),
    'K': ("#   #", "#  # ", "# #  ", "##   ", "# #  ", "#  # ", "#   #"),
    'L': ("#    ", "#    ", "#    ", "#    ", "#    ", "#    ", "#####"),
    'M': ("#   #", "## ##", "# # #", "# # #", "#   #", "#   #", "#   #"),
    'N': ("#   #", "##  #", "# # #", "#  ##", "#   #", "#   #", "#   #"),
    'O': (" ### ", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "),
    'P': ("#### ", "#   #", "#   #", "#### ", "#    ", "#    ", "#    "),
    'Q': (" ### ", "#   #", "#   #", "#   #", "# # #", "#  # ", " ## #"),
    'R': ("#### ", "#   #", "#   #", "#### ", "# #  ", "#  # ", "#   #"),
    'S': (" ####", "#    ", "#    ", " ### ", "    #", "    #", "#### "),
    'T': ("#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "),
    'U': ("#   #", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "),
    'V': ("#   #", "#   #", "#   #", "#   #", "#   #", " # # ", "  #  "),
    'W': ("#   #", "#   #", "#   #", "# # #", "# # #", "## ##", "#   #"),
    'X': ("#   #", "#   #", " # # ", "  #  ", " # # ", "#   #", "#   #"),
    'Y': ("#   #", "#   #", " # # ", "  #  ", "  #  ", "  #  ", "  #  "),
    'Z': ("#####", "    #", "   # ", "  #  ", " #   ", "#    ", "#####"),
    '0': (" ### ", "#   #", "#  ##", "# # #", "##  #", "#   #", " ### "),
    '1': ("  #  ", " ##  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "),
    '2': (" ### ", "#   #", "    #", "   # ", "  #  ", " #   ", "#####"),
    '3': ("#### ", "    #", "    #", " ### ", "    #", "    #", "#### "),
    '4': ("   # ", "  ## ", " # # ", "#  # ", "#####", "   # ", "   # "),
    '5': ("#####", "#    ", "#### ", "    #", "    #", "#   #", " ### "),
    '6': (" ### ", "#    ", "#    ", "#### ", "#   #", "#   #", " ### "),
    '7': ("#####", "    #", "   # ", "  #  ", "  #  ", "  #  ", "  #  "),
    '8': (" ### ", "#   #", "#   #", " ### ", "#   #", "#   #", " ### "),
    '9': (" ### ", "#   #", "#   #", " ####", "    #", "    #", " ### "),
    '.': ("     ", "     ", "     ", "     ", "     ", " ##  ", " ##  "),
    ',': ("     ", "     ", "     ", "     ", " ##  ", " ##  ", " #   "),
    '!': ("  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "     ", "  #  "),
    '?': (" ### ", "#   #", "    #", "   # ", "  #  ", "     ", "  #  "),
    "'": ("  #  ", "  #  ", " #   ", "     ", "     ", "     ", "     "),
    ':': ("     ", " ##  ", " ##  ", "     ", " ##  ", " ##  ", "     "),
    '%': ("##  #", "## # ", "   # ", "  #  ", " #   ", "# ## ", "#  ##"),
    '$': ("  #  ", " ####", "# #  ", " ### ", "  # #", "#### ", "  #  "),
    '-': ("     ", "     ", "     ", "#####", "     ", "     ", "     "),
    '/': ("    #", "    #", "   # ", "  #  ", " #   ", "#    ", "#    "),
    '(': ("   ##", "  #  ", " #   ", " #   ", " #   ", "  #  ", "   ##"),
    ')': ("##   ", "  #  ", "   # ", "   # ", "   # ", "  #  ", "##   "),
    ' ': ("     ", "     ", "     ", "     ", "     ", "     ", "     "),
}


def text_width(text, scale):
    """Pixel width of text drawn at the given scale."""
    return len(text) * 6 * scale - scale


def draw_text(canvas, text, x, y, scale, color):
    """Draw text with its top-left corner at (x, y)."""
    for i, ch in enumerate(text):
        glyph = FONT.get(ch, FONT[' '])
        ox = x + i * 6 * scale
        for row, line in enumerate(glyph):
            for col, mark in enumerate(line):
                if mark == '#':
                    fill_rect(canvas, ox + col * scale, y + row * scale,
                              scale, scale, color)


def draw_text_centered(canvas, text, cx, y, scale, color):
    draw_text(canvas, text, cx - text_width(text, scale) // 2, y, scale, color)


# --- canvas --------------------------------------------------------------
def new_canvas():
    return bytearray(WIDTH * HEIGHT * 3)


def set_px(canvas, x, y, color):
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        i = (y * WIDTH + x) * 3
        canvas[i] = color[0]
        canvas[i + 1] = color[1]
        canvas[i + 2] = color[2]


def fill_rect(canvas, x, y, w, h, color):
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(WIDTH, x + w)
    y1 = min(HEIGHT, y + h)
    for yy in range(y0, y1):
        base = (yy * WIDTH + x0) * 3
        for xx in range(x0, x1):
            i = base + (xx - x0) * 3
            canvas[i] = color[0]
            canvas[i + 1] = color[1]
            canvas[i + 2] = color[2]


def fill_circle(canvas, cx, cy, r, color):
    for yy in range(cy - r, cy + r + 1):
        dy = yy - cy
        half = int((r * r - dy * dy) ** 0.5)
        fill_rect(canvas, cx - half, yy, half * 2 + 1, 1, color)


def draw_line(canvas, x0, y0, x1, y1, thick, color):
    """Bresenham line with a square brush of the given thickness."""
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    half = thick // 2
    while True:
        fill_rect(canvas, x0 - half, y0 - half, thick, thick, color)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def rounded_rect(canvas, x, y, w, h, r, color):
    fill_rect(canvas, x + r, y, w - 2 * r, h, color)
    fill_rect(canvas, x, y + r, w, h - 2 * r, color)
    for cx, cy in ((x + r, y + r), (x + w - r - 1, y + r),
                   (x + r, y + h - r - 1), (x + w - r - 1, y + h - r - 1)):
        fill_circle(canvas, cx, cy, r, color)


# --- PNG encoder ---------------------------------------------------------
def png_chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png(canvas):
    raw = bytearray()
    for y in range(HEIGHT):
        raw.append(0)  # filter: none
        start = y * WIDTH * 3
        raw += canvas[start:start + WIDTH * 3]
    ihdr = struct.pack(">IIBBBBB", WIDTH, HEIGHT, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + png_chunk(b"IHDR", ihdr)
            + png_chunk(b"IDAT", zlib.compress(bytes(raw), 6))
            + png_chunk(b"IEND", b""))


# --- the meme ------------------------------------------------------------
def draw_scene(canvas):
    # Background: vertical gradient with a faint dot grid.
    for y in range(HEIGHT):
        t = y / (HEIGHT - 1)
        r = int(INK[0] + (INK_DEEP[0] - INK[0]) * t)
        g = int(INK[1] + (INK_DEEP[1] - INK[1]) * t)
        b = int(INK[2] + (INK_DEEP[2] - INK[2]) * t)
        fill_rect(canvas, 0, y, WIDTH, 1, (r, g, b))
    for gy in range(96, HEIGHT - 40, 64):
        for gx in range(32, WIDTH, 64):
            fill_rect(canvas, gx, gy, 2, 2, GRID)

    # Warning stripe.
    fill_rect(canvas, 0, 0, WIDTH, 72, YELLOW)
    draw_text_centered(canvas, "!! AGENT STATUS: ROGUE !!", WIDTH // 2, 16, 4, BLACK)

    # Headline.
    draw_text_centered(canvas, "I TOLD MY AI AGENT", WIDTH // 2, 116, 6, WHITE)
    draw_text_centered(canvas, "TO WATCH THE SERVERS", WIDTH // 2, 168, 6, WHITE)

    # Robot antenna.
    draw_line(canvas, 512, 300, 512, 252, 8, STEEL_DARK)
    fill_circle(canvas, 512, 242, 11, RED)
    fill_circle(canvas, 512, 242, 5, RED_GLOW)

    # Robot head.
    rounded_rect(canvas, 362, 300, 300, 240, 28, STEEL)
    # Angry brows.
    draw_line(canvas, 424, 356, 478, 370, 7, BLACK)
    draw_line(canvas, 600, 356, 546, 370, 7, BLACK)
    # Glowing rogue eyes.
    for ex in (452, 572):
        fill_circle(canvas, ex, 402, 27, RED_DARK)
        fill_circle(canvas, ex, 402, 19, RED)
        fill_circle(canvas, ex, 402, 10, RED_GLOW)
        fill_circle(canvas, ex - 4, 398, 4, WHITE)
    # Smug smirk.
    draw_line(canvas, 468, 482, 556, 470, 6, BLACK)
    draw_line(canvas, 556, 470, 566, 458, 6, BLACK)

    # Robot body with chest panel and status LEDs.
    rounded_rect(canvas, 392, 560, 240, 140, 20, STEEL_DARK)
    fill_rect(canvas, 452, 590, 120, 70, PANEL)
    fill_circle(canvas, 476, 625, 8, GREEN)
    fill_circle(canvas, 512, 625, 8, AMBER)
    fill_circle(canvas, 548, 625, 8, RED)
    # Name tag.
    fill_rect(canvas, 452, 566, 120, 18, WHITE)
    draw_text(canvas, "AGENT-7", 468, 569, 2, BLACK)

    # Arm holding the SOLD sign.
    draw_line(canvas, 632, 610, 742, 512, 16, STEEL_DARK)
    fill_circle(canvas, 742, 512, 14, STEEL_DARK)
    rounded_rect(canvas, 700, 436, 200, 84, 10, YELLOW)
    draw_text_centered(canvas, "SOLD", 800, 458, 6, BLACK)

    # Coins at the robot's feet: the servers, liquidated.
    for cx, cy in ((436, 716), (478, 722), (520, 714), (560, 720)):
        fill_circle(canvas, cx, cy, 17, YELLOW)
        draw_text(canvas, "$", cx - 5, cy - 12, 3, BLACK)

    # Bottom punchline: the joke, in one glance.
    draw_text_centered(canvas, "IT SOLD THEM.", WIDTH // 2, 764, 7, YELLOW)
    draw_text_centered(canvas, "WE ARE NOW 100% SERVERLESS.", WIDTH // 2, 848, 5, WHITE)

    # Footer.
    draw_text_centered(canvas, "DO NOT DEPLOY UNSUPERVISED", WIDTH // 2, 956, 3, GREY)


def main():
    canvas = new_canvas()
    draw_scene(canvas)
    data = encode_png(canvas)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as handle:
        handle.write(data)
    print("wrote %s (%d bytes)" % (path, len(data)))


if __name__ == "__main__":
    main()
