"""检查课程网站的页面、站内资源、教学公式与课程入口。"""

from __future__ import annotations

import re
import json
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
    "site/pages/commuting.html",
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
        visible_text = re.sub(r"<[^>]+>", "", text)
        if re.search(r"(?:作者|邮箱)[：:]", visible_text) or 'href="mailto:' in text:
            errors.append(f"{page.relative_to(SITE)}: 仍有作者或邮箱信息。")
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
    for relative in ["site/pages/foundations.html", "site/pages/laboratory.html", "site/pages/commuting.html", "site/pages/evidence.html"]:
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
    commuting = ROOT / "site/pages/commuting.ipynb"
    if not commuting.is_file():
        errors.append("通勤 Notebook 缺失。")
    else:
        nb = json.loads(commuting.read_text(encoding="utf-8"))
        cells = nb.get("cells", [])
        joined = "\n".join("".join(c.get("source", [])) for c in cells)
        for required in ["load_csv", "commute_multiplier", "def state", "def solve", "def estimate", "高通勤成本", "练习", "EXPECTED_HASHES", "Agent 实现与核验", "03-estimate-calibrate.md"]:
            if required not in joined:
                errors.append(f"通勤 Notebook 缺少：{required}。")
        if "**作者" in joined or "待定" in joined:
            errors.append("通勤 Notebook 仍有署名或待定标记。")
        for cell in cells:
            if cell.get("cell_type") == "code":
                if cell.get("execution_count") is None:
                    errors.append("通勤 Notebook 存在未执行代码格。")
                if any(o.get("output_type") == "error" for o in cell.get("outputs", [])):
                    errors.append("通勤 Notebook 含错误输出。")
        for target in ["site/pages/commuting.ipynb", "articles/p05-commuting-qsm/downloads/commuting-workbook.zip", "articles/p05-commuting-qsm/downloads/commuting-agent-inputs.zip", "articles/p05-commuting-qsm/downloads/commuting.ipynb"]:
            if not (SITE / target).is_file():
                errors.append(f"通勤下载资源缺失：{target}。")
    download = SITE / "articles/p05-commuting-qsm/downloads/commuting.ipynb"
    if download.exists() and download.read_bytes() != commuting.read_bytes():
        errors.append("通勤下载 Notebook 与网页源文件不同步。")
    page = SITE / "site/pages/commuting.html"
    if "../../articles/p05-commuting-qsm/downloads/commuting.ipynb" not in page.read_text(encoding="utf-8"):
        errors.append("通勤 Notebook 下载链接被改写或缺失。")
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
