"""Dice Rush Extended - brand image (195x195 px), pixel-art style.

Built only from the mod's own art (dice from build/generated/bdr/art/dice, the fortune teller's
hands of Dice Shaker from build/generated/shaker/art/scene) and the free Press Start 2P font
(OFL, the pixel font the game uses). The original DICE RUSH logo is not used.

Run:  tools/venv/Scripts/python.exe tools/art/gen_brand.py
Output: docs/brand_195.png (+ docs/brand_780.png, the same picture 4x bigger)
"""
import os
import random

from PIL import Image, ImageDraw, ImageFont

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DICE = os.path.join(REPO, "build", "generated", "bdr", "art", "dice")
SCENE = os.path.join(REPO, "build", "generated", "shaker", "art", "scene")
FONT_CANDIDATES = [
    os.path.join(REPO, "work", "recovered", "assets", "fonts", "PressStart2P-Regular.ttf"),
    os.path.join(REPO, "tools", "art", "PressStart2P-Regular.ttf"),
]
OUT = os.path.join(REPO, "docs", "brand_195.png")
SIZE = 195


def hexc(value, alpha=255):
    value = value.lstrip("#")
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16), alpha)


def font(size):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    raise SystemExit("Press Start 2P font not found (put PressStart2P-Regular.ttf into tools/art/)")


def dice_sprite(kind, size=64):
    """The mod's dice are drawn on a 64x64 grid and stored 4x. 64 = the crisp original; smaller sizes
    are scaled smoothly and get hard alpha edges again."""
    image = Image.open(os.path.join(DICE, kind + ".png")).convert("RGBA")
    if size == 64:
        return image.resize((size, size), Image.NEAREST)
    small = image.resize((size, size), Image.LANCZOS)
    alpha = small.getchannel("A").point(lambda a: 255 if a >= 110 else 0)
    small.putalpha(alpha)
    return small


def hand_sprite(side):
    """The fortune teller's hand of Dice Shaker (native pixel size)."""
    return Image.open(os.path.join(SCENE, "hand_%s.png" % side)).convert("RGBA")


def text_mask(text, size):
    """Hard-edged (not anti-aliased) text mask, cropped to the glyphs."""
    fnt = font(size)
    box = fnt.getbbox(text)
    mask = Image.new("L", (box[2] + 4, box[3] + 4), 0)
    draw = ImageDraw.Draw(mask)
    draw.fontmode = "1"
    draw.text((0, 0), text, font=fnt, fill=255)
    return mask.crop(mask.getbbox())


def gradient_fill(mask, top, bottom):
    width, height = mask.size
    fill = Image.new("RGBA", mask.size)
    pixels = fill.load()
    for y in range(height):
        t = y / max(1, height - 1)
        color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(4))
        for x in range(width):
            pixels[x, y] = color
    out = Image.new("RGBA", mask.size, (0, 0, 0, 0))
    out.paste(fill, (0, 0), mask)
    return out


def outlined(mask, top, bottom, outline, thickness=2, shadow=None):
    """Gradient text with a pixel outline (and an optional drop shadow below it)."""
    pad = thickness + (2 if shadow else 0)
    width, height = mask.size
    canvas = Image.new("RGBA", (width + pad * 2, height + pad * 2), (0, 0, 0, 0))
    solid = Image.new("RGBA", mask.size, outline)
    if shadow:
        shadow_solid = Image.new("RGBA", mask.size, shadow)
        for dx in range(-thickness, thickness + 1):
            for dy in range(-thickness, thickness + 1):
                canvas.paste(shadow_solid, (pad + dx, pad + dy + 2), mask)
    for dx in range(-thickness, thickness + 1):
        for dy in range(-thickness, thickness + 1):
            if dx * dx + dy * dy <= thickness * thickness + 1:
                canvas.paste(solid, (pad + dx, pad + dy), mask)
    face = gradient_fill(mask, top, bottom)
    canvas.alpha_composite(face, (pad, pad))
    return canvas


def background():
    image = Image.new("RGBA", (SIZE, SIZE))
    pixels = image.load()
    top, bottom = hexc("#241450"), hexc("#0c0822")
    for y in range(SIZE):
        t = y / (SIZE - 1)
        color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(4))
        for x in range(SIZE):
            pixels[x, y] = color
    draw = ImageDraw.Draw(image)
    # stepped glow behind the dice (hard edged rings, pixel-art style)
    center = (SIZE // 2, 98)
    for radius, color in ((78, "#2e1a63"), (62, "#38207a"), (46, "#44288f")):
        draw.ellipse((center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius), fill=hexc(color))
    # stars
    rng = random.Random(67)
    for _ in range(70):
        x, y = rng.randrange(6, SIZE - 6), rng.randrange(6, SIZE - 6)
        pixels[x, y] = hexc(rng.choice(["#ffffff", "#c9b8ff", "#8f7bd8", "#ffe9a8"]), rng.choice([150, 200, 255]))
    for x, y in ((20, 46), (174, 40), (28, 140), (168, 132), (150, 70), (40, 92)):
        color = hexc("#fff3c4")
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            pixels[x + dx, y + dy] = color
    return image


def frame(image):
    draw = ImageDraw.Draw(image)
    dark, gold, light, shade = hexc("#2a1405"), hexc("#d99a1e"), hexc("#ffd36b"), hexc("#a8650c")
    last = SIZE - 1
    draw.rectangle((0, 0, last, last), outline=dark, width=1)
    draw.rectangle((1, 1, last - 1, last - 1), outline=gold, width=3)
    draw.line((1, 1, last - 1, 1), fill=light)            # light from the top left
    draw.line((1, 1, 1, last - 1), fill=light)
    draw.line((1, last - 1, last - 1, last - 1), fill=shade)
    draw.line((last - 1, 1, last - 1, last - 1), fill=shade)
    draw.rectangle((4, 4, last - 4, last - 4), outline=dark, width=1)
    # cut corners + rivets like the game's wooden/golden panels
    for cx, cy in ((0, 0), (last, 0), (0, last), (last, last)):
        image.putpixel((cx, cy), (0, 0, 0, 0))
    for x, y in ((6, 6), (last - 13, 6), (6, last - 13), (last - 13, last - 13)):
        draw.rectangle((x, y, x + 7, y + 7), fill=gold, outline=dark)
        draw.rectangle((x + 2, y + 2, x + 3, y + 3), fill=light)


def banner(image, text_image, center_x, top):
    """Red ribbon with folded ends behind 'EXTENDED'."""
    draw = ImageDraw.Draw(image)
    width, height = text_image.size
    left, right = center_x - width // 2 - 10, center_x + width // 2 + 10
    bottom = top + height + 6
    dark, red, red_light, red_dark = hexc("#2a0a0e"), hexc("#c8283a"), hexc("#ee4a5a"), hexc("#7c1420")
    # folded tails
    for side in (-1, 1):
        edge = left if side < 0 else right
        tail = [(edge, top + 4), (edge + side * 12, top + 4), (edge + side * 7, (top + bottom) // 2 + 2), (edge + side * 12, bottom + 4), (edge, bottom + 4)]
        draw.polygon(tail, fill=red_dark, outline=dark)
    draw.rectangle((left, top, right, bottom), fill=red, outline=dark)
    draw.line((left + 1, top + 1, right - 1, top + 1), fill=red_light)
    draw.line((left + 1, bottom - 1, right - 1, bottom - 1), fill=red_dark)
    image.alpha_composite(text_image, (center_x - width // 2, top + 3))


def make() -> Image.Image:
    image = background()
    # the fortune teller's arms come in from both sides (like in Dice Shaker), the hands never touch the dice
    left, right = hand_sprite("left"), hand_sprite("right")
    image.alpha_composite(left, (-50, 72))
    image.alpha_composite(right, (SIZE - right.width + 50, 72))
    # dice (smaller): pepe and 67 behind, the lucky block in front - every symbol stays visible
    size = 38
    back_left, back_right, front = dice_sprite("pepe", size), dice_sprite("sixseven", size), dice_sprite("luckyblock", size)
    back_y = 62
    shadow = ImageDraw.Draw(image)
    shadow.ellipse((SIZE // 2 - 46, back_y + 54, SIZE // 2 + 46, back_y + 66), fill=hexc("#1b0f3e"))
    shadow.ellipse((SIZE // 2 - 26, back_y + 57, SIZE // 2 + 26, back_y + 64), fill=hexc("#130a2e"))
    image.alpha_composite(back_left, (SIZE // 2 - size - 1, back_y))
    image.alpha_composite(back_right, (SIZE // 2 + 1, back_y))
    image.alpha_composite(front, (SIZE // 2 - size // 2, back_y + 20))
    # title, and under RUSH in small letters: +DICE SHAKER / +COOP
    title = outlined(text_mask("DICE RUSH", 16), hexc("#ffffff"), hexc("#9fe3ff"), hexc("#10183a"), 2, shadow=hexc("#05060f"))
    title_x = (SIZE - title.width) // 2
    image.alpha_composite(title, (title_x, 10))
    right_edge = title_x + title.width - 3
    shaker = outlined(text_mask("+DICE SHAKER", 8), hexc("#ffd0ff"), hexc("#c46bff"), hexc("#1a0628"), 1)
    coop = outlined(text_mask("+COOP", 8), hexc("#d8fbff"), hexc("#4fd6ff"), hexc("#06182a"), 1)
    top = 10 + title.height - 1
    image.alpha_composite(shaker, (right_edge - shaker.width, top))
    image.alpha_composite(coop, (right_edge - coop.width, top + shaker.height - 1))
    # EXTENDED on a ribbon
    extended = outlined(text_mask("EXTENDED", 16), hexc("#fff0a8"), hexc("#f2a71b"), hexc("#3a1d05"), 2)
    banner(image, extended, SIZE // 2, 152)
    frame(image)
    return image


def main():
    image = make()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    image.save(OUT)
    # 4x copy (pixel-exact) for the README, stays crisp on high-DPI screens
    image.resize((SIZE * 4, SIZE * 4), Image.NEAREST).save(OUT.replace("_195.png", "_780.png"))
    print("saved", OUT, image.size)


if __name__ == "__main__":
    main()
