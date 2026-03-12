"""
目录：
一.导入库与加载数据
二.时间趋势分析
三.产品维度分析
四.客户维度分析
五.输出汇总统计
"""

#---------------一.导入库与加载数据----------------------------------------------------------
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# 1.1 设置中文字体（避免图表乱码，此处通过文件定义）
font_path = 'C:/Windows/Fonts/msyh.ttc'  
prop = fm.FontProperties(fname=font_path)
plt.rcParams['font.family'] = prop.get_name()

# 1.2 定义文件路径
    # (1)输入
basket_path = 'D:/WORK/database/sqlexport/v_basket_detail.csv'      # 购物篮明细
customer_features_path = 'D:/WORK/database/sqlexport/v_customer_features.csv'  # 客户特征
product_info_path = 'D:/WORK/database/sqlexport/v_product_info.csv'            # 产品信息
    # (2)输出
PHOTOS_DIR = r'D:\WORK\report\photos'          # 图片存放路径
PYEXPORT_DIR = r'D:\WORK\database\pyexport'    # 表格存放路径

#1.3 加载与查看数据
    # (1)加载数据
df_basket = pd.read_csv(basket_path)
df_cust = pd.read_csv(customer_features_path)
df_prod = pd.read_csv(product_info_path)
print("="*50)
print("数据加载完成")

    # (2)查看数据规模
print("df_basket 形状:", df_basket.shape)
print("df_cust 形状:", df_cust.shape)
print("df_prod 形状:", df_prod.shape)

    # (3)查看各表前几行
print("\ndf_basket 前2行:\n", df_basket.head(2))
print("\ndf_cust 前2行:\n", df_cust.head(2))
print("\ndf_prod 前2行:\n", df_prod.head(2))

    # (4)转换日期列
df_basket['order_date'] = pd.to_datetime(df_basket['order_date'])
df_cust['first_purchase_date'] = pd.to_datetime(df_cust['first_purchase_date'])
df_cust['last_purchase_date'] = pd.to_datetime(df_cust['last_purchase_date'])
print("\n日期列转换完成")
print("df_basket 日期范围:", df_basket['order_date'].min(), "至", df_basket['order_date'].max())
print("df_cust 首次购买日期范围:", df_cust['first_purchase_date'].min(), "至", df_cust['first_purchase_date'].max())



#-----------------二. 时间趋势分析------------------------------------------------
#2.1 按日聚合
daily_sales = df_basket.groupby('order_date').agg(
    total_sales=('sales_amount', 'sum'),
    total_orders=('basket_id', 'nunique')
).reset_index()

print("\n按日聚合完成，日数据量:", len(daily_sales))
print("日销售额描述统计:\n", daily_sales['total_sales'].describe())

#2.2 按月聚合
df_basket['year_month'] = df_basket['order_date'].dt.to_period('M').astype(str)  # 转为字符串便于绘图
monthly_sales = df_basket.groupby('year_month').agg(
    total_sales=('sales_amount', 'sum'),
    total_orders=('basket_id', 'nunique')
).reset_index()
monthly_sales['year_month_dt'] = pd.to_datetime(monthly_sales['year_month'] + '-01')  # 转为日期用于排序

print("\n按月聚合完成，月数据量:", len(monthly_sales))
print("月销售额描述统计:\n", monthly_sales['total_sales'].describe())

# 2.3 按季度聚合
df_basket['year_quarter'] = df_basket['order_date'].dt.to_period('Q').astype(str)
quarterly_sales = df_basket.groupby('year_quarter').agg(
    total_sales=('sales_amount', 'sum'),
    total_orders=('basket_id', 'nunique')
).reset_index()
    # 提取季度起始日期
quarterly_sales['quarter_start'] = quarterly_sales['year_quarter'].apply(lambda x: pd.Period(x).start_time)

print("\n按季度聚合完成，季度数据量:", len(quarterly_sales))
print("季度销售额描述统计:\n", quarterly_sales['total_sales'].describe())


# 2.4 绘制销售额时间序列图
fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=False)

# (1) 日销售额
axes[0].plot(daily_sales['order_date'], daily_sales['total_sales'], color='steelblue', linewidth=0.8)
axes[0].set_title('日销售额趋势')
axes[0].set_ylabel('销售额')
axes[0].axvline(pd.Timestamp('2015-07-01'), color='red', linestyle='--', linewidth=1, label='2015Q3爆发点')
axes[0].axvline(pd.Timestamp('2016-07-31'), color='gray', linestyle=':', linewidth=1, label='数据截止')
axes[0].legend()
axes[0].tick_params(axis='x', rotation=45)

# (2) 月销售额
axes[1].plot(monthly_sales['year_month_dt'], monthly_sales['total_sales'], marker='o', markersize=3, color='darkorange')
axes[1].set_title('月销售额趋势')
axes[1].set_ylabel('销售额')
axes[1].axvline(pd.Timestamp('2015-07-01'), color='red', linestyle='--', label='2015Q3爆发点')
axes[1].axvline(pd.Timestamp('2016-07-31'), color='gray', linestyle=':', label='数据截止')
axes[1].legend()
axes[1].tick_params(axis='x', rotation=45)

# (3) 季度销售额
axes[2].plot(quarterly_sales['quarter_start'], quarterly_sales['total_sales'], marker='s', markersize=5, color='green')
axes[2].set_title('季度销售额趋势')
axes[2].set_ylabel('销售额')
axes[2].axvline(pd.Timestamp('2015-07-01'), color='red', linestyle='--', label='2015Q3爆发点')
axes[2].axvline(pd.Timestamp('2016-07-31'), color='gray', linestyle=':', label='数据截止')
axes[2].legend()
axes[2].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig(os.path.join(PHOTOS_DIR, 'sales_trend.png'), dpi=150)
plt.show()
print("\n时间趋势图已保存为 sales_trend.png")



#---------------------- 3. 产品维度分析 ---------------------------------------------------------------------------
df_basket_with_cat = df_basket.merge(df_prod, on='product_id', how='left')
print("df_basket_with_cat 列名:", df_basket_with_cat.columns.tolist())

# 3.1 按产品类别聚合（df_basket 已包含产品类别信息）
print("df_basket 列名:", df_basket.columns.tolist())  # 调试：确认包含 product_category

if 'product_category' in df_basket.columns:
    category_stats = df_basket.groupby('product_category').agg(
        total_sales=('sales_amount', 'sum'),
    ).reset_index()
        # 若需计算利润占比，但无利润字段时，可跳过
    if 'profit' in df_basket.columns:
        profit_stats = df_basket.groupby('product_category')['profit'].sum().reset_index(name='total_profit')
        category_stats = category_stats.merge(profit_stats, on='product_category', how='left')
        category_stats['profit_margin_pct'] = (category_stats['total_profit'] / category_stats['total_sales'] * 100).round(2)
else:
        # 如果没有 product_category，则从合并后的数据中选取合适的列
    category_stats = df_basket_with_cat.groupby('product_category_x').agg(
        total_sales=('sales_amount', 'sum'),
    ).reset_index()
    category_stats.rename(columns={'product_category_x': 'product_category'}, inplace=True)

print("\n产品类别销售额统计:\n", category_stats)

    # 绘制类别销售额饼图
plt.figure(figsize=(8, 8))
plt.pie(category_stats['total_sales'], labels=category_stats['product_category'], autopct='%1.1f%%', startangle=90)
plt.title('各产品类别销售额占比')
plt.tight_layout()
plt.savefig(os.path.join(PHOTOS_DIR, 'category_pie.png'), dpi=150)
plt.show()

# 3.2 热销产品排名
product_sales = df_basket.groupby('product_id').agg(
    total_sales=('sales_amount', 'sum'),
    total_quantity=('sales_amount', 'count')
).reset_index()
product_sales = product_sales.merge(df_prod, on='product_id', how='left')
top10_sales = product_sales.nlargest(10, 'total_sales')


    # (1).检查是否合并 product_name
if 'product_name' not in product_sales.columns:
    product_sales = product_sales.merge(df_prod[['product_id', 'product_name']], on='product_id', how='left')
    # 对于可能缺失名称的产品，填充占位
    product_sales['product_name'] = product_sales['product_name'].fillna('未知产品')

    # (2).销售额 TOP10
top10_sales = product_sales.nlargest(10, 'total_sales').copy()

    # (3).销量 TOP10
top10_qty = product_sales.nlargest(10, 'total_quantity').copy()

    # (4).创建唯一标签：产品ID - 产品名称
top10_sales['label'] = top10_sales['product_id'].astype(str) + ' - ' + top10_sales['product_name']
top10_qty['label'] = top10_qty['product_id'].astype(str) + ' - ' + top10_qty['product_name']

    # (5).绘制条形图
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # (6).销售额 TOP10
axes[0].barh(top10_sales['label'], top10_sales['total_sales'], color='steelblue')
axes[0].set_xlabel('销售额')
axes[0].set_title('销售额TOP10产品')
axes[0].invert_yaxis()

    # (7).销量 TOP10
axes[1].barh(top10_qty['label'], top10_qty['total_quantity'], color='darkorange')
axes[1].set_xlabel('销量')
axes[1].set_title('销量TOP10产品')
axes[1].invert_yaxis()

plt.tight_layout()
plt.savefig(os.path.join(PHOTOS_DIR, 'top10_products.png'), dpi=150)
plt.show()

#3.4 产品价格分布（单价）
if 'sales_amount' in df_basket.columns:
    # 按产品聚合，计算平均单价
    product_price = df_basket.groupby('product_id')['sales_amount'].mean().reset_index()
    product_price.columns = ['product_id', 'avg_unit_price']  # 重命名列，便于理解

    # 绘制直方图
    plt.figure(figsize=(10, 6))
    plt.hist(product_price['avg_unit_price'], bins=30, edgecolor='black', alpha=0.7)
    plt.xlabel('平均单价')
    plt.ylabel('产品数量')
    plt.title('产品平均单价分布直方图')
    plt.tight_layout()
    plt.savefig(os.path.join(PHOTOS_DIR, 'price_distribution.png'), dpi=150)
    plt.show()

    print("产品价格统计描述:\n", product_price['avg_unit_price'].describe())
else:
    print("注意：df_basket 中无 sales_amount 字段，跳过价格分布图。")




# ------------------- 4. 客户维度分析 -----------------------------------------------------
# 4.1 客户购买频次分布
freq_dist = df_cust['frequency'].value_counts().sort_index().reset_index()
freq_dist.columns = ['purchase_times', 'customer_count']
print("\n客户购买频次分布（前10）:\n", freq_dist.head(10))

    # 绘制频次分布直方图（只展示1-10次，长尾截断）
plt.figure(figsize=(10, 6))
df_cust['frequency'].hist(bins=range(1, 21), edgecolor='black', alpha=0.7)
plt.xlabel('购买次数')
plt.ylabel('客户数')
plt.title('客户购买频次分布')
plt.xticks(range(1, 21))
plt.tight_layout()
plt.savefig(os.path.join(PHOTOS_DIR, 'customer_freq.png'), dpi=150)
plt.show()

# 4.2 客户地区分布（销售大区）
    # (1) 按销售大区聚合统计
region_stats = df_basket.groupby('sales_region_name').agg(
    customer_count=('customer_id', 'nunique'),
    order_count=('basket_id', 'nunique'),
    total_sales=('sales_amount', 'sum')
).reset_index()

    # (2) 添加平均客单价（总销售额 / 订单数）
region_stats['avg_order_value'] = (region_stats['total_sales'] / region_stats['order_count']).round(2)

    # (3) 添加销售额占比
region_stats['sales_pct'] = (region_stats['total_sales'] / region_stats['total_sales'].sum() * 100).round(2)

    # (4) 按销售额降序排序
region_stats = region_stats.sort_values('total_sales', ascending=False).reset_index(drop=True)

print("\n【各销售大区销售统计】")
print(region_stats[['sales_region_name', 'total_sales', 'order_count', 'customer_count', 'avg_order_value', 'sales_pct']])

    # (5) 绘制销售额条形图（带数值标签）
plt.figure(figsize=(12, 6))
bars = plt.bar(region_stats['sales_region_name'], region_stats['total_sales'], color='steelblue', alpha=0.8)
plt.xlabel('销售大区')
plt.ylabel('销售额')
plt.title('各销售大区销售额分布')

    # 在柱子上添加数值标签（以万元为单位显示，简化数字）
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height + 0.01 * region_stats['total_sales'].max(),
                f'{height/10000:.1f}w', ha='center', va='bottom', fontsize=9)

plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig(os.path.join(PHOTOS_DIR, 'region_sales.png'), dpi=150)
plt.show()

# 4.3 首次购买日期分布
plt.figure(figsize=(12, 6))
df_cust['first_purchase_date'].hist(bins=50, edgecolor='black', alpha=0.7)
plt.xlabel('首次购买日期')
plt.ylabel('客户数')
plt.title('客户首次购买日期分布')
plt.tight_layout()
plt.savefig(os.path.join(PHOTOS_DIR, 'first_purchase_dist.png'), dpi=150)
plt.show()

# 4.4 简单RFM分组：将客户按RFM值分箱打分
    # (1) 使用五分位数对 recency, frequency, monetary 打分（1-5分），然后计算总分
df_cust['R_score'] = pd.qcut(df_cust['recency_days'], 5, labels=[5,4,3,2,1])  # 最近购买越近得分越高
df_cust['F_score'] = pd.qcut(df_cust['frequency'].rank(method='first'), 5, labels=[1,2,3,4,5])  # 频次越高得分越高
df_cust['M_score'] = pd.qcut(df_cust['monetary'].rank(method='first'), 5, labels=[1,2,3,4,5])
df_cust['RFM_score'] = df_cust[['R_score','F_score','M_score']].astype(int).sum(axis=1)

    # (2) 分组统计
rfm_groups = df_cust.groupby('RFM_score').agg(
    customer_count=('customer_id', 'count'),
    avg_recency=('recency_days', 'mean'),
    avg_frequency=('frequency', 'mean'),
    avg_monetary=('monetary', 'mean')
).reset_index().sort_values('RFM_score', ascending=False)
print("\nRFM分组统计（按RFM总分）:\n", rfm_groups)

    # (3) 绘制RFM总分分布
plt.figure(figsize=(10, 6))
df_cust['RFM_score'].hist(bins=15, edgecolor='black', alpha=0.7)
plt.xlabel('RFM总分')
plt.ylabel('客户数')
plt.title('客户RFM总分分布')
plt.tight_layout()
plt.savefig(os.path.join(PHOTOS_DIR, 'rfm_score_dist.png'), dpi=150)
plt.show()

#4.5 客户购物篮大小分析
# 基于 df_basket 统计每个购物篮的商品数量
if 'basket_id' in df_basket.columns:
    # 计算每个购物篮的商品数量
    basket_size = df_basket.groupby('basket_id').size().reset_index(name='item_count')
    
    print("\n5.1 购物篮大小统计")
    print("购物篮总数:", len(basket_size))
    print("购物篮大小描述统计:\n", basket_size['item_count'].describe())
    
    # 按大小分组统计购物篮数量
    size_dist = basket_size['item_count'].value_counts().sort_index().reset_index()
    size_dist.columns = ['item_count', 'basket_count']
    size_dist['percentage'] = (size_dist['basket_count'] / len(basket_size) * 100).round(2)
    print("\n购物篮大小分布:\n", size_dist)
    
    # 绘制直方图（条形图，因为 item_count 为整数）
    plt.figure(figsize=(10, 6))
    # 限制横轴范围（例如只显示 item_count ≤ 10，因为长尾可能很长）
    max_show = min(10, basket_size['item_count'].max())
    data_show = basket_size[basket_size['item_count'] <= max_show]['item_count']
    bins = range(1, max_show+2)  # 确保每个整数一个柱
    plt.hist(data_show, bins=bins, edgecolor='black', alpha=0.7, align='left')
    plt.xlabel('购物篮商品数量')
    plt.ylabel('购物篮数量')
    plt.title(f'购物篮大小分布（仅展示 ≤ {max_show} 件）')
    plt.xticks(range(1, max_show+1))
    plt.tight_layout()
    plt.savefig(os.path.join(PHOTOS_DIR, 'basket_size_hist.png'), dpi=150)
    plt.show()
    
    # 绘制饼图（展示前几大类别，其余合并为“其他”）
    if len(size_dist) > 6:
        # 合并小类别
        top5 = size_dist.head(5).copy()
        others_count = size_dist.iloc[5:]['basket_count'].sum()
        others = pd.DataFrame({'item_count': ['其他'], 'basket_count': [others_count]})
        pie_data = pd.concat([top5, others], ignore_index=True)
    else:
        pie_data = size_dist.copy()
    
    plt.figure(figsize=(8, 8))
    plt.pie(pie_data['basket_count'], labels=pie_data['item_count'].astype(str), autopct='%1.1f%%', startangle=90)
    plt.title('购物篮大小占比')
    plt.tight_layout()
    plt.savefig(os.path.join(PHOTOS_DIR, 'basket_size_pie.png'), dpi=150)
    plt.show()
    
    #4.6 平均每位客户营收
    arpu = df_basket['sales_amount'].sum() / df_basket['customer_id'].nunique()



# --------------------------------5. 输出汇总统计 ------------------------------------------------
# 5.1关键指标表
summary = pd.DataFrame({
    'metric': ['总销售额', '总订单数', '总客户数', '总产品数', '平均客单价', '平均购物车大小', '整体复购率', '平均每位客户营收'],
    'value': [
        df_basket['sales_amount'].sum(),
        df_basket['basket_id'].nunique(),
        df_basket['customer_id'].nunique(),
        df_prod['product_id'].nunique(),
        df_basket.groupby('basket_id')['sales_amount'].sum().mean(),
        df_basket.groupby('basket_id')['product_id'].count().mean(),
        f"{df_cust['is_repeat_customer'].mean()*100:.2f}%",  # 来自客户特征表的复购标志
        f"¥{arpu:,.2f}"
    ]
})
print("\n【关键指标汇总】\n", summary)
summary.to_csv(os.path.join(PYEXPORT_DIR, 'summary_stats.csv'), index=False)
print("汇总统计已保存至 summary_stats.csv")

# 5.2 中间变量表
category_stats.to_csv(os.path.join(PYEXPORT_DIR, 'category_stats.csv'), index=False)
product_sales.to_csv(os.path.join(PYEXPORT_DIR, 'product_sales.csv'), index=False)
rfm_groups.to_csv(os.path.join(PYEXPORT_DIR, 'rfm_groups.csv'), index=False)
print("\n所有图表和CSV文件已生成。请检查当前目录。")


