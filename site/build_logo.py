"""生成与导航 SVG 对应的 PNG 和网站 favicon。"""

from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "figs" / "raw"
STAMP = datetime.now().strftime("%Y%m%d-%H%M%S")
STEM = f"qsm-course-fig01-logo-{STAMP}"

svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="QSM 图标">
  <rect width="64" height="64" rx="14" fill="#102a43"/>
  <circle cx="30" cy="29" r="17" fill="none" stroke="#f7f4ed" stroke-width="7"/>
  <path d="M41 41 L52 52" fill="none" stroke="#f7f4ed" stroke-width="7" stroke-linecap="round"/>
  <circle cx="52" cy="52" r="4" fill="#d49a62"/>
</svg>
"""
ASSET.mkdir(parents=True, exist_ok=True)
(ASSET / f"{STEM}.svg").write_text(svg, encoding="utf-8")

size = 256
image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(image)
draw.rounded_rectangle((0, 0, 255, 255), radius=56, fill="#102a43")
draw.ellipse((52, 48, 188, 184), outline="#f7f4ed", width=28)
draw.line((164, 164, 208, 208), fill="#f7f4ed", width=28)
draw.ellipse((192, 192, 224, 224), fill="#d49a62")
image.save(ASSET / f"{STEM}.png")
image.save(ASSET / f"{STEM}.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print(STEM)
