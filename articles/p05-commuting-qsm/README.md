# 两地区模型的通勤扩展

[正式正文](article.md) · [可执行 Notebook](../../site/pages/commuting.ipynb) · [离线练习包](downloads/commuting-workbook.zip) · [模型说明](model.md)

本文区分居住地与工作地，比较 B 地区住房增加 20% 后居民、就业、工资、租金和通勤流量的调整。全部数据为教学构造，不对应真实城市；福利仅为工人事前指数，不包含住房或交通建设成本。

## 1. 两条学习路径

网页与下载 Notebook 同源，Notebook 含完整解释、模型函数、估计、校准、求解、核验、图形和练习。固定输入优先读取本地，不依赖参考脚本。使用离线包时先解压，保留 data/ 目录；Python 依赖需要提前安装。中文绘图需微软雅黑、黑体或 Noto Sans CJK SC。

参考脚本用于复现和对照。在仓库根目录运行：

```text
python -X utf8 -m pip install -r articles/p05-commuting-qsm/requirements.txt
python -X utf8 articles/p05-commuting-qsm/code/qsm_commuting_demo.py --output runs/p05-my-run
```

脚本按固定种子重新生成同一份教学样本，Notebook 则直接读取固定 CSV。脚本输出目录非空时拒绝覆盖；没有中文字体时可以添加 --no-figures 先核对数值。两条路径主参数均使用教学真值，估计参数只用于演示及指定敏感性情景。

## 2. 数据与结果

[数据说明](data/README.md) 给出字段、单位、生成顺序、随机种子和样本性质；[参考结果](results/reference/README.md) 保存估计、校准、均衡、通勤、敏感性和核验。theta/beta 网格重新匹配完整 OD；tau 网格只匹配对称总量，允许基准通勤份额改变。每组政策内基本面固定。

[实现提示词](prompts/01-implement.md) 和 [核验提示词](prompts/02-verify.md) 用于另一项独立练习。已执行的独立会话与参考实现数值一致；Notebook 的执行另作记录，不冒充再次独立重建。

正式正文统一在 article.md，准备阶段双稿已归档。网站导航和资源已在本地整合，远程发布按用户授权另行执行。原无通勤模型保持不变。

## 3. Agent 独立实现练习

正文与在线 Notebook 提供从零实现、估计与校准检查、独立核验三段完整提示词。[练习说明](prompts/README.md) 和 [只含模型与固定输入的练习包](downloads/commuting-agent-inputs.zip) 可用于新会话。新版提示词已经按模型约定核对，尚未再次进行新会话盲写试跑。
