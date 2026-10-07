# QSM 网站维护说明

修改前阅读[统一规范](../docs/site-standards.md)和[内容台账](../docs/site-content-ledger.md)。原推文在 `articles/*/article.md` 保留出版格式；网站章节单独适配，去除作者、邮箱、Title 和 Keywords。

## 内容来源与网址

| 章节 | 唯一内容源 | 渲染入口 | 下载文件 |
|---|---|---|---|
| M1：无通勤基准模型 | site/pages/m1-baseline.ipynb | 生成的 m1-baseline.qmd | articles/p04-minimal-qsm/downloads/baseline.ipynb |
| M2：加入跨地区通勤 | site/pages/m2-commuting.ipynb | 同源 Notebook | articles/p05-commuting-qsm/downloads/commuting.ipynb |
| M3：通勤成本变化 | site/pages/m3-transport-policy.ipynb | 同源 Notebook | articles/p06-transport-qsm/downloads/transport.ipynb |

本次网站尚未公布，直接改为上述顺序语义 URL，不生成旧页面或跳转。统一发布后保持网址稳定。下载文件名不承担网站排序任务，维持简短功能名称。

## 修改与构建

在仓库根目录运行：

```text
python site/prepare_site.py
quarto render
python -B site/check_site.py --prompt-contract strict
```

`prepare_site.py` 不执行数值计算。它读取三个主 Notebook，为计算结果表添加语义标题与锚点，同步离线 Notebook 和完整 ZIP，并通过 Quarto convert 生成 M1 QMD。M1 网页沿用讲义表格和上传图，Notebook 另外保留完整执行输出。M2/M3 网页直接呈现执行输出。仅修改排版时核对公式、代码与数值；改计算后必须从头执行再同步。

离线副本将本章资源转换为包内相对路径，其他章节链接指向最终公开网址；不要要求网页与下载文件逐字节相同。检查代码、公式与数值，并单独检查路径转换。完整包包括固定数据、模型和依赖说明；新增或调整离线结构时必须在新解压目录执行。输入包与含答案的完整包分别维护。

GitHub Actions 渲染并运行只读检查器；它不生成旧链接兼容页。发布前先在本地运行同步脚本，确保待提交下载包已更新。提交、推送和发布须另获用户授权。

## 图式与阅读交互

公式使用 `eq-` 语义标签，图形使用 `fig-` 标签及图注、替代文本。Quarto 负责页内自动编号。多行方程组默认一个编号；不要手写显示序号。输出图在代码单元顶部通过 `#| label`、`#| fig-cap` 配置，多图还使用 `fig-subcap`。

Markdown 表格后添加图注语法 `: 表名 {#tbl-语义标签}`。Notebook 输出表的单元元数据 `qsm_tables` 按输出顺序列出语义 `id` 与标题，由同步脚本写入 HTML caption。Quarto 自动按整页顺序编号，共享阅读脚本把表内滚动交给外层容器。新增表格必须通过检查器和浏览器核验。

桌面正文净宽 800 px、字号 18 px；手机正文 17 px。标题上下各约半行留白。代码默认折叠，入口文字与箭头用深绿色，保留键盘焦点。Agent 提示词保留复制功能。密集图与正文同宽；小幅计算图按实际分辨率展示。所有教学图点击进入同一 lightbox，支持 Esc 关闭和焦点返回，不以原图下载作为默认行为。

每轮验收覆盖全站链接、公式图表标签、展开操作、图片点击不下载、实际表格行宽、390 px 手机阅读及下载同步。检查器只读；用户提出评估任务时，不借检查之名写入网页或发布资源。


## 随读提示词组件 v2

三个模型页采用两类随读卡片，统一指南已加入网站说明导航。规则来源见 [长期规范第 11–13 节](../docs/site-standards.md)，配色与分类值见 prompt-contract.json。

卡片在主 Notebook 中编写，保留稳定 id，新增 `data-prompt-kind="exercise"` 或 `data-prompt-kind="transfer"`。summary 同时包含 Agent、中文类型与任务；不放复制按钮或链接，不设置 open。复制按钮在展开区域内，分别关联 task 与 example；aria-controls 指向各自文本块，复制失败时选中对应文字。

```html
<details class="agent-prompt" id="agent-章节-任务" data-prompt-kind="transfer">
<summary><span class="agent-prompt-toggle" aria-hidden="true"></span><span>Agent · 迁移到我的研究：具体任务</span></summary>
<div class="agent-prompt-body">
<div data-prompt-role="materials">

说明 {模型说明材料} 应填写已上传的文件名或粘贴的设定。

</div>
<div data-prompt-role="scope">

说明什么时候使用，以及需要核对的模型条件。

</div>
<div data-prompt-role="task">

使用一个 text 围栏存放可复制任务，包含 {模型说明材料}。

</div>
<div data-prompt-role="example">

使用另一个 text 围栏给出教材填写示例，与模板分别复制。

</div>
<div data-prompt-role="checks">

说明拿到回复后检查哪些方程、输出或执行证据。

</div>
</div>
</details>
```

上面是结构示意，不是可直接提交的完整卡片。task 必须有且仅有一个非空 text 围栏；渲染后为 pre。迁移类 example 同样使用单独围栏。讲义练习可以省略 example，但 materials 必须有明确材料链接。角色区内不嵌套 details，保持渲染、复制与导出结构清晰。所有占位符在 materials 区逐项说明，示例不算占位符说明。

prepare_site.py 从角色区导出两类内容及指南，保留任务与示例的独立区块。指南由 offline_guide_text 作固定的离线路径转换；不要手工编辑生成副本。通勤练习包还同步无通勤模型说明至 models/no-commuting-model.md，供扩展练习对照。源稿、渲染 HTML、下载 Notebook 的任务内容应相同；外围材料链接允许明确的离线路径转换。input-only 包不加入参考程序、Notebook 或答案。

## 检查工具与迁移状态

```text
python -B site/check_site.py
python -B site/check_site.py --prompt-contract audit
python -B site/check_prompt_contract.py --audit --json
python -B site/check_site.py --prompt-contract strict
python -B -m unittest discover -s site/tests -p "test_prompt_contract.py" -v
```

- 默认命令检查既有页面并明确提示 v2 尚未检查。
- audit 返回缺口列表，缺口本身不改变退出状态；PENDING 绝不是验收通过。原有页面检查失败仍返回非零。
- strict 在所有静态要求满足前返回非零。CI 已使用 strict，不能用 audit 放行发布。修改工作流本身不代表已经发布。
- 检查工具仅用 Python 标准库；-B 避免导入时写入缓存。不会联网、写站点或运行模型。JSON 只输出到标准输出，日志保存由调用者显式重定向。
- 配色检查核对 CSS 变量声明及声明色值的对比度；实际选择器是否应用、状态颜色、复制行为、材料充分性与经济含义仍需浏览器和人工核验。
- 不设置每章两类卡片的最低数量；也不把出现关键词当作经济学正确的证明。

实施顺序：使用指南 → 三章卡片 → 共享配色与复制逻辑 → 下载和导出 → FAQ/学习路线 → strict 与浏览器/人工审阅 → 获授权后发布。新规范先经过规则与工具阶段；本次已完成本地页面迁移，模型代码、数据和参考输出保持不变。


2026-10-08 调整：Agent 讲义练习为浅紫底与书本图标，迁移任务为浅蓝底与向外箭头。既有 aria-hidden 的装饰 span 承载固定类别图标，summary 右侧 CSS 箭头表示开合；图标由共享 CSS 内联矢量定义，不依赖外部资源。模板结构和复制规则不变。
