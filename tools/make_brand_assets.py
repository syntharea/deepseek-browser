#!/usr/bin/env python3
"""Generate DeepSeek-branded icons, posters and short welcome videos."""
from pathlib import Path
from urllib.request import Request, urlopen
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import os
import subprocess

ROOT = Path(__file__).resolve().parent.parent
EXT = Path(os.environ.get("EXT_DIR", ROOT / "work" / "deepseek-ext"))
BRAND = ROOT / "brand"

ICON = None
WORDMARK = None

BLUE = (77, 107, 254)
NAVY = (5, 9, 20)
DEEP = (10, 24, 66)
FONT_ZH_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_ZH_REG = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT_EN_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_EN_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def gradient(width: int, height: int) -> Image.Image:
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    for y in range(height):
        t = y / max(1, height - 1)
        r = round(NAVY[0] + (DEEP[0] - NAVY[0]) * t)
        g = round(NAVY[1] + (DEEP[1] - NAVY[1]) * t)
        b = round(NAVY[2] + (DEEP[2] - NAVY[2]) * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([width * 0.52, -height * 0.55, width * 1.18, height * 0.72], fill=BLUE + (120,))
    gd.ellipse([-width * 0.15, height * 0.55, width * 0.45, height * 1.4], fill=(120, 80, 255, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(70))
    return Image.alpha_composite(img.convert("RGBA"), glow)


def white_wordmark(width: int) -> Image.Image:
    ratio = width / WORDMARK.width
    wm = WORDMARK.resize((width, round(WORDMARK.height * ratio)), Image.LANCZOS)
    alpha = wm.getchannel("A")
    white = Image.new("RGBA", wm.size, (255, 255, 255, 255))
    white.putalpha(alpha)
    return white


def poster(lang: str) -> Image.Image:
    W, H = 960, 540
    img = gradient(W, H)
    draw = ImageDraw.Draw(img)
    zh = lang == "zh"
    wm = white_wordmark(360)
    img.alpha_composite(wm, (80, 118))
    draw.rectangle([80, 232, 140, 236], fill=BLUE)
    title_font = ImageFont.truetype(FONT_ZH_BOLD if zh else FONT_EN_BOLD, 38 if zh else 34)
    sub_font = ImageFont.truetype(FONT_ZH_REG if zh else FONT_EN_REG, 20)
    small_font = ImageFont.truetype(FONT_EN_REG, 15)
    title = "浏览器里的 DeepSeek" if zh else "DeepSeek in your browser"
    sub = "打开网页、点击、填写、提取，交给它完成。" if zh else "Open pages, click, fill forms, extract, and finish tasks."
    draw.text((80, 268), title, font=title_font, fill=(255, 255, 255, 255))
    draw.text((80, 330), sub, font=sub_font, fill=(199, 210, 254, 255))
    draw.text((80, 455), "deepseek.com", font=small_font, fill=(147, 164, 216, 255))
    return img


def make_video(image: Image.Image, path: Path) -> None:
    tmp = path.with_suffix(".png")
    image.save(tmp)
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", str(tmp),
        "-vf",
        "zoompan=z='min(zoom+0.00012,1.04)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=450:s=960x540:fps=30,"
        "fade=t=in:st=0:d=0.6,fade=t=out:st=14.4:d=0.6,format=yuv420p",
        "-t", "15", "-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
        "-movflags", "+faststart", str(path),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    tmp.unlink(missing_ok=True)


def fetch(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=30) as response:
        path.write_bytes(response.read())


def ensure_brand() -> None:
    global ICON, WORDMARK
    BRAND.mkdir(parents=True, exist_ok=True)
    icon_png = BRAND / "deepseek-icon.png"
    if not icon_png.exists():
        icon_ico = BRAND / "deepseek.ico"
        if not icon_ico.exists():
            fetch("https://www.deepseek.com/favicon.ico", icon_ico)
        Image.open(icon_ico).convert("RGBA").save(icon_png)
    wordmark = BRAND / "deepseek-wordmark.png"
    if not wordmark.exists():
        fetch("https://cdn.deepseek.com/logo.png", wordmark)
    ICON = Image.open(icon_png).convert("RGBA")
    WORDMARK = Image.open(wordmark).convert("RGBA")


def main() -> None:
    ensure_brand()
    for folder in [EXT / "icon", EXT / "welcome"]:
        folder.mkdir(parents=True, exist_ok=True)
    for size in [16, 32, 48, 128, 256]:
        ICON.resize((size, size), Image.LANCZOS).save(EXT / "icon" / f"{size}.png")
    for lang, suffix in [("zh", ""), ("en", "-en")]:
        img = poster(lang)
        img.convert("RGB").save(EXT / "welcome" / f"browser-intro{suffix}-poster.jpg", quality=92)
        make_video(img, EXT / "welcome" / f"browser-intro{suffix}.mp4")
    # onboarding screenshots are unused and were third-party branded
    onboarding = EXT / "onboarding"
    if onboarding.exists():
        for child in onboarding.iterdir():
            child.unlink()
        onboarding.rmdir()
    print("brand assets written")


if __name__ == "__main__":
    main()
