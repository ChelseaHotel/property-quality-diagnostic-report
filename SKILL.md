---
name: property-quality-diagnostic-report
description: 将物业品质检查、品质整改或整改单明细 Excel 预检、标准化并生成离线 HTML 诊断报告，支持字段识别、问题口径配置、整改率与扣分分析、业务板块诊断、待整改明细、三级脱敏和敏感信息扫描。用于用户要求分析物业品检结果、整改记录、品质工单，或将相关 Excel 转换为可视化 HTML、管理复盘报告及可公开的脱敏示例时。
---

# 物业品质诊断报告

## 输出

生成单文件离线 HTML，包含核心指标、动态管理结论、板块诊断、检查批次、待整改清单、全量筛选和打印样式。

## 标准流程

1. 先运行预检，不要直接生成：

   ```bash
   <python> <skill>/scripts/build_report.py <输入.xlsx> --preflight-only
   ```

2. 检查工作表、表头、字段映射、项目分布、状态、日期、重复工单、问题口径、敏感字段和 `confirmation_required`。
3. 出现多个项目时必须使用 `--project`；不得静默合并后使用众数项目名。
4. 文件名与表内项目名冲突、存在重复工单、未知状态或关键字段歧义时，优先通过参数或配置消除；人工核实后才使用 `--confirm-preflight`。
5. 生成报告：

   ```bash
   <python> <skill>/scripts/build_report.py <输入.xlsx> --out <目录>
   ```

   默认使用 `local`，完整保留用户上传文件中的项目、工单、人员、问题描述、措施和时间信息。

6. 提交 Skill 源码或公开示例到 GitHub 前运行：

   ```bash
   <python> <skill>/scripts/scan_sensitive.py <输出目录>
   ```

## 隐私模式

- `local`（默认）：忠实保留用户上传文件中的项目、工单、提交人、问题描述及其他业务信息。
- `safe`：仅在用户明确要求脱敏、匿名化或内部分享版时使用；匿名化工单和人员，并清理常见定位信息。
- `public`：仅在制作 GitHub 公开示例时使用，只接受同时传入 `--synthetic` 的合成数据。

脱敏要求约束的是 Skill 源码、测试数据和 GitHub 内容，不得默认改变用户上传文件所生成的业务报告。公开模式不得用于真实生产数据。需要调整规则时阅读[隐私规范](references/privacy-policy.md)。

## 问题口径

默认使用 `problem-or-score`：问题描述非空且不属于“无问题”文本，或扣罚分值大于 0。可通过 `--issue-policy` 切换：

- `problem-or-score`
- `problem-only`
- `score-only`
- `status-based`

详细定义和状态标准化见[指标口径](references/metric-policy.md)。

## 输入与配置

- 使用 `--sheet`、`--header-row` 修正工作表或表头识别。
- 使用 `--project` 筛选单个项目，使用 `--project-name` 控制报告标题。
- 使用 `--config <json>` 扩展字段别名、状态别名和无问题文本。
- 使用 `--title` 覆盖完整报告标题。
- 不要依赖固定列序号、固定项目名称、固定日期或固定 KPI。

字段要求及配置格式见[输入结构](references/input-schema.md)。

## 高风险阻断

以下情况停止生成：

- 无法识别整改状态、问题描述或业务板块。
- 筛选后没有记录或没有实际问题。
- 多项目输入未指定项目。
- 公开模式未明确声明合成数据。
- 预检仍有需确认风险且未传 `--confirm-preflight`。

## 验证

生成后必须核对：

- 全量记录、实际问题、已整改、待整改、扣分和整改率能够从明细重算。
- 各板块合计与总体一致。
- 搜索、筛选、详情弹窗和打印可用。
- 桌面端、移动端无整页横向溢出。
- 板块诊断左右五行的垂直坐标差不超过 1px。
- HTML 不加载外部网络资源。

修改解析、口径或模板后运行：

```bash
<python> <skill>/tests/test_report.py
```

若环境提供 Playwright，再运行：

```bash
<node> <skill>/scripts/verify_report.mjs <输出.html> --out <截图目录>
```
