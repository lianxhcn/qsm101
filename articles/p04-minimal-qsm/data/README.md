# 教学输入说明

这两个 CSV 均为教学构造，可用于固定输入的独立实现练习。不是人口普查或真实城市调查。

## teaching-baseline.csv

| 字段 | 含义 | 单位 |
|---|---|---|
| region | A、B 地区 | 分类 |
| workers | 居住和就业一致的工人数 | 人 |
| monthly_wage | 每个工人的月工资 | 元/工人/月 |
| monthly_rent_per_m2 | 同质住房服务单位月租金 | 元/平方米/月 |
| origin | teaching_assumption | 数据性质 |

## synthetic-choice-tasks.csv

8000 条独立模拟二选一任务。字段 ln_wage_ratio=log(w_B/w_A)，ln_rent_ratio=log(r_B/r_A)，choose_B 为是否选择 B 的 0/1 值。

使用 numpy.random.default_rng(20261004)，先生成 8000 个 Uniform(-0.35,0.35) 工资差，再生成 8000 个 Uniform(-0.40,0.40) 房租差，最后按 logistic(0.12+4*(工资差-0.25*房租差)) 进行 rng.binomial(1,p) 抽样。

估计时 alpha 固定为 0.25，同时估计任务截距和 theta。任务截距不代替基准便利度。固定输入的校验值记录在已核验结果 verification.json 及交接包来源清单中。
