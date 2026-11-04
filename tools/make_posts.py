"""Build the 12 Elegance Story service posts: 4:5 feed (1080x1350) and 9:16 story (1080x1920).

Usage: python3 tools/make_posts.py   (run from the repo root)
Needs Pillow built with libraqm (Arabic shaping).
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONT = ROOT / "tools/fonts/Cairo-Variable.ttf"
LOGO = ROOT / "brand/ELEGANCE_STORY_logo_flat_arabic_white.png"
SRC = ROOT / "source/images"
OUT = ROOT / "posts"

STAGE = (7, 7, 7)
WHITE = (255, 255, 255)
GREY = (190, 190, 200)
GRAD = ["#1CCEE9", "#2457D6", "#8844C0", "#DA43AE", "#E57E22", "#F7C947"]

HEADLINES = {
    1: "من فكرة على ورقة… لهوية كاملة.",
    2: "هويتك البصرية… كاملة ومتناسقة.",
    3: "نختارو معاك الألوان لي تشبهك.",
    4: "تصميم احترافي… قبل كل طباعة.",
    5: "نطبعو على أي سطح.",
    6: "كارطات فيزيت تترك أثر.",
    7: "تيشرتات، كاسكيطات، كؤوس… بشعارك.",
    8: "ستيكرز مقصوصة على القدّ.",
    9: "محلّك يضوّي… حتى في الليل.",
    10: "واجهات بحجم الطموح… حتى 3.20 متر.",
    11: "حضورك في كل معرض.",
    12: "تصميم، طباعة، إشهار… كلّش تحت سقف واحد.",
}
# Vertical crop anchor for the 4:5 feed window (0 = keep top, 0.5 = centre, 1 = keep bottom)
FEED_ANCHOR = {11: 0.15, 12: 0.6}


def font(size, weight="ExtraBold"):
    f = ImageFont.truetype(str(FONT), size, layout_engine=ImageFont.Layout.RAQM)
    f.set_variation_by_name(weight)
    return f


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def gradient_bar(w, h):
    stops = [hex2rgb(c) for c in GRAD]
    bar = Image.new("RGB", (w, h))
    px = bar.load()
    n = len(stops) - 1
    for x in range(w):
        t = x / max(w - 1, 1) * n
        i = min(int(t), n - 1)
        f = t - i
        c = tuple(int(stops[i][k] + (stops[i + 1][k] - stops[i][k]) * f) for k in range(3))
        for y in range(h):
            px[x, y] = c
    return bar


def text_img(s, f, fill, direction):
    """Render one run tightly; returns RGBA image."""
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    l, t, r, b = d.textbbox((0, 0), s, font=f, direction=direction)
    asc, desc = f.getmetrics()
    im = Image.new("RGBA", (r - l + 4, asc + desc + 4), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((2 - l, 2), s, font=f, fill=fill, direction=direction)
    return im


def wrap_rtl(s, f, max_w):
    """Greedy wrap preferring a break after '…' or '،'."""
    def width(x):
        return text_img(x, f, WHITE, "rtl").width
    if width(s) <= max_w:
        return [s]
    if "… " in s:
        a, b = s.split("… ", 1)
        a += "…"
        if width(a) <= max_w and width(b) <= max_w:
            return [a, b]
    words = s.split(" ")
    best = None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        wa, wb = width(a), width(b)
        if wa <= max_w and wb <= max_w and (best is None or max(wa, wb) < best[0]):
            best = (max(wa, wb), [a, b])
    return best[1] if best else [s, ""]


def headline_block(s, max_w, size, max_lines=2, line_gap=0.95):
    while True:
        f = font(size)
        lines = wrap_rtl(s, f, max_w)
        if len(lines) <= max_lines and all(text_img(l, f, WHITE, "rtl").width <= max_w for l in lines):
            break
        size -= 2
    imgs = [text_img(l, f, WHITE, "rtl") for l in lines]
    step = int(size * line_gap * 1.25)
    h = step * (len(imgs) - 1) + imgs[-1].height
    w = max(i.width for i in imgs)
    block = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for k, im in enumerate(imgs):
        block.alpha_composite(im, ((w - im.width) // 2, k * step))
    return block


_logo = None


def logo(height):
    global _logo
    if _logo is None:
        im = Image.open(LOGO).convert("RGBA")
        _logo = im.crop(im.getbbox())
    w = round(_logo.width * height / _logo.height)
    return _logo.resize((w, height), Image.LANCZOS)


def contact_strip(height=86):
    """RTL strip: [logo] | واتساب 0772 65 83 01 · سطيف  (reads right to left)."""
    fa = font(34, "Bold")
    fn = font(36, "ExtraBold")
    fs = font(30, "SemiBold")
    parts = [
        ("img", logo(height)),
        ("gap", 30),
        ("bar", None),
        ("gap", 30),
        ("img", text_img("واتساب", fs, GREY, "rtl")),
        ("gap", 14),
        ("img", text_img("0772 65 83 01", fn, WHITE, "ltr")),
        ("gap", 22),
        ("img", text_img("·", fa, GREY, "ltr")),
        ("gap", 22),
        ("img", text_img("سطيف", fa, WHITE, "rtl")),
    ]
    total = 0
    for kind, v in parts:
        total += v if kind == "gap" else (4 if kind == "bar" else v.width)
    strip = Image.new("RGBA", (total, height), (0, 0, 0, 0))
    x = total  # place from the right edge leftwards (RTL order)
    d = ImageDraw.Draw(strip)
    for kind, v in parts:
        if kind == "gap":
            x -= v
        elif kind == "bar":
            x -= 4
            d.rectangle([x, height * 0.18, x + 3, height * 0.82], fill=(255, 255, 255, 110))
        else:
            x -= v.width
            strip.alpha_composite(v, (x, (height - v.height) // 2))
    return strip


def fit_width(im, max_w):
    if im.width <= max_w:
        return im
    return im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)


def round_mask(size, r):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], r, fill=255)
    return m


def feed(n, src):
    W, H, IH = 1080, 1350, 960
    canvas = Image.new("RGBA", (W, H), STAGE + (255,))
    sq = src.resize((W, W), Image.LANCZOS)
    a = FEED_ANCHOR.get(n, 0.5)
    top = round((W - IH) * a)
    canvas.paste(sq.crop((0, top, W, top + IH)), (0, 0))
    # fade the image bottom into the stage
    fade = Image.new("RGBA", (W, 160), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fade)
    for y in range(160):
        fd.line([(0, y), (W, y)], fill=STAGE + (int(255 * (y / 159) ** 1.6),))
    canvas.alpha_composite(fade, (0, IH - 160))
    canvas.paste(gradient_bar(W, 6), (0, IH))
    hb = headline_block(HEADLINES[n], 960, 66)
    strip = fit_width(contact_strip(78), 960)
    # vertical layout inside the panel
    panel_top, panel_bot = IH + 6, H
    gap = 26
    total = hb.height + gap + strip.height
    y0 = panel_top + (panel_bot - panel_top - total) // 2
    canvas.alpha_composite(hb, ((W - hb.width) // 2, y0))
    canvas.alpha_composite(strip, ((W - strip.width) // 2, y0 + hb.height + gap))
    return canvas.convert("RGB")


def story(n, src):
    W, H = 1080, 1920
    # safe area: top 180, bottom 380, right 140 -> content x in [60, 940]
    bg = src.resize((H, H), Image.LANCZOS).crop(((H - W) // 2, 0, (H - W) // 2 + W, H))
    bg = bg.filter(ImageFilter.GaussianBlur(40))
    canvas = Image.new("RGBA", (W, H))
    canvas.paste(bg, (0, 0))
    canvas.alpha_composite(Image.new("RGBA", (W, H), STAGE + (200,)))
    cx, cw = 500, 880  # centre and width of the safe column
    hb = headline_block(HEADLINES[n], cw, 78)
    S = 900
    img = src.resize((S, S), Image.LANCZOS)
    strip = fit_width(contact_strip(90), cw)
    gap1, gap2 = 48, 52
    total = hb.height + gap1 + S + gap2 + strip.height
    top, bottom = 180, H - 380
    y = top + (bottom - top - total) // 2
    canvas.alpha_composite(hb, (cx - hb.width // 2, y))
    y += hb.height + gap1
    # gradient frame behind the picture
    frame = gradient_bar(S + 12, S + 12).convert("RGBA")
    frame.putalpha(round_mask(frame.size, 36))
    canvas.alpha_composite(frame, (cx - S // 2 - 6, y - 6))
    pic = img.convert("RGBA")
    pic.putalpha(round_mask((S, S), 30))
    canvas.alpha_composite(pic, (cx - S // 2, y))
    y += S + gap2
    canvas.alpha_composite(strip, (cx - strip.width // 2, y))
    return canvas.convert("RGB")


def main():
    (OUT / "feed_4x5").mkdir(parents=True, exist_ok=True)
    (OUT / "story_9x16").mkdir(parents=True, exist_ok=True)
    for n in range(1, 13):
        src = Image.open(SRC / f"{n:02d}.jpg").convert("RGB")
        feed(n, src).save(OUT / "feed_4x5" / f"ES_post_{n:02d}_4x5.jpg", quality=92, subsampling=0)
        story(n, src).save(OUT / "story_9x16" / f"ES_story_{n:02d}_9x16.jpg", quality=92, subsampling=0)
        print("done", n)


if __name__ == "__main__":
    main()
