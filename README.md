# qsm101：从第一个模型开始学习 QSM

这里整理连享会 QSM 系列推文的正文、配图、模型说明、教学数据、代码与参考结果。读者可以先建立空间均衡的直觉，再完成一个两地区模型的估计、校准和反事实计算。后续文章将逐步加入通勤等机制。

## 按顺序阅读

| 编号 | 文章 | 建议完成的练习 |
|---|---|---|
| P01 | [一文读懂 QSM](articles/p01-qsm-introduction/article.md) | 分清数据、参数与均衡条件 |
| P02 | [从 DID 到 QSM：柏林墙研究](articles/p02-qsm-mechanisms/article.md) | 理解因果识别与结构反事实的联系 |
| P03 | [QSM 怎么学](articles/p03-learning-roadmap/article.md) | 选择综述、讲义和适合的工具包 |
| P04 | [第一次动手做 QSM](articles/p04-minimal-qsm/article.md) | 运行参考代码，再用 Codex 按提示词实现 |
| P05 | 通勤引力扩展 (规划中) | 未来区分居住地与工作地，并重新校准求解 |

完整目录见 [文章索引](articles/INDEX.md)。P01–P03 为作者确认稿；P04 参考程序与原始提示词的独立实现均已完成数值和经济条件核验；实际环境问题及处理见 [试跑记录](docs/agent-workflow.md)。

## 先跑通 P04

需要 Python。交付测试环境是 Python 3.12，本地另验证了 Windows Python 3.11.14，依赖版本保存在每篇文章的 requirements.txt 中。先按 [环境配置](docs/setup.md) 创建虚拟环境，然后在仓库根目录运行：

```text
python -X utf8 -m pip install -r articles/p04-minimal-qsm/requirements.txt
python articles/p04-minimal-qsm/code/qsm_demo.py --output runs/p04-first-run
```

程序生成教学样本、估计参数、校准基准并计算“B 地区住房增加 20%”的均衡结果。B 地区人口约 41,901 人，月工资约 7,963 元，月租金约 69.51 元/平方米。所有数据和结果均为教学构造，没有真实城市估计。

缺少中文字体时，在运行命令末尾加 `--no-figures` 先核对数值。参考结果在 [results/reference](articles/p04-minimal-qsm/results/reference/)；个人输出写入 `runs/`，不混入参考结果。

## 用 Codex 学习

[Agent 练习流程](docs/agent-workflow.md) 将参考代码复现与独立实现分开。独立实现只提供完整模型约定、固定样本和文章提示词；完成后再对照结果。阅读 [FAQ](docs/faq.md) 了解数据、租金、福利和校准的含义。

课程介绍和学习目标见 [课程入口](course/README.md)。本仓库可以作为学员课前准备和课后练习材料；课程安排与报名信息以正式公告为准。

## 资料组织与维护

每篇文章的正文、代码、数据和结果放在同一个文章目录。资料入口见 [目录说明](docs/repository-map.md) 和 [文献入口](references/README.md)。项目规则在 [AGENTS.md](AGENTS.md)，后续改动通过 Git 历史与 [CHANGELOG](CHANGELOG.md) 记录。

文章保留各自署名。Python 代码采用 [MIT 许可](LICENSE-CODE)；有权授权的原创图文采用 [CC BY 4.0](LICENSE-CONTENT.md)。九张原配图可随仓库公开再分发；P02 论文图及其他第三方素材不纳入原创内容许可，来源见各图目录的 `SOURCES.md`。

联系：连享会，<lianxhcn@163.com>。
