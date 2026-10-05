# 两地区 QSM：Agent 练习

本目录仅含模型说明、固定教学输入和提示词，不含参考实现或政策结果。所有数据均为教学构造，不对应真实城市。

1. 在新的练习目录解压，并在该目录新建 Agent 会话。
2. 告诉 Agent 可用的 Python 环境，先读取 model.md 和 data/README.md。
3. 复制 prompts/01-implement.md 完成首次实现与实际运行。
4. 用 prompts/03-estimate-calibrate.md 检查估计与校准，再用 prompts/02-verify.md 核验经济条件。
5. 首次实现结束后才提供参考结果作对照。代码写入 code/，输出写入新的 results/ 子目录。

没有运行权限或依赖缺失时，应报告未验证，不得声称已跑通。不要求联网、安装全局软件或发布结果。SHA256 输入清单见 input-manifest.json。

新增提示词是在历史独立试跑基础上的教学细化，本包不声称已经再次完成新会话盲写测试。

[下载练习包](../downloads/commuting-agent-inputs.zip)。
