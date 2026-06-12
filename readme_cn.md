# RFM 关联规则 — 体育零售案例分析

基于 Python 的体育用品零售客户分析项目，覆盖 **RFM 客户分层、K-Means 聚类、关联规则挖掘（Apriori）** 三大分析模块，结合 Tableau 构建销售全景看板。

## 环境

| 组件 | 版本/配置 |
|---|---|
| Python | 3.x |
| MySQL | 8.x（源数据导入） |
| Tableau Desktop | 2026.1.2 |
| 数据量 | ~57 万行购物篮明细，~1.8 万客户 |

## 项目结构

```
.
├── database/
│   ├── sqlexport/                # MySQL 导出 CSV
│   │   ├── v_basket_detail.csv       # 购物篮明细（~57 万行）
│   │   └── v_customer_features.csv   # 客户 RFM 特征（~1.8 万行）
│   └── pyexport/                 # Python 分析导出
│       ├── ml_customer_with_cluster.csv  # K-Means 聚类结果
│       └── ml_cluster_profile.csv       # 聚类画像汇总
├── notebooks/                    # Jupyter Notebook 分析
├── report/                       # 分析报告
├── BI/                           # Tableau 看板
│   ├── 260612_DA_BI.twb          # Tableau 工作簿
│   ├── 260612_DA_BI.pdf          # 看板导出
│   └── DA_BI.png                 # 看板截图
├── readme_cn.md                  # 本文件
├── readme_en.md                  # English version
└── requirements.md               # 分析需求说明
```

## 三大分析模块

| # | 模块 | 方法 | 核心成果 |
|---|---|---|---|
| 1 | **RFM 客户分层** | Recency / Frequency / Monetary 三维评分 | 客户价值分群，识别高价值与流失风险客户 |
| 2 | **K-Means 聚类** | 标准化 RFM → K-Means → 聚类画像 | 2 群聚类（高价值活跃 / 沉睡客户），含 size_pct 占比 |
| 3 | **关联规则挖掘** | Apriori 算法 → 支持度/置信度/提升度 | 购物篮商品关联规则，支撑交叉销售策略 |

## BI 看板

基于本项目数据构建的 **Tableau 销售全景与客户分析看板**（1 页），覆盖 KPI 总览、月度销售趋势、RFM 客户散点图和客户群价值对比共 4 大类组件。

![BI 看板](BI/DA_BI.png)

> 工作簿文件：[BI/260612_DA_BI.twb](BI/260612_DA_BI.twb)

### 看板组件

| 组件 | 类型 | 说明 |
|------|------|------|
| KPI 卡片行 | 文本卡片 | 总销售额、总订单数、总客户数、客单价、SKU 数 |
| 月度销售趋势 | 双轴组合图（柱+线） | 柱=销售额，线=订单数，按月聚合 |
| RFM 散点图 | 散点图 | X=R值(活跃度)，Y=M值(消费力)，颜色=客户群，大小=F值(购买频次) |
| 客户群对比 | 条形图 | 沉睡客户 vs 高价值活跃，各指标上下对比 |

## 快速开始

### 1. 数据导入 MySQL

```bash
mysql -u root < database/create_views.sql
```

### 2. 运行 Python 分析

```bash
pip install -r requirements.txt
jupyter notebook notebooks/
```

### 3. 打开 Tableau 看板

Tableau Desktop → 打开 → `BI/260612_DA_BI.twb`

## 许可

MIT
