# 提示词长期规范与检查工具验收

日期：2026-10-07。范围：先确定规则与检查工具，不实施读者页面。

## 已完成

- AGENTS.md 接入已批准规范；docs/site-standards.md 第 11–13 节固定两类提示词、材料、占位符、适用边界、全站配色与迁移验收顺序。
- site/prompt-contract.json 保存两类名称、结构字段、指南目标路径、语义颜色和人工检查要求。状态明确为 approved-pending-page-migration。
- site/README.md 固定组件属性、模板/示例分开、导出约定、命令和当前实现限制。
- 新增 site/check_prompt_contract.py，只读、标准库、不联网、不执行模型。现有 check_site.py 增加 current/audit/strict 三种明确范围，不弱化原有页面检查。
- 新增 site/tests/test_prompt_contract.py，覆盖合格完整样例、分类缺失、折叠、占位符、网站依赖、填写示例同步、低对比度、过期 ZIP、缺少指南、清单哈希及独立输入包混入代码。

## 实际验证

- 22 项单元与完整样例测试全部通过。
- 现有页面检查通过；新版 audit 退出 0 并明确显示 PENDING；strict 退出 1，准确拒绝尚未改造的页面。
- 当前新版盘点有 73 条缺口记录，包含源稿、HTML 和下载副本的重复位置。主要是现有 16 张卡片尚无分类属性、指南和离线指南尚未建立、CSS 尚未声明批准的语义变量；不是模型故障，也不是新版验收通过。
- 对 491 个受保护文件逐字节校验，修改数为 0，覆盖页面、样式、交互脚本、生成脚本、下载包和已渲染网站。
- 命令采用 python -B 避免缓存写入。测试的临时站点仅位于自动清理的临时目录；测试不会改写真实页面。

## 后续实施门槛

按规范完成指南、卡片、样式、复制目标、导出与下载、FAQ/学习路线后，运行 python -B site/check_site.py --prompt-contract strict。然后做新会话上下文审阅、经济学条件审阅和浏览器实际交互/颜色检查。自动检查不能证明经济学正确，也不能代替 Agent 独立试跑。

完成迁移后将 CI 检查切为 strict；本轮未修改部署配置。未修改模型、数据和参考结果，未发布。

详细证据位于 Task/prompt-contract-20261007/：tests.log、strict.log、audit.log、audit.json、protected-before.json、protected-after.json。
