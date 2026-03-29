# 数据词典

## 1. 原始表

### order.csv（销售明细表）
| 字段名 | 数据类型 | 说明 | 示例值 |
|--------|----------|------|--------|
| 订单日期 | date | 下单日期 |2016/1/1 |
| 年份 | int | 下单年份 | 2016 |
| 订单数量 | int | 无意义数据（均为1） | 1 |
| 产品ID | int | 链接产品表的外键| 528 |
| 客户ID | string | 链接客户表的外键 | 14432BA |
| 交易类型 | int | 无意义数据（均为1） | 1 |
| 销售区域ID | int | 销售区域数字代码 | 4 |
| 销售大区 | string | 销售大区名称 | 西南区 |
| 国家 | string | 销售国家名称 | 中国 |
| 区域 | string | 销售国家所属区域 | 大中华区 |
| 产品类别 | string | 产品所属大类 | 配件 |
| 产品型号名称 | string | 细分类别的不同型号 | Rawlings Heart of THE Hide-11.5 |
| 产品名称 | string | 产品细分类别 | 棒球手套 |
| 产品成本 | float | / | 500 |
| 利润 | float | 产品单价 - 产品成本 | 1000 |
| 单价 | float | / | 1500 |
| 销售金额 | float | 每一单的销售金额 | 1500 |

### product.csv（产品信息表）
| 字段名 | 数据类型 | 说明 | 示例值 |
|--------|----------|------|--------|
| 产品类别| string| 产品所属大类 | 配件 |
| 产品id | int | 产品唯一标识 | 528 |
| 产品型号 | string | 细分类别的不同型号 | BA-180 |
| 产品名称 | string | 产品细分类别 | 棒球手套 |

### customer.csv（客户ID表）
| 字段名 | 数据类型 | 说明 | 示例值 |
|--------|----------|------|--------|
| 客户id | string | 客户唯一标识 | 30410BA |

### date.csv（日期表）
| 字段名 | 数据类型 | 说明 | 示例值 |
|--------|----------|------|--------|
| 日期 | date| 年月日 | 2013/7/1 |
| 年度| int | 仅年份 | 2013 |
| 季度 | string | 仅季度 | Q3 |
| 月份 | int | 仅月份 | 7 |
| 日 | int | 仅当月第几日 | 1 |
| 年度季度 | date | 年度+季度 | 2013Q3 |
| 年度月份 | date | 年度+月份 | 201307 |
| 星期几 | int | 星期内的天数 | 1 |


## 2. 衍生表

### (1). rfm_groups（RFM 聚类结果）
| 字段名            | 数据类型  | 说明                | 计算方式                                           |
| -------------- | ----- | ----------------- | ---------------------------------------------- |
| RFM_score      | int   | RFM总分，R、F、M三项得分之和 | R_score + F_score + M_score，每个维度按五分位数打分（R反向打分） |
| customer_count | int   | 该RFM总分对应的客户数量     | 按RFM_score分组计数                                 |
| avg_recency    | float | 该组客户的平均最近购买间隔天数   | mean(recency_days)                             |
| avg_frequency  | float | 该组客户的平均购买次数       | mean(frequency)                                |
| avg_monetary   | float | 该组客户的平均总消费金额      | mean(monetary)                                 |

### (2). ml_customer_with_cluster.csv（带簇标签的客户表）
|字段名|数据类型|说明|计算方式|
|---|---|---|---|
|customer_id|string|客户唯一标识|原始客户ID|
|recency_days|int|最近购买间隔天数|基准日期减去客户最后一次购买日期|
|frequency|int|购买次数（基于购物篮）|客户不同购物篮ID的计数|
|monetary|float|总消费金额|客户所有订单销售额之和|
|cluster|int|K-Means聚类分配的簇编号|K-Means聚类结果|
|cluster_name|string|簇的业务名称|根据RFM特征人工命名（如“高价值活跃”“沉睡客户”等）|

### (3).  ml_cluster_profile.csv（簇特征）
|字段名|数据类型|说明|计算方式|
|---|---|---|---|
|cluster|int|簇编号|K-Means聚类结果，为索引列|
|recency_days|float|该簇客户的平均最近购买间隔天数|簇内所有客户recency_days的均值|
|frequency|float|该簇客户的平均购买次数|簇内所有客户frequency的均值|
|monetary|float|该簇客户的平均总消费金额|簇内所有客户monetary的均值|
|size|int|该簇包含的客户数量|簇内客户计数|
|size_pct|float|该簇客户数占全体客户的比例（%）|(size / 总客户数) * 100|
|cluster_name|string|簇的业务名称|同ml_customer_with_cluster中的cluster_name|

### (4). ml_strong_rules.csv（强规则表）
|字段名|数据类型|说明|计算方式|
|---|---|---|---|
|antecedents|frozenset|前件项集（产品ID集合）|Apriori算法生成|
|consequents|frozenset|后件项集（产品ID集合）|Apriori算法生成|
|antecedent support|float|前件的支持度|包含前件的购物篮数 / 总购物篮数|
|consequent support|float|后件的支持度|包含后件的购物篮数 / 总购物篮数|
|support|float|规则的支持度|同时包含前后件的购物篮数 / 总购物篮数|
|confidence|float|规则的置信度|support(前件∪后件) / support(前件)|
|lift|float|规则的提升度|confidence / support(后件)|
|leverage|float|杠杆率|support(前件∪后件) - support(前件)*support(后件)|
|conviction|float|确信度|(1 - support(后件)) / (1 - confidence)|
|ante_len|int|前件中的产品数量|len(antecedents)|
|conseq_len|int|后件中的产品数量|len(consequents)|
|ante_names|list|前件产品名称列表（产品细分种类）|根据产品ID映射product_name|
|conseq_names|list|后件产品名称列表（产品细分种类）|根据产品ID映射product_name|
|ante_ids_names|list|前件产品标识列表（ID-名称）|格式：`{product_id}-{product_name}`|
|conseq_ids_names|list|后件产品标识列表（ID-名称）|格式：`{product_id}-{product_name}`|

### (5). ml_product_communities.csv（产品社区表）
|字段名|数据类型|说明|计算方式|
|---|---|---|---|
|product_id|int|产品唯一标识|原始产品ID|
|community|int|Louvain社区检测分配的社区编号|基于产品共现网络图计算|
|product_name|string|产品细分种类名称|产品信息表映射|

