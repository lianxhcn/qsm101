"""为已公开的旧文章 URL 生成轻量跳转页，保留外部引用。"""

from html import escape
from pathlib import Path
from urllib.parse import quote
import os

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"
DESTINATIONS = {
    "articles/p01-qsm-introduction/article.html": "site/pages/foundations.html",
    "articles/p02-qsm-mechanisms/article.html": "site/pages/evidence.html",
    "articles/p03-learning-roadmap/article.html": "site/pages/reading.html",
    "articles/p04-minimal-qsm/article.html": "site/pages/laboratory.html",
    "articles/p04-minimal-qsm/README.html": "site/pages/laboratory.html",
    "articles/p04-minimal-qsm/model.html": "site/pages/laboratory.html",
    "articles/p04-minimal-qsm/prompts/README.html": "site/pages/laboratory.html",
    "articles/p04-minimal-qsm/results/reference/README.html": "site/pages/laboratory.html",
    "docs/setup.html": "site/pages/laboratory.html",
    "docs/faq.html": "site/pages/faq.html",
    "docs/agent-workflow.html": "site/pages/laboratory.html",
    "docs/repository-map.html": "site/pages/reading.html",
    "course/README.html": "index.html",
    "references/README.html": "site/pages/reading.html",
}

for previous, current in DESTINATIONS.items():
    target = SITE / previous
    destination = SITE / current
    if not destination.is_file():
        raise FileNotFoundError(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    relative = Path(os.path.relpath(destination, target.parent)).as_posix()
    canonical = "https://lianxhcn.github.io/qsm101/" + quote(current)
    html = (
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="robots" content="noindex">'
        f'<meta http-equiv="refresh" content="0; url={escape(relative, quote=True)}">'
        f'<link rel="canonical" href="{escape(canonical, quote=True)}">'
        '<title>页面已迁移 · QSM 基础</title></head><body>'
        f'<p>页面已迁移。<a href="{escape(relative, quote=True)}">前往新页面</a>。</p>'
        '</body></html>'
    )
    target.write_text(html, encoding="utf-8")
if __name__ == '__main__':
    print(f'已建立 {len(DESTINATIONS)} 个旧网址跳转页。')
