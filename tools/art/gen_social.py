"""Dice Rush Extended - GitHub social preview (1280x640), pixel-art style.

Drawn on a 427x214 pixel canvas and scaled 3x with hard edges: the brand image on the left,
the main features on the right. Uses the brand image of gen_brand.py.

Run:  tools/venv/Scripts/python.exe tools/art/gen_social.py
Output: docs/social_preview.png
"""
import os
import random

from PIL import Image, ImageDraw

import gen_brand as brand

REPO = brand.REPO
OUT = os.path.join(REPO, "docs", "social_preview.png")
WIDTH, HEIGHT = 427, 214
SCALE = 3
FEATURES = [
    ("NEW MODE: DICE SHAKER", "#c46bff"),
    ("100 NEW DICE", "#7ee06a"),
    ("SHOP AND DESIGNS", "#ffd166"),
    ("67 NEW TALENTS", "#5dd0ff"),
    ("40 TAROT CARDS", "#ff9fd8"),
    ("10 STAFF TYPES", "#ff9f5a"),
    ("COOP FOR 2 PLAYERS", "#ff6fa8"),
    ("UP TO 7,000 DICE", "#9fe3ff"),
]


def background():
    image = Image.new("RGBA", (WIDTH, HEIGHT))
    pixels = image.load()
    top, bottom = brand.hexc("#241450"), brand.hexc("#0c0822")
    for y in range(HEIGHT):
        t = y / (HEIGHT - 1)
        color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(4))
        for x in range(WIDTH):
            pixels[x, y] = color
    rng = random.Random(7000)
    for _ in range(110):
        x, y = rng.randrange(6, WIDTH - 6), rng.randrange(6, HEIGHT - 6)
        pixels[x, y] = brand.hexc(rng.choice(["#ffffff", "#c9b8ff", "#8f7bd8", "#ffe9a8"]), rng.choice([150, 200, 255]))
    for x, y in ((224, 24), (404, 30), (398, 120), (236, 176), (318, 196)):
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            pixels[x + dx, y + dy] = brand.hexc("#fff3c4")
    return image


def frame(image):
    draw = ImageDraw.Draw(image)
    dark, gold, light, shade = brand.hexc("#2a1405"), brand.hexc("#d99a1e"), brand.hexc("#ffd36b"), brand.hexc("#a8650c")
    right, bottom = WIDTH - 1, HEIGHT - 1
    draw.rectangle((0, 0, right, bottom), outline=dark, width=1)
    draw.rectangle((1, 1, right - 1, bottom - 1), outline=gold, width=3)
    draw.line((1, 1, right - 1, 1), fill=light)
    draw.line((1, 1, 1, bottom - 1), fill=light)
    draw.line((1, bottom - 1, right - 1, bottom - 1), fill=shade)
    draw.line((right - 1, 1, right - 1, bottom - 1), fill=shade)
    draw.rectangle((4, 4, right - 4, bottom - 4), outline=dark, width=1)
    for cx, cy in ((0, 0), (right, 0), (0, bottom), (right, bottom)):
        image.putpixel((cx, cy), (0, 0, 0, 0))


def gem(draw, x, y, color):
    """Small pixel diamond used as bullet point."""
    fill, dark = brand.hexc(color), brand.hexc("#0a0618")
    draw.polygon([(x + 3, y - 1), (x + 7, y + 3), (x + 3, y + 7), (x - 1, y + 3)], fill=dark)
    draw.polygon([(x + 3, y), (x + 6, y + 3), (x + 3, y + 6), (x, y + 3)], fill=fill)
    draw.point((x + 2, y + 2), fill=brand.hexc("#ffffff"))


def main():
    image = background()
    image.alpha_composite(brand.make(), (9, 9))
    draw = ImageDraw.Draw(image)
    left = 222
    title = brand.outlined(brand.text_mask("FAN MOD FOR DICE RUSH", 8), brand.hexc("#fff0a8"), brand.hexc("#f2a71b"), brand.hexc("#3a1d05"), 1)
    image.alpha_composite(title, (left - 1, 18))
    draw.line((left, 34, WIDTH - 16, 34), fill=brand.hexc("#5a3fa0"))
    for index, (text, color) in enumerate(FEATURES):
        y = 44 + index * 17
        gem(draw, left, y, color)
        line = brand.outlined(brand.text_mask(text, 8), brand.hexc("#ffffff"), brand.hexc("#d8e6ff"), brand.hexc("#0a0618"), 1)
        image.alpha_composite(line, (left + 12, y - 1))
    footer = brand.outlined(brand.text_mask("github.com/Minnteee", 8), brand.hexc("#b9a6f0"), brand.hexc("#8f7bd8"), brand.hexc("#0a0618"), 1)
    image.alpha_composite(footer, (left - 1, HEIGHT - 26))
    frame(image)
    big = image.resize((WIDTH * SCALE, HEIGHT * SCALE), Image.NEAREST).crop((0, 0, 1280, 640))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    big.convert("RGB").save(OUT, optimize=True)
    print("saved", OUT, big.size, "%.0f KB" % (os.path.getsize(OUT) / 1024))


if __name__ == "__main__":
    main()
