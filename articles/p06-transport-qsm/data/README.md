# P06 固定教学输入

所有数据为教学构造。原始两份 CSV 从交接包逐字节复制，未四舍五入。

| 文件 | 字段与单位 | SHA256 |
|---|---|---|
| teaching-central-residential-primitives.csv | region；residents (工人数)；monthly_wage (元/工人/月)；monthly_rent_per_m2 (元/平方米/月) | 2aceabb4f8969c5666a519bd380199b1f70813e7a5aded1d36762f40f7ebd06e |
| teaching-central-residential-od.csv | home_region 为行 (居住)，work_region 为列 (工作)，workers 为工人数 | 0aae343f0e2cbae123a3a07656aa682af40f976283a1aff3c1e839dec549c08c |

`teaching-central-residential-baseline.csv` 为程序生成的派生核对表：R 为居民、E 为就业、w 为工资、r 为租金、H 为平方米有效住房、Z 为生产率复合项、B 为便利度。它不是第三份原始数据，程序不读取它来反推结果。

生成顺序：给定 R=(50000,70000)、w=(10000,8200)、r=(140,100)，以 theta=4 和 tau0=ln(9)/4 计算各居住地条件工作概率，M=R*q；列和给出 E；住房出清反演 H、边际产出反演 Z、居民份额比反演 B。全部运算使用双精度，CSV 输出采用 17 位有效数字。

基准拟合不构成识别或外部验证。原始数值、行为参数、反演基本面及所有反事实均为教学构造。来源：P06 交接包；retrieved_date: 2026-10-06。
