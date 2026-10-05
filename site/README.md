# QSM 课程预习站维护说明

改版前先读[网站内容与更新台账](../docs/site-content-ledger.md)：其中记录网站定位、原稿对应关系、P05 的插入位置和发布前核对项。

网站用 Quarto 构建。公开页面是 `index.qmd` 与 `site/pages/*.qmd`，按学习主题组织；`articles/*/article.md` 保留原始推文，不直接作为网站章节渲染。两地区模型以 `site/pages/laboratory.ipynb` 为可下载主文件；修改后先从头执行，再用 `quarto convert site/pages/laboratory.ipynb --output site/pages/laboratory.qmd` 更新网页源，并删除转换产生的 `#| execution:` 时间元数据。新增内容先核对模型与数据性质，再加入对应主题，并在 `site/pages/updates.qmd` 记录变化。

课程主页固定入口配置在 `_quarto.yml` 的导航和页脚，首页另有显要按钮。课程日期、报名和费用以 <https://www.lianxh.cn/qsm.html> 为准，不在本网站复制易变信息。

新页面应使用稳定英文 slug。加入导航时更新 `_quarto.yml`；若替换已有公开 URL，更新 `site/build_legacy.py` 的跳转表，避免旧链接失效。图标与封面原文件保存在 `figs/raw/`，上传结果记录在 `figs/uploaded-images.md`；再次生成或上传须采用新时间戳，不覆盖同名对象。

在仓库根目录运行：

```text
quarto render
python site/build_legacy.py
python site/check_site.py
```

GitHub Actions 在推送到 main 后执行同样的构建与检查，再发布 `_site/`。实验室的模拟结果不代表真实城市估计；通勤等后续机制应另写模型约定和核验，不直接改动现有两地区参考结果。


通勤章节以 `site/pages/commuting.ipynb` 为唯一网页与下载源，直接由 Quarto 渲染已执行输出，不另维护手写 qmd。离线包在 `articles/p05-commuting-qsm/downloads/commuting-workbook.zip`，包含 Notebook、两份固定 CSV、依赖说明和许可。修改后从头执行 Notebook、与参考 CSV 对照，再重新打包和渲染。所有网页与下载 Notebook 均不署名，也不显示邮箱；用户许可的远程发布另行执行。

通勤 Notebook 下载副本位于 `articles/p05-commuting-qsm/downloads/commuting.ipynb`，仅从已执行的网页源文件逐字节复制。重新执行后须同步该副本及 ZIP；站点检查会阻止不同步的下载文件。

Callout 采用 Quarto 原生 note/tip/warning 三类，提示词额外使用 agent-prompt 类。site/callout-copy.html 为纯文本提示词增加复制按钮，site/styles.css 管理手机换行与按钮焦点。只改 Markdown 排版时核对代码单元及已有输出保持不变即可，不必重复计算模型。
