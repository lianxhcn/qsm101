# Python 环境配置

测试环境为 Python 3.12.14；依赖版本为 numpy 2.3.5、scipy 1.17.0、pandas 2.2.3、matplotlib 3.10.8。本机另已验证 Windows、Python 3.11.14 与同一组锁定依赖 (2026-10-05)。以下命令在仓库根目录执行。

## Windows PowerShell

```text
py -3.12 -m venv .venv
.venv\Scripts\python.exe -X utf8 -m pip install -r articles/p04-minimal-qsm/requirements.txt
.venv\Scripts\python.exe articles/p04-minimal-qsm/code/qsm_demo.py --output runs/p04-first-run
```

无需激活环境也可以直接调用它的解释器。没有 `py` 命令，或 `py -3.12` 报告没有安装的 Python 时，先用 `python --version` 确认已安装版本，再用 `python -m venv .venv`。

## macOS / Linux

```text
python3 -m venv .venv
.venv/bin/python -m pip install -r articles/p04-minimal-qsm/requirements.txt
.venv/bin/python articles/p04-minimal-qsm/code/qsm_demo.py --output runs/p04-first-run
```

只在虚拟环境安装依赖，不必修改系统 Python。安装失败时先保留具体错误，再检查 Python 版本、网络或软件包索引。参考运行不会调用大模型 API；使用 Codex 编写和检查代码所需的登录及额度由自己的 Codex 环境提供。

## 中文字体

程序依次查找 Noto Sans CJK SC、Microsoft YaHei、SimHei。找到其中之一即可出图。当前环境没有这些字体时，先在运行命令末尾加 `--no-figures`，完成数值核验后再配置字体。这一分支已在本次复跑中验证；字体错误发生在数值文件写出后的出图阶段。

## 输出与输入

所有个人运行指定 `--output runs/<本次运行名称>`。结果目录中生成 input/、CSV、JSON；出图时再生成 PNG、SVG、PDF。固定参考输入在 `articles/p04-minimal-qsm/data/`，参考结果在 `results/reference/`。

参考主程序总是重新生成模拟输入，不读取你放入 data/ 的真实数据。独立实现练习读取已保存的固定输入，流程见 [Agent 练习说明](agent-workflow.md)。

## Windows 依赖文件编码

本机 pip 24.0 曾按 GBK 读取含中文注释的 UTF-8 `requirements.txt`，触发 `UnicodeDecodeError`。改用 `python -X utf8 -m pip install -r <依赖文件>` 后，四个锁定包安装成功，`python -m pip check` 通过。`PYTHONIOENCODING` 只控制标准输入输出，不能代替这里的 UTF-8 模式。无需删除中文注释或修改系统区域设置。
