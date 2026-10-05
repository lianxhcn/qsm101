# qsm101 网站发布质量记录

检查日期：2026-10-05。

## 范围与依据

已读取仓库的 README.md、AGENTS.md、articles/INDEX.md、P04 model.md、环境与 FAQ 文档，以及连享会 GitHub 发布规则。网站沿用 P01–P04 的 article.md 唯一正文；P01–P03 未改写。P05 只在首页显示“规划中”。

## 执行与结果

- 在 G 开发目录和 D 发布镜像分别运行 Quarto 1.6.39 的 `quarto render`，均成功生成 15 个 HTML 页面。
- 在两处运行 `site/check_site.py`，检查全部站内文件链接、四篇文章中的公式和配图，均通过。P04 参考结果目录的链接已在网站构建时指向对应的 README 页面，原稿保留。
- GitHub Actions 运行 [37275082906](https://github.com/lianxhcn/qsm101/actions/runs/37275082906) 成功。Pages 来源为 GitHub Actions，公开地址为 <https://lianxhcn.github.io/qsm101/>。
- 公开首页、P04 页面和 P04 配图的 HTTP 状态均为 200。在线 P04 页面包含作者署名、公式和参考结果入口。
- 仅暂存网站配置、首页、样式、检查脚本、发布计划、README 入口和索引中的已确认署名。未提交 `.venv/`、`_site/`、私人任务目录或个人运行结果。
- 本轮未新建、下载或修改图片；网站直接使用仓库中原有配图。P02 第三方素材沿用仓库中的来源说明，不纳入原创图文许可。

## 已知限制

Quarto 1.6.39 渲染时提示 zh-CN 翻译文件与 Abstract 术语缺失，但 HTML 的 `lang` 为 `zh-CN`，页面生成和检查通过。未逐一检查文章引用的外部论文与工具链接。网站展示的是教学模型，不把模拟结果表述为真实城市估计或外部验证。


## 2026-10-05：课程预习站改版

- 读取并整合原始文章、两地区模型约定、运行说明、FAQ、学习路线和课程入口。公开导航改为学习主题；原稿仍在 `articles/`，未改写确认稿，网站只在“关于本站”集中署名。
- 首页使用新封面与小 logo，显要位置链接 <https://www.lianxh.cn/qsm.html>。课程主页、图床封面和 SVG logo 的公开地址均返回 HTTP 200。
- 本地 G 开发目录与 D 发布镜像分别运行 `quarto render`、`site/build_legacy.py` 和 `site/check_site.py`：生成 8 个主题页面及 14 个旧网址跳转页，站内链接、教学公式、课程入口与本地 favicon 检查通过。桌面 1440px 与手机 390px 的首页截图已人工检查；导航小图标的零高度问题已修复。
- GitHub Actions [运行 37281138179](https://github.com/lianxhcn/qsm101/actions/runs/37281138179) 成功。公开首页、基础页、实验室页、关于页、ICO 文件和旧文章网址均返回 HTTP 200；旧网址页面包含迁移提示。
- 新视觉文件：`figs/raw/qsm-course-fig01-logo-20261005-152554.svg`、同名 PNG/ICO，以及 `figs/raw/qsm-course-fig02-cover-20261005-152554.png`。SVG 用于顶栏，ICO 用于 favicon，封面 PNG 用于首页首屏。SVG、PNG logo 与封面由 PicGo 上传，链接见 `figs/uploaded-images.md`。ICO 格式被上传脚本拒绝，作为网站本地资源发布。最初 PicGo 连接检查返回失败，但三次实际图片上传均成功，公开链接已核验。
- 网站正文没有本地图片路径引用；`figs/raw/` 是仓库内原件位置，ICO 与 SVG 的站点资源路径属于构建配置。未发现本次新增文件包含密钥或个人运行结果。
- 局限：Quarto 1.6.39 仍提示中文翻译文件及 Abstract 术语缺失，页面构建、渲染和公开访问不受影响。本文仅核对课程主页和新图床链接的可访问性，未逐一复核所有外部论文链接。模拟结果仍仅用于教学，不等于真实城市估计。
