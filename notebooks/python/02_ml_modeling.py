# -*- coding: utf-8 -*-
"""
机器学习分析脚本（客户聚类 + 关联规则挖掘）
/*
    目录：
    第一部分：客户聚类（K-Means） 
    第二部分：关联规则挖掘与产品网络图 
*/
    输入：v_customer_features.csv, v_basket_detail.csv, v_product_info.csv
    输出：ml_customer_with_cluster.csv, ml_cluster_profile.csv, ml_association_rules.csv, ml_product_communities.csv,
      ml_elbow.png, ml_cluster_radar.png, ml_cluster_scatter.png, ml_product_network.png 等
"""

#-----------------------------导入库 ------------------------------------
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from mlxtend.frequent_patterns import apriori, association_rules
import networkx as nx
import community as community_louvain
import os
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False

# -------------------------路径配置 ----------------------------------------
SQL_EXPORT_DIR = r'D:\WORK\database\sqlexport'
PYEXPORT_DIR = r'D:\WORK\database\pyexport'
PHOTOS_DIR = r'D:\WORK\report\photos'

print("="*60)
print("机器学习分析脚本开始执行")
print("="*60)

# ---------- 第一部分：客户聚类（K-Means） ----------
print("\n\n" + "="*60)
print("第一部分：客户聚类分析（基于RFM）")
print("="*60)

# 1.1 加载客户特征数据
# (1) 读取CSV
cust_path = os.path.join(SQL_EXPORT_DIR, 'v_customer_features.csv')
df_cust = pd.read_csv(cust_path)
print("\n一.1 客户特征数据加载成功")
print("数据形状:", df_cust.shape)
print("前两行:\n", df_cust.head(2))
print("字段列表:", df_cust.columns.tolist())

# 1.2 数据预处理
# (1) 提取RFM指标（确认字段名）
rfm_cols = ['recency_days', 'frequency', 'monetary']
X = df_cust[rfm_cols].copy()

# (3) 描述统计
print("\n一.2 RFM描述统计:")
print(X.describe())

# (4) 标准化（使各指标量纲一致）
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
X_scaled = pd.DataFrame(X_scaled, columns=rfm_cols)

print("\n标准化完成，示例数据:")
print(X_scaled.head(2))

# 1.3 确定最佳聚类数 K
# (1) 计算不同K值的SSE和轮廓系数
sse = []
sil_scores = []
K_range = range(2, 9)  # 2-8类

for k in K_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X_scaled)
    sse.append(kmeans.inertia_)
    sil_scores.append(silhouette_score(X_scaled, labels))

# (2) 绘制肘部图
plt.figure(figsize=(12, 5))
plt.subplot(1, 2, 1)
plt.plot(K_range, sse, 'bo-')
plt.xlabel('K值')
plt.ylabel('SSE')
plt.title('肘部法则确定K')

plt.subplot(1, 2, 2)
plt.plot(K_range, sil_scores, 'ro-')
plt.xlabel('K值')
plt.ylabel('轮廓系数')
plt.title('轮廓系数')
plt.tight_layout()
plt.savefig(os.path.join(PHOTOS_DIR, 'ml_elbow.png'), dpi=150)
plt.show()
print("\n一.3 肘部图已保存至 ml_elbow.png")

# (3) 自动选择K（取轮廓系数最大的K，兼顾SSE拐点）
best_k = K_range[np.argmax(sil_scores)]
print(f"\n根据轮廓系数，推荐K={best_k}")

# 1.4 执行K-Means聚类
kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
cluster_labels = kmeans.fit_predict(X_scaled)

# 将簇标签加入原始数据
df_cust['cluster'] = cluster_labels

# 1.5 聚类结果分析
# (1) 计算各簇RFM均值
cluster_profile = df_cust.groupby('cluster')[rfm_cols].mean().round(2)
cluster_profile['size'] = df_cust.groupby('cluster').size()
cluster_profile['size_pct'] = (cluster_profile['size'] / len(df_cust) * 100).round(2)

print("\n一.5 各簇特征统计:")
print(cluster_profile)

# (2) 为簇命名（根据业务经验）
# 命名规则：recency小、frequency大、monetary大 -> 高价值；recency大 -> 沉睡；等
cluster_names = {}
for i in range(best_k):
    row = cluster_profile.loc[i]
    if row['recency_days'] < cluster_profile['recency_days'].median() and row['frequency'] > cluster_profile['frequency'].median():
        name = '高价值活跃'
    elif row['frequency'] == 1 and row['monetary'] < cluster_profile['monetary'].median():
        name = '新客/低频低消'
    elif row['recency_days'] > cluster_profile['recency_days'].quantile(0.75):
        name = '沉睡客户'
    elif row['frequency'] > cluster_profile['frequency'].quantile(0.75):
        name = '高频忠诚'
    else:
        name = '普通客户'
    cluster_names[i] = name

df_cust['cluster_name'] = df_cust['cluster'].map(cluster_names)
cluster_profile['cluster_name'] = [cluster_names[i] for i in cluster_profile.index]

print("\n簇命名结果:")
print(cluster_profile[['cluster_name', 'size', 'size_pct']])

# 1.6 可视化
# (1) 雷达图展示各簇RFM特征（标准化后的值便于比较）
from math import pi

# 标准化后的簇均值
cluster_scaled = pd.DataFrame(kmeans.cluster_centers_, columns=rfm_cols)
cluster_scaled['cluster'] = range(best_k)
cluster_scaled = cluster_scaled.merge(cluster_profile[['cluster_name']], left_on='cluster', right_index=True)

# 绘制雷达图
fig, axes = plt.subplots(1, best_k, figsize=(4*best_k, 4), subplot_kw=dict(projection='polar'))
if best_k == 1:
    axes = [axes]
for i, ax in enumerate(axes):
    # 选择第i个簇的数据
    data = cluster_scaled.iloc[i][rfm_cols].values.flatten().tolist()
    # 闭合数据
    data += data[:1]
    angles = [n / len(rfm_cols) * 2 * pi for n in range(len(rfm_cols))]
    angles += angles[:1]
    ax.plot(angles, data, 'o-', linewidth=2)
    ax.fill(angles, data, alpha=0.25)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(rfm_cols)
    ax.set_title(cluster_scaled.iloc[i]['cluster_name'])
plt.tight_layout()
plt.savefig(os.path.join(PHOTOS_DIR, 'ml_cluster_radar.png'), dpi=150)
plt.show()

# (2) 散点图（用前两个主成分降维）
from sklearn.decomposition import PCA
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)

plt.figure(figsize=(10, 8))
scatter = plt.scatter(X_pca[:, 0], X_pca[:, 1], c=cluster_labels, cmap='viridis', alpha=0.6)
plt.colorbar(scatter)
plt.xlabel('PCA1')
plt.ylabel('PCA2')
plt.title('客户聚类散点图（PCA降维）')
plt.tight_layout()
plt.savefig(os.path.join(PHOTOS_DIR, 'ml_cluster_scatter.png'), dpi=150)
plt.show()

# 1.7 保存结果
# (1) 带簇标签的客户表
cust_cluster = df_cust[['customer_id', 'recency_days', 'frequency', 'monetary', 'cluster', 'cluster_name']]
cust_cluster.to_csv(os.path.join(PYEXPORT_DIR, 'ml_customer_with_cluster.csv'), index=False)
# (2) 簇特征表
cluster_profile.to_csv(os.path.join(PYEXPORT_DIR, 'ml_cluster_profile.csv'))

print("\n一.7 客户聚类结果已保存至:")
print(f"  - {os.path.join(PYEXPORT_DIR, 'ml_customer_with_cluster.csv')}")
print(f"  - {os.path.join(PYEXPORT_DIR, 'ml_cluster_profile.csv')}")


# ---------- 第二部分：关联规则挖掘与产品网络图 ----------
print("\n\n" + "="*60)
print("第二部分：关联规则挖掘与产品网络图")
print("="*60)

# 2.1 加载数据
basket_path = os.path.join(SQL_EXPORT_DIR, 'v_basket_detail.csv')
prod_info_path = os.path.join(SQL_EXPORT_DIR, 'v_product_info.csv')

df_basket = pd.read_csv(basket_path)
df_prod = pd.read_csv(prod_info_path)

print("\n二.1 数据加载成功")
print("购物篮明细表形状:", df_basket.shape)
print("产品信息表形状:", df_prod.shape)

# 2.2 构建购物篮矩阵
# (1) 确保 basket_id 和 product_id 无缺失
df_basket = df_basket.dropna(subset=['basket_id', 'product_id'])

# (2) 同一购物篮内同一产品去重
df_basket_unique = df_basket.drop_duplicates(subset=['basket_id', 'product_id'])

# (3) 创建透视表（行=basket_id，列=product_id，值=1/0）
basket_matrix = df_basket_unique.pivot_table(index='basket_id', columns='product_id', aggfunc='size', fill_value=0)
basket_matrix = (basket_matrix > 0).astype(int)

print("\n二.2 购物篮矩阵构建完成")
print("矩阵形状:", basket_matrix.shape)
print("购物篮数量:", basket_matrix.shape[0])
print("产品种类数:", basket_matrix.shape[1])

# 2.3 频繁项集挖掘
# (1) 设置最小支持度（根据数据量级调整，这里取0.02作为起始）
min_support = 0.02
frequent_itemsets = apriori(basket_matrix, min_support=min_support, use_colnames=True)

# (2) 添加项集长度列
frequent_itemsets['length'] = frequent_itemsets['itemsets'].apply(len)

print("\n二.3 频繁项集挖掘结果")
print("频繁项集总数:", len(frequent_itemsets))
print("各长度分布:\n", frequent_itemsets['length'].value_counts().sort_index())
print("示例（前5）:\n", frequent_itemsets.head())

# 2.4 关联规则生成
# (1) 设置最小置信度（取0.5）
min_confidence = 0.5
rules = association_rules(frequent_itemsets, metric='confidence', min_threshold=min_confidence)

# (2) 添加前后件长度
rules['ante_len'] = rules['antecedents'].apply(len)
rules['conseq_len'] = rules['consequents'].apply(len)

# (3) 按提升度排序
rules = rules.sort_values('lift', ascending=False).reset_index(drop=True)

print("\n二.4 关联规则生成")
print("规则总数:", len(rules))
print("提升度>2的规则数:", len(rules[rules['lift'] > 2]))
print("示例（前5）:\n", rules[['antecedents','consequents','support','confidence','lift']].head())

# 2.5 添加产品标识（ID+名称，确保唯一性）
# (1) 建立产品ID到标识的映射字典
prod_map = df_prod.set_index('product_id').apply(
    lambda row: f"{row.name}-{row['product_name']}", axis=1
).to_dict()
# 处理可能出现的缺失名称
prod_map = {k: (v if pd.notna(v) else f"产品{k}") for k, v in prod_map.items()}

def itemset_to_ids_names(itemset):
    """将frozenset转换为包含ID和名称的字符串列表"""
    return [prod_map.get(pid, f"未知{pid}") for pid in itemset]

rules['ante_ids_names'] = rules['antecedents'].apply(itemset_to_ids_names)
rules['conseq_ids_names'] = rules['consequents'].apply(itemset_to_ids_names)

# (2) 筛选强规则（提升度>2且置信度>0.6）作为重点
strong_rules = rules[(rules['lift'] > 2) & (rules['confidence'] > 0.6)]
print("\n强规则数量:", len(strong_rules))

# 打印示例时使用新的标识列
print("示例（前5）:\n", rules[['ante_ids_names','conseq_ids_names','support','confidence','lift']].head())

# 2.6 产品网络图构建
# (1) 构建产品共现矩阵（基于购物篮）
# 方法：对每个购物篮，两两产品组合计数
from collections import defaultdict
cooccur = defaultdict(int)

# 只考虑至少出现过一定次数的产品，以减少计算量（可选）
# 这里先使用所有产品
product_ids = basket_matrix.columns
basket_array = basket_matrix.values

# 遍历每个购物篮
for i in range(basket_array.shape[0]):
    items = product_ids[basket_array[i] == 1]
    for a in items:
        for b in items:
            if a < b:  # 避免重复计数
                cooccur[(a, b)] += 1

# (2) 构建网络图
G = nx.Graph()
for (a, b), weight in cooccur.items():
    if weight >= 2:  # 至少共同出现2次才连边，减少噪声
        G.add_edge(a, b, weight=weight)

print("\n二.6 产品共现网络")
print("节点数:", G.number_of_nodes())
print("边数:", G.number_of_edges())

# (3) 社区检测（Louvain算法）
partition = community_louvain.best_partition(G)
community_df = pd.DataFrame(list(partition.items()), columns=['product_id', 'community'])
# 添加产品名称
community_df['product_name'] = community_df['product_id'].map(prod_map)
print("\n社区数量:", community_df['community'].nunique())

# (4) 绘制网络图
plt.figure(figsize=(14, 10))
pos = nx.spring_layout(G, seed=42)

# 获取所有社区并分配颜色
communities = sorted(set(partition.values()))
cmap = plt.cm.tab20
colors = {c: cmap(i / len(communities)) for i, c in enumerate(communities)}

# 按社区绘制节点，每个社区添加图例标签
for com in communities:
    nodes_in_com = [node for node in G.nodes() if partition[node] == com]
    node_sizes = [G.degree(node) * 50 for node in nodes_in_com]
    nx.draw_networkx_nodes(
        G, pos,
        nodelist=nodes_in_com,
        node_color=[colors[com]],
        node_size=node_sizes,
        alpha=0.8,
        label=f'社区 {com}'
    )

# 绘制边
nx.draw_networkx_edges(G, pos, alpha=0.3)

# 绘制节点标签
labels = {}
for node in G.nodes():
    name = prod_map.get(node, str(node))
    if len(name) > 6:
        name = name[:6] + '…'
    labels[node] = f"{node}\n{name}"
nx.draw_networkx_labels(G, pos, labels, font_size=8)

plt.title("产品共现网络图（节点颜色=社区，大小=度数）")
plt.axis('off')

# 调整图例参数，防止重叠
plt.legend(title='社区', loc='upper right', bbox_to_anchor=(1.1, 1),
           markerscale=0.4,           # 缩小图例标记大小
           labelspacing=2.0,           # 增加行间距
           handletextpad=1.0,           # 增加标记与文本的间距
           fontsize=9,                   # 可适当减小字体
           title_fontsize=10)

plt.tight_layout()
plt.savefig(os.path.join(PHOTOS_DIR, 'ml_product_network.png'), dpi=150)
plt.show()

# 2.7 保存结果
# (1) 关联规则表
rules.to_csv(os.path.join(PYEXPORT_DIR, 'ml_association_rules.csv'), index=False)
# (2) 强规则表
strong_rules.to_csv(os.path.join(PYEXPORT_DIR, 'ml_strong_rules.csv'), index=False)
# (3) 产品社区表
community_df.to_csv(os.path.join(PYEXPORT_DIR, 'ml_product_communities.csv'), index=False)

print("\n二.7 结果已保存:")
print(f"  - {os.path.join(PYEXPORT_DIR, 'ml_association_rules.csv')}")
print(f"  - {os.path.join(PYEXPORT_DIR, 'ml_strong_rules.csv')}")
print(f"  - {os.path.join(PYEXPORT_DIR, 'ml_product_communities.csv')}")



# ==================== 业务建议简要输出 ====================
print("\n" + "="*60)
print("【业务建议摘要】")
print("1. 客户分层运营：根据聚类结果，对高价值活跃客户推送新品，对沉睡客户发送唤醒优惠券。")
print("2. 产品捆绑销售：基于强规则，例如 {} → {}，推出组合折扣。".format(
    list(strong_rules.iloc[0]['ante_ids_names'])[:2] if len(strong_rules)>0 else '手套',
    list(strong_rules.iloc[0]['conseq_ids_names'])[:2] if len(strong_rules)>0 else '球'
))
print("3. 货架优化：将同一社区的摆放相近，提升交叉购买。")
print("4. 个性化推荐：根据客户历史购买，推荐同社区其他产品。")
print("="*60)

print("\n脚本执行完毕。")