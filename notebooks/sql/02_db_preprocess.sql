-- 第二部分：进阶处理与初步指标统计
/*
内容大纲：
    一. 初步业务指标 
    二. 时间趋势分析 
    三. 产品维度分析 
    四. 客户维度分析 
    五. 常见信息视图 
*/

-- 一. 初步业务指标---------------------------------------------
	USE retail_analysis ; #导入数据库，多条SQL语句之间必须加分号
    
	-- 1.1订单结构分析
    #人工检查发现，原数据可能是明细表，没有订单id；需要考虑合成购物篮
    
	-- (1)检查 quantity 字段的取值分布
        #如果全部记录均为1，说明原表格就是明细表
		SELECT 
			quantity, 
			COUNT(*) AS record_count,
			ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM `order`), 2) AS percentage
		FROM `order`
		GROUP BY quantity
		ORDER BY quantity;
        #经检验，确实是订单明细

	-- (2)创建包含合成订单ID的视图
    /*算法：
    每个用户在同一天买的所有商品，都会并入一个购物车;
    我们假定一个用户一天只买一次，所有需求都在这次购买中打包支付；
    这会夸大真实的购物车大小，但原始数据中下单时间只精确到日，这里没有更好的办法；
    误差是能接受的，因为体育用品是耐用品，集中购买符合常识。
    */
	CREATE OR REPLACE VIEW v_order_with_basket AS
	SELECT 
		*,
		CONCAT(customer_id, '_', order_date) AS basket_id  #合成订单ID
	FROM `order`;

	-- (3) 统计合成订单的商品数量（购物车大小）分布
	SELECT 
		item_count,
		COUNT(*) AS basket_count,
		ROUND(COUNT(*) * 100.0 / (SELECT COUNT(DISTINCT basket_id) FROM v_order_with_basket), 2) AS percentage
	FROM (
		SELECT 
			basket_id,
			COUNT(*) AS item_count
		FROM v_order_with_basket
		GROUP BY basket_id
	) AS basket_stats
	GROUP BY item_count
	ORDER BY item_count;

	-- (4) 查看多件订单的示例
	SELECT 
		basket_id,
		COUNT(*) AS item_count,
		GROUP_CONCAT(product_id ORDER BY product_id) AS products,
		MIN(order_date) AS order_date,
		MIN(customer_id) AS customer_id
	FROM v_order_with_basket
	GROUP BY basket_id
	HAVING item_count > 1
	ORDER BY item_count DESC
	LIMIT 10;
    
-- 1.2 总指标（基于合成购物篮）
	SELECT '总销售额' AS metric, ROUND(SUM(sales_amount), 2) AS value FROM `order`
	UNION ALL
	SELECT '总订单数', COUNT(DISTINCT basket_id) FROM v_order_with_basket
	UNION ALL
	SELECT '总客户数', COUNT(DISTINCT customer_id) FROM `order`
	UNION ALL
	SELECT '总产品数', (SELECT COUNT(*) FROM product);
		
-- 1.3 平均指标
	WITH basket_stats AS (
		SELECT 
			basket_id,
			SUM(sales_amount) AS basket_total,
			COUNT(*) AS item_count
		FROM v_order_with_basket
		GROUP BY basket_id
	)
	SELECT '平均客单价', ROUND(AVG(basket_total), 2) FROM basket_stats
	UNION ALL
	SELECT '平均每单产品数', ROUND(AVG(item_count), 2) FROM basket_stats;

-- 1.4 复购率指标（基于购物篮）
	-- (1) 整体复购率（基于购物篮的购买次数≥2的客户占比）
	SELECT 
		'整体复购率' AS metric,
		CONCAT(
			ROUND(
				(
					SELECT COUNT(DISTINCT customer_id)
					FROM (
						SELECT customer_id
						FROM v_order_with_basket
						GROUP BY customer_id
						HAVING COUNT(DISTINCT basket_id) >= 2
					) AS repeat_customers
				) 
				/ 
				(SELECT COUNT(DISTINCT customer_id) FROM v_order_with_basket)
				* 100, 
			2), 
		'%') AS value;

	-- (2) 跨年复购率
	WITH customer_year AS (
		SELECT DISTINCT 
			customer_id, 
			YEAR(order_date) AS yr
		FROM v_order_with_basket
	),
	customer_first_year AS (
		SELECT 
			customer_id,
			MIN(yr) AS first_yr
		FROM customer_year
		GROUP BY customer_id
	)
	SELECT 
		cy.yr AS 年份,
		COUNT(DISTINCT cy.customer_id) AS 当年客户数,
		COUNT(DISTINCT CASE WHEN cf.first_yr < cy.yr THEN cy.customer_id END) AS 老客户数,
		CONCAT(
			ROUND(
				COUNT(DISTINCT CASE WHEN cf.first_yr < cy.yr THEN cy.customer_id END) 
				/ COUNT(DISTINCT cy.customer_id) * 100, 
			2), 
		'%') AS 年复购率
	FROM customer_year cy
	LEFT JOIN customer_first_year cf ON cy.customer_id = cf.customer_id
	GROUP BY cy.yr
	ORDER BY cy.yr;

	-- (3) 年内复购率
	WITH customer_year_stats AS (
		SELECT 
			customer_id,
			YEAR(order_date) AS yr,
			COUNT(DISTINCT basket_id) AS purchase_count
		FROM v_order_with_basket
		GROUP BY customer_id, YEAR(order_date)
	)
	SELECT 
		yr AS 年份,
		COUNT(DISTINCT customer_id) AS 当年客户数,
		COUNT(DISTINCT CASE WHEN purchase_count >= 2 THEN customer_id END) AS 同年复购客户数,
		CONCAT(ROUND(COUNT(DISTINCT CASE WHEN purchase_count >= 2 THEN customer_id END) / COUNT(DISTINCT customer_id) * 100, 2), '%') AS 同年复购率
	FROM customer_year_stats
	GROUP BY yr
	ORDER BY yr;
    
-- 二. 时间趋势分析（按年、季度、月度聚合，计算同比环比）------------------
	-- 2.1 按年度聚合（基于购物篮）
	SELECT 
		o.`year`,
		SUM(o.sales_amount) AS total_sales,
		COUNT(DISTINCT ob.basket_id) AS total_orders,
		LAG(SUM(o.sales_amount), 1) OVER (ORDER BY o.`year`) AS prev_year_sales,
		CASE 
			WHEN LAG(SUM(o.sales_amount), 1) OVER (ORDER BY o.`year`) IS NOT NULL 
			THEN CONCAT(ROUND((SUM(o.sales_amount) - LAG(SUM(o.sales_amount), 1) OVER (ORDER BY o.`year`)) / LAG(SUM(o.sales_amount), 1) OVER (ORDER BY o.`year`) * 100, 2), '%')
			ELSE NULL
		END AS yoy_growth
	FROM `order` o
	JOIN v_order_with_basket ob ON o.id = ob.id  -- 通过原id关联以获取basket_id
	GROUP BY o.`year`
	ORDER BY o.`year`;

	-- 2.2 按季度聚合（基于购物篮）
	WITH quarterly_sales AS (
		SELECT 
			d.year_quarter,
			d.year,
			d.quarter,
			SUM(o.sales_amount) AS total_sales,
			COUNT(DISTINCT ob.basket_id) AS total_orders
		FROM `date` d
		LEFT JOIN `order` o ON o.order_date = d.date
		LEFT JOIN v_order_with_basket ob ON o.id = ob.id
		WHERE d.date BETWEEN '2013-01-01' AND '2016-12-31'
		GROUP BY d.year_quarter, d.year, d.quarter
	)
	SELECT 
		year_quarter,
		total_sales,
		total_orders,
		CASE 
			WHEN LAG(total_sales, 1) OVER (ORDER BY year_quarter) IS NULL THEN NULL
			WHEN LAG(total_sales, 1) OVER (ORDER BY year_quarter) = 0 THEN NULL
			ELSE CONCAT(ROUND((total_sales - LAG(total_sales, 1) OVER (ORDER BY year_quarter)) / LAG(total_sales, 1) OVER (ORDER BY year_quarter) * 100, 2), '%')
		END AS qoq_growth,
		CASE 
			WHEN LAG(total_sales, 4) OVER (ORDER BY year_quarter) IS NULL THEN NULL
			WHEN LAG(total_sales, 4) OVER (ORDER BY year_quarter) = 0 THEN NULL
			ELSE CONCAT(ROUND((total_sales - LAG(total_sales, 4) OVER (ORDER BY year_quarter)) / LAG(total_sales, 4) OVER (ORDER BY year_quarter) * 100, 2), '%')
		END AS yoy_growth
	FROM quarterly_sales
	ORDER BY year_quarter;

	-- 2.3 按月度聚合（基于购物篮）
	WITH monthly_sales AS (
		SELECT 
			d.year_month,
			d.year,
			d.month,
			SUM(o.sales_amount) AS total_sales,
			COUNT(DISTINCT ob.basket_id) AS total_orders
		FROM `date` d
		LEFT JOIN `order` o ON o.order_date = d.date
		LEFT JOIN v_order_with_basket ob ON o.id = ob.id
		WHERE d.date BETWEEN '2013-01-01' AND '2016-12-31'
		GROUP BY d.year_month, d.year, d.month
	)
	SELECT 
		`year_month`,
		total_sales,
		total_orders,
		CASE 
			WHEN LAG(total_sales, 1) OVER (ORDER BY `year_month`) IS NULL THEN NULL
			WHEN LAG(total_sales, 1) OVER (ORDER BY `year_month`) = 0 THEN NULL
			ELSE CONCAT(ROUND((total_sales - LAG(total_sales, 1) OVER (ORDER BY `year_month`)) / LAG(total_sales, 1) OVER (ORDER BY `year_month`) * 100, 2), '%')
		END AS mom_growth,
		CASE 
			WHEN LAG(total_sales, 12) OVER (ORDER BY `year_month`) IS NULL THEN NULL
			WHEN LAG(total_sales, 12) OVER (ORDER BY `year_month`) = 0 THEN NULL
			ELSE CONCAT(ROUND((total_sales - LAG(total_sales, 12) OVER (ORDER BY `year_month`)) / LAG(total_sales, 12) OVER (ORDER BY `year_month`) * 100, 2), '%')
		END AS yoy_growth
	FROM monthly_sales
	ORDER BY `year_month`;

-- 三. 产品维度分析
	-- 3.1 按产品类别聚合（基于购物篮）
	SELECT 
		p.product_category,
		COUNT(DISTINCT ob.basket_id) AS order_count,
		ROUND(SUM(o.sales_amount), 2) AS total_sales,
		ROUND(SUM(o.profit), 2) AS total_profit,
		ROUND(SUM(o.profit) / SUM(o.sales_amount) * 100, 2) AS profit_margin_pct
	FROM `order` o
	JOIN product p ON o.product_id = p.product_id
	JOIN v_order_with_basket ob ON o.id = ob.id
	GROUP BY p.product_category
	ORDER BY total_sales DESC;

-- 3.2 十大热销产品（按销售额）
	SELECT 
		p.product_id,
		p.product_name,
		p.product_category,
		SUM(o.quantity) AS total_quantity,
		ROUND(SUM(o.sales_amount), 2) AS total_sales
	FROM `order` o
	JOIN product p ON o.product_id = p.product_id
	GROUP BY p.product_id, p.product_name, p.product_category
	ORDER BY total_sales DESC
	LIMIT 10;
    
-- 3.3 十大热销产品（按销量）
	SELECT 
		p.product_id,
		p.product_name,
		p.product_category,
		SUM(o.quantity) AS total_quantity,
		ROUND(SUM(o.sales_amount), 2) AS total_sales
	FROM `order` o
	JOIN product p ON o.product_id = p.product_id
	GROUP BY p.product_id, p.product_name, p.product_category
	ORDER BY total_quantity DESC
	LIMIT 10;

-- 四. 客户维度分析
	-- 4.1 客户购买频次分布
	SELECT 
		purchase_times,
		COUNT(customer_id) AS customer_count
	FROM (
		SELECT 
			customer_id,
			COUNT(DISTINCT basket_id) AS purchase_times
		FROM v_order_with_basket
		GROUP BY customer_id
	) AS cust_freq
	GROUP BY purchase_times
	ORDER BY purchase_times;

	-- 4.2 客户地区分布（按销售大区）
	SELECT 
		o.sales_region_name,
		COUNT(DISTINCT o.customer_id) AS customer_count,
		COUNT(DISTINCT o.id) AS order_count,
		ROUND(SUM(o.sales_amount), 2) AS total_sales
	FROM `order` o
	GROUP BY o.sales_region_name
	ORDER BY total_sales DESC;

	-- 4.3 客户生命周期基础特征
	-- 计算每个客户的首次购买日期、最近购买日期、平均订单金额
	SELECT 
		customer_id,
		MIN(order_date) AS first_purchase_date,
		MAX(order_date) AS last_purchase_date,
		ROUND(AVG(basket_total), 2) AS avg_order_value
	FROM (
		SELECT 
			customer_id,
			order_date,
			basket_id,
			SUM(sales_amount) AS basket_total
		FROM v_order_with_basket
		GROUP BY customer_id, order_date, basket_id
	) AS customer_baskets
	GROUP BY customer_id
	ORDER BY customer_id
	LIMIT 20;

	-- 4.4. RFM 计算（用于 Python 客户分层）
	SET @base_date = (SELECT DATE_ADD(MAX(order_date), INTERVAL 1 DAY) FROM `order`);

	WITH customer_rfm_raw AS (
		SELECT 
			customer_id,
			DATEDIFF(@base_date, MAX(order_date)) AS recency_days,
			COUNT(DISTINCT basket_id) AS frequency,
			ROUND(SUM(sales_amount), 2) AS monetary
		FROM v_order_with_basket
		GROUP BY customer_id
	)
	SELECT * FROM customer_rfm_raw
	ORDER BY customer_id
	LIMIT 20;

-- 五. 创建视图：订单明细、客户 RFM、产品信息
	-- 5.1 订单明细视图
	CREATE OR REPLACE VIEW v_order_detail AS
	SELECT 
		o.id AS order_id,
		o.customer_id,
		o.product_id,
		o.order_date,
		o.sales_amount,
		p.product_category,
		p.product_name
	FROM `order` o
	LEFT JOIN product p ON o.product_id = p.product_id;
    
    -- 5.2 购物篮明细视图（基于 basket_id，）
	CREATE OR REPLACE VIEW v_basket_detail AS
	SELECT 
		ob.basket_id,
		ob.customer_id,
		ob.order_date,
		ob.product_id,
		ob.sales_amount,
		p.product_category,
		p.product_name
	FROM v_order_with_basket ob
	LEFT JOIN product p ON ob.product_id = p.product_id;
    
	-- 5.3 客户特征视图
	CREATE OR REPLACE VIEW v_customer_features AS 
	WITH basket_totals AS (
		SELECT 
			basket_id,
			customer_id,
			order_date,
			SUM(sales_amount) AS basket_total
		FROM v_order_with_basket
		GROUP BY basket_id, customer_id, order_date
	),
	customer_base AS (
		SELECT 
			customer_id,
			MIN(order_date) AS first_purchase_date,
			MAX(order_date) AS last_purchase_date,
			COUNT(DISTINCT basket_id) AS frequency,
			ROUND(SUM(basket_total), 2) AS monetary,
			ROUND(AVG(basket_total), 2) AS avg_order_value
		FROM basket_totals
		GROUP BY customer_id
	)
	SELECT 
		customer_id,
		DATEDIFF(
			(SELECT DATE_ADD(MAX(order_date), INTERVAL 1 DAY) FROM `order`), 
			last_purchase_date
		) AS recency_days,
		frequency,
		monetary,
		first_purchase_date,
		last_purchase_date,
		avg_order_value,
		CASE WHEN frequency >= 2 THEN 1 ELSE 0 END AS is_repeat_customer
	FROM customer_base;

	-- 5.4 产品信息视图
	CREATE OR REPLACE VIEW v_product_info AS
	SELECT 
		product_id,
		product_category,
		product_name
	FROM product;

	-- 5.5 验证视图创建成功
	SELECT 'v_order_detail' AS view_name, COUNT(*) AS `rows` FROM v_order_detail
	UNION ALL
	SELECT 'v_basket_detail', COUNT(*) FROM v_basket_detail
	UNION ALL
	SELECT 'v_customer_features', COUNT(*) FROM v_customer_features
	UNION ALL
	SELECT 'v_product_info', COUNT(*) FROM v_product_info;


	-- 5.5 导出为 CSV（供 Python 离线使用）
	#两个前提：1.有文件权限；2.如果目录不存在需先手动创建
    
    SELECT * FROM v_order_detail
	INTO OUTFILE 'D:/WORK/database/sqlexport/v_order_detail.csv'
	FIELDS TERMINATED BY ',' 
	ENCLOSED BY '"'
	LINES TERMINATED BY '\n';
    
	SELECT * FROM v_basket_detail
	INTO OUTFILE 'D:/WORK/database/sqlexport/v_basket_detail.csv'
	FIELDS TERMINATED BY ',' 
	ENCLOSED BY '"'
	LINES TERMINATED BY '\n';

	SELECT * FROM v_customer_features
	INTO OUTFILE 'D:/WORK/database/sqlexport/v_customer_features.csv'
	FIELDS TERMINATED BY ',' 
	ENCLOSED BY '"'
	LINES TERMINATED BY '\n';

	SELECT * FROM v_product_info
	INTO OUTFILE 'D:/WORK/database/sqlexport/v_product_info.csv'
	FIELDS TERMINATED BY ',' 
	ENCLOSED BY '"'
	LINES TERMINATED BY '\n';