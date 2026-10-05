# 目录与后续扩展

| 路径 | 用途 | 更新方式 |
|---|---|---|
| README.md | 仓库入口、阅读顺序与首次运行 | 维护简短、可执行的入口 |
| articles/INDEX.md | 编号、主题、资料与状态 | 只链接实际存在的文章 |
| articles/<编号与主题>/article.md | 唯一推文正文 | 用 Git 记录改动，不建立多份最终稿 |
| articles/<编号与主题>/figures/ | 正文配图 | 保留来源，计算图与结果相对应 |
| articles/p04-minimal-qsm/code/ | P04 参考实现 | 模型变化时同步 model.md 与说明 |
| articles/p04-minimal-qsm/data/ | 固定教学输入 | 说明模拟规则与字段口径 |
| articles/p04-minimal-qsm/results/reference/ | 已核验参考结果 | 复核后更新，不存个人试跑 |
| articles/p04-minimal-qsm/prompts/ | 正文提示词与独立实现输入 | 改提示词后重新试跑 |
| docs/ | 环境、Agent 练习和 FAQ | 经验依据实际记录补充 |
| course/ | 学习目标和课程入口说明 | 与正式课程公告保持一致 |
| references/ | 理论、数据、软件来源入口 | 提供来源链接，不复制受限全文 |
| runs/ | 自己的运行输出 | 被 Git 忽略 |
| Task/、.work/ | 私人任务与原始记录 | 被 Git 忽略，不公开 |

每篇新文章先确认问题、机制、变量口径和资料性质，再建立自己的目录。只有正文与资料实际存在时才加入索引。P05 将承接 P04 的住房政策问题，加入通勤机制；目前保留规划文字即可。
