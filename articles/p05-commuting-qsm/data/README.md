# 教学输入字段与生成规则

两份 CSV 均为教学构造，以 UTF-8 BOM 保存，无任何真实城市观察。固定输入与生成输入的 SHA256 见参考 verification.json。

## 1. teaching-baseline.csv

四行顺序为 AA、AB、BA、BB；home_region 为居住地，work_region 为工作地。commuters 为该格人数，residents 为对应行合计，employment 为对应列合计；重复边际字段不能跨四行直接相加。monthly_wage 为工作地月工资 (元/工人/月)，monthly_rent_per_m2 为居住地单位月租金 (元/平方米/月)。alpha、beta、theta 为教学行为参数，tau 为该格通勤效用成本 (不扣收入)，total_workers 为固定总工人数，data_origin 声明构造性质。H 与 Z 从基准反演，见 calibrated-parameters.json，不是独立观察数据。

## 2. synthetic-joint-choice-tasks.csv

共有 20000 个选择集、80000 行。choice_set_id 从 0 开始，每组顺序固定为 AA、AB、BA、BB。home_region、work_region 是两个区位；commute_indicator 为跨区指示变量；commute_multiplier 为效用成本强度，本地 0、跨区 Uniform(0.5,1.5)。log_wage 是工作地月工资自然对数，log_rent 是居住地单位月租金自然对数。chosen 为选择指示，同一选择集恰有一个 1；data_origin 始终为 synthetic_choice_experiment。

随机数生成器为 numpy.random.default_rng(20261005)。按顺序生成 (20000,2) 的工资扰动 Uniform(-0.35,0.35)、租金扰动 Uniform(-0.40,0.40)、通勤强度 Uniform(0.5,1.5)，最后生成 20000 个 Uniform(0,1)，通过累计四选项概率抽取选择。工资和租金对数基数分别为 ln(9600)、ln(120)，同一任务共享工作地工资和居住地租金，三种属性在任务间独立生成。

概率为 softmax(theta*(log_wage-alpha*log_rent)-theta*tau*commute_multiplier)。模拟真值 alpha=.25、theta=4、tau=ln(9)/4。拟合变量是 log_wage-alpha*log_rent 和负的 commute_multiplier，不能把 commute_indicator 误当作连续强度。估计 theta 与 theta*tau，tau 标准误用含协方差的 Delta 法。标准误基于独立任务，不是将同组四个选项当成四个独立工人。

模拟选择样本只检验估计程序。均衡基准仍使用真值，不能把样本估计写成真实城市通勤参数。固定输入只用于第一次独立实现对照；主程序会重新按规则生成同一份样本。
