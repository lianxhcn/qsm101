# P05 已验收参考结果

来源：2026-10-05 的 runs/p05-final-run/。所有输入、估计和均衡为教学构造。当前参考程序通过 484 项数值检查；数值容差、环境版本和输入哈希逐项保存在 verification.json。

主政策查看 equilibrium-results.csv 中 scenario=B_housing_plus20 的 A/B 两行。restricted_B_housing_plus20 为掩码模型；不同模型福利增幅均相对于各自基准。跨区人数查看 commuting-matrix-results.csv，行是居住地、列是工作地。敏感性表 calibration_target 区分完整 OD 与总量基准。

synthetic-estimates.csv 记录真值、估计、标准误、置信区间、种子和样本量；estimation-diagnostics.json 记录收敛状态、得分、协方差和信息矩阵特征值。solver-diagnostics.json 保留每组初值及 hybr 失败后的备用求解记录。figure-manifest.json 对应公开 figures/ 下的新时间戳图形。

这些检查验证代码是否实现给定方程，不是模型的外部实证检验。参考结果不应被个人试跑覆盖。
