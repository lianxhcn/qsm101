"""检查课程网站的页面、站内资源、教学公式与课程入口。"""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from build_legacy import DESTINATIONS

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"
COURSE_URL = "https://www.lianxh.cn/qsm.html"
LESSONS = [
    "site/pages/foundations.html",
    "site/pages/reading.html",
    "site/pages/laboratory.html",
    "site/pages/evidence.html",
    "site/pages/faq.html",
    "site/pages/updates.html",
    "site/pages/about.html",
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
    for relative in ["index.html", *LESSONS, *DESTINATIONS]:
        if not (SITE / relative).is_file():
            errors.append(f"{relative}: 页面缺失。")
    if errors:
        return errors

    for page in pages:
        text = page.read_text(encoding="utf-8")
        parser = References()
        parser.feed(text)
        for kind, reference in parser.paths:
            parsed = urlsplit(reference)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = SITE / unquote(parsed.path).lstrip("/") if parsed.path.startswith("/") else page.parent / unquote(parsed.path)
            if target.is_dir():
                target /= "index.html"
            if not target.exists():
                errors.append(f"{page.relative_to(SITE)}: {kind}={reference} 不存在。")

    for relative in ["index.html", *LESSONS]:
        text = (SITE / relative).read_text(encoding="utf-8")
        if COURSE_URL not in text:
            errors.append(f"{relative}: 缺少课程主页入口。")
        visible = re.sub(r"<[^>]+>", " ", text)
        if re.search(r"\bP0[1-9]\b", visible):
            errors.append(f"{relative}: 公开页面仍显示内部编号。")
    for relative in ["site/pages/foundations.html", "site/pages/laboratory.html", "site/pages/evidence.html"]:
        if 'class="math display"' not in (SITE / relative).read_text(encoding="utf-8"):
            errors.append(f"{relative}: 教学公式未渲染。")
    notebook = ROOT / "site/pages/laboratory.ipynb"
    if not notebook.is_file():
        errors.append("两地区模型 Notebook 缺失。")
    else:
        notebook_text = notebook.read_text(encoding="utf-8")
        for required in ["在线章节", "下载基准数据", "load_csv", "estimate_theta", "solve(params"]:
            if required not in notebook_text:
                errors.append(f"Notebook 缺少必要内容：{required}。")
    if not (SITE / "figs/raw/qsm-course-fig01-logo-20261005-152554.ico").is_file():
        errors.append("网站 favicon 缺失。")
    if "qsm-course-fig02-cover-20261005-152554.png" not in (SITE / "site/styles.css").read_text(encoding="utf-8"):
        errors.append("首页封面样式缺失。")
    return errors

if __name__ == "__main__":
    failures = check()
    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        raise SystemExit(1)
    print(f"站点检查通过：{len(list(SITE.rglob('*.html')))} 个 HTML 页面、{len(DESTINATIONS)} 个旧网址跳转，公式、资源与课程入口均存在。")
