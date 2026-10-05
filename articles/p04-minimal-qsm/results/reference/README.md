# 参考输出

本目录保留实际参考程序运行的五个结果文件，不接收个人练习输出。数据与政策均为教学构造。

| 文件 | 内容 |
|---|---|
| synthetic-estimates.csv | 二元 Logit 模拟参数估计、IID 标准误与区间 |
| calibrated-parameters.json | 给定行为参数后反演的 H、Z、B |
| equilibrium-results.csv | 基准、B 住房扩建均衡，以及明确标注 NOT_GE 的固定价格预测 |
| sensitivity-results.csv | 每组 theta、beta 重新校准后的政策结果 |
| verification.json | 经济条件、共同冲击检查、版本和输入校验值 |

主情景是 B_housing_plus20_GE。W 为全体模型工人的事前福利指数，不是每个居民收入变化或政策净社会收益。敏感性曲线是参数情景比较，不是置信区间。
