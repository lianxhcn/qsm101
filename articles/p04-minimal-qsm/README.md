# P04 运行与材料说明

正文在本目录的 article.md。教学数据不对应真实城市，总劳动人口固定，居住地与工作地一致。理论约定见 [model.md](model.md)。

## 运行

在仓库根目录配置虚拟环境后执行：

```text
python -m pip install -r articles/p04-minimal-qsm/requirements.txt
python articles/p04-minimal-qsm/code/qsm_demo.py --output runs/p04-first-run
```

没有中文字体则添加 `--no-figures`。参考程序按已知规则重新生成模拟任务，不读取 data/ 中的 CSV；独立实现按提示词读取固定输入。数据字段说明见 [data/README.md](data/README.md)。

## 结果对照

- theta 约 3.92422015，IID 标准误约 0.12280278。
- B 地区住房增加 20% 后：人口约 41900.60761，月工资约 7962.94936，租金约 69.51092。
- 工人事前福利指数增加约 1.88396%，没有扣除建设成本。
- results/reference/ 保存参数、结果、敏感性和核验记录；它们来自实际参考运行。

图片保留 PNG、SVG 和 PDF 三种格式。文件名中的 `20261004-2330` 是原结果生成标记，本次正文修改没有改变模型和参考图。自己的运行保存在 runs/。

## 提示词练习

[提示词说明](prompts/README.md) 给出独立实现和继续核验的方法。参考程序和原始提示词的独立实现均已实际运行并分别核验；环境问题与复测记录见 [Agent 练习流程](../../docs/agent-workflow.md)。
