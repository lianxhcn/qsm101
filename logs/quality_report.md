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
