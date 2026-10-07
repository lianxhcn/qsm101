# P06：交通更方便，工作会更靠近中心还是更分散？

[正文](article.md) · [模型](model.md) · [完整 Notebook](../../site/pages/m3-transport-policy.ipynb) · [固定输入](data/README.md) · [离线包](downloads/transport-workbook.zip)

所有数据和结果为教学构造。本章固定基本面，只把双向跨区广义通勤成本降低 25%，分别计算居民、就业、工资、租金与通勤。福利是工人事前毛效用指标，不是交通建设净社会福利。

在仓库根目录运行：

```text
python -X utf8 -m pip install -r articles/p06-transport-qsm/requirements.txt
python -X utf8 articles/p06-transport-qsm/code/qsm_transport_demo.py --output runs/p06-my-run
```

输出目录须为空。程序先核对固定输入、反演基准、求解政策，再完成 322 项检查。成功时 `verification.json` 中 passed 为 true。个人输出写入 runs，保留 results/reference 不动。

目录：code 为数值程序和机制图脚本，data 为固定教学输入及派生核对表，prompts 为独立练习指令，figures 保留当前配图与历史版本，results/reference 为实际运行后确认的参考输出，downloads 为离线包。

Notebook 按输入、校准、固定价格预测、均衡与核验分步展示，包含 27 个代码单元。当前正文与离线包采用 `qsm-transport-fig01-model-evolution-20261006-221849.png`，离线包只收录这一张配图。

Notebook 内嵌计算函数，不导入参考脚本；离线运行仅读取同目录 data，无需联网。完整练习包已包含图形本地副本。独立练习请使用 inputs 包，在完成前不要接触本目录参考结果。

[在线讲义](https://lianxhcn.github.io/qsm101/site/pages/m3-transport-policy.html)与下载资源由仓库统一维护。运行结果与核验记录见 results/reference；项目质量记录见仓库 logs。
