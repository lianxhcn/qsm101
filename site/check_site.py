"""检查 Quarto 静态网站中的本地资源与基本页面结构。"""

from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"
ARTICLES = [
    "articles/p01-qsm-introduction/article.html",
    "articles/p02-qsm-mechanisms/article.html",
    "articles/p03-learning-roadmap/article.html",
    "articles/p04-minimal-qsm/article.html",
]


class References(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.paths: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        for key in ("href", "src"):
            value = attributes.get(key)
            if value:
                self.paths.append((key, value))


def check() -> list[str]:
    errors: list[str] = []
    pages = sorted(SITE.rglob("*.html"))
    if not pages or not (SITE / "index.html").exists():
        return ["网站首页没有生成。"]

    for page in pages:
        text = page.read_text(encoding="utf-8")
        parser = References()
        parser.feed(text)
        if "[toc]" in text:
            errors.append(f"{page.relative_to(SITE)}: 原稿目录占位符仍在页面中。")
        for kind, reference in parser.paths:
            parsed = urlsplit(reference)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            if parsed.path.startswith("/"):
                target = SITE / unquote(parsed.path).lstrip("/")
            else:
                target = page.parent / unquote(parsed.path)
            if target.is_dir():
                target /= "index.html"
            if not target.exists():
                errors.append(f"{page.relative_to(SITE)}: {kind}={reference} 不存在。")

    for relative in ARTICLES:
        page = SITE / relative
        if not page.exists():
            errors.append(f"{relative}: 文章页面没有生成。")
            continue
        text = page.read_text(encoding="utf-8")
        if 'class="math display"' not in text:
            errors.append(f"{relative}: 未发现渲染后的独立公式。")
        if 'src="figures/' not in text:
            errors.append(f"{relative}: 未发现文章配图。")

    return errors


if __name__ == "__main__":
    failures = check()
    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        raise SystemExit(1)
    print(f"站点检查通过：{len(list(SITE.rglob('*.html')))} 个 HTML 页面，4 篇文章均有公式和配图，本地链接存在。")
