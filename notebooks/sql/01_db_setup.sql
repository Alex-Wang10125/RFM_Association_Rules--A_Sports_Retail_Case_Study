-- 开始：创建数据库
-- 注意：需要将数据放入安全目录，否则部分代码可能报错

/*目录：
	第一部分：建立空表
	第二部分：导入csv数据到表格 
    第三部分：数据结构完整性 
*/


CREATE DATABASE IF NOT EXISTS retail_analysis
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
USE retail_analysis;

-- 第一部分：建立空表
	-- 1.1 产品表 product
	CREATE TABLE product (
		product_id INT PRIMARY KEY,
		product_category VARCHAR(50),
		product_model VARCHAR(100),
		product_name VARCHAR(100)
	) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

	-- 1.2 客户表 customer
	CREATE TABLE customer (
		customer_id VARCHAR(20) PRIMARY KEY   
	) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

	-- 1.3 日期表 date
	CREATE TABLE `date` (
		`date` DATE PRIMARY KEY,
		`year` INT,
		`quarter` VARCHAR(5),
		`month` INT,
		`day` INT,
		`year_quarter` VARCHAR(10),
		`year_month` VARCHAR(10),
		`weekday` INT
	) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

	-- 1.4 订单表 order （order 是 MySQL 关键字，需用反引号转义）
	CREATE TABLE `order` (
		order_date DATE,
		year INT,
		quantity INT,
		product_id INT,
		customer_id VARCHAR(20),
		transaction_type INT,
		sales_region_id INT,
		sales_region_name VARCHAR(50),
		country VARCHAR(50),
		area VARCHAR(50),
		product_type VARCHAR(50),
		product_model_name VARCHAR(100),
		product_name VARCHAR(100),
		product_cost DECIMAL(10,2),
		profit DECIMAL(10,2),
		unit_price DECIMAL(10,2),
		sales_amount DECIMAL(10,2)
	) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 第二部分：导入csv数据到表格
	USE retail_analysis;
	LOAD DATA INFILE 'D:/WORK/database/raw/customer.csv'
	INTO TABLE customer
	CHARACTER SET utf8mb4
	FIELDS TERMINATED BY ','          #单列文件实际无逗号，但标准CSV仍用逗号作为字段分隔符
	LINES TERMINATED BY '\n'          #行结束符
	IGNORE 1 ROWS                     #跳过标题行
	(customer_id);                    #指定要导入的列（与表字段对应）
	SELECT * FROM customer LIMIT 10; #验证前10行，看看是否成功导入

	LOAD DATA INFILE 'D:/WORK/database/raw/product.csv'
	INTO TABLE product
	CHARACTER SET utf8mb4
	FIELDS TERMINATED BY ','
	LINES TERMINATED BY '\n'
	IGNORE 1 ROWS
	(product_category, product_id, product_model, product_name);
	SELECT COUNT(*) AS product_rows FROM product;
	SELECT * FROM product LIMIT 10; #验证导入结果

	LOAD DATA INFILE 'D:/WORK/database/raw/date.csv'
	INTO TABLE `date`
	CHARACTER SET utf8mb4
	FIELDS TERMINATED BY ','
	LINES TERMINATED BY '\n'
	IGNORE 1 ROWS
	(`date`, `year`, `quarter`, `month`, `day`, `year_quarter`, `year_month`, `weekday`);
	SELECT COUNT(*) AS date_rows FROM `date`;
	SELECT * FROM `date` LIMIT 10; #验证导入结果

	LOAD DATA INFILE 'D:/WORK/database/raw/order.csv'
	INTO TABLE `order`
	CHARACTER SET utf8mb4
	FIELDS TERMINATED BY ','
	LINES TERMINATED BY '\n'
	IGNORE 1 ROWS
	(order_date, `year`, quantity, product_id, customer_id, transaction_type,
	 sales_region_id, sales_region_name, country, area, product_type,
	 product_model_name, product_name, product_cost, profit, unit_price, sales_amount);
	SELECT COUNT(*) AS order_rows FROM `order`;
	SELECT * FROM `order` LIMIT 10; #验证导入结果

-- 第三部分：数据结构完整性
	-- 3.1 检查数据完整性
	SET SQL_SAFE_UPDATES = 0; #临时禁用安全更新模式
	UPDATE customer 
	SET customer_id = REPLACE(REPLACE(customer_id, '\r', ''), '"', '')
	WHERE customer_id LIKE '%\r%' OR customer_id LIKE '%"%';

	SELECT customer_id, LENGTH(customer_id)
	FROM customer
	WHERE LENGTH(customer_id) > 7; #检查是否还有长度 >7 的值（正常 ID 应为 7 字符）

	#检查 order 表中的 product_id 是否都在 product 表中存在
	SELECT COUNT(*) AS missing_product_ids
	FROM `order` o
	LEFT JOIN product p ON o.product_id = p.product_id
	WHERE p.product_id IS NULL; -- 应该返回空值，如果非空说明对不上

	#检查 order 表中的 customer_id 是否都在 customer 表中存在
	SELECT COUNT(*) AS missing_customer_ids
	FROM `order` o
	LEFT JOIN customer c ON o.customer_id = c.customer_id
	WHERE c.customer_id IS NULL;

	# 检查 order 表中的 order_date 是否都在 date 表中存在
	SELECT COUNT(*) AS missing_dates
	FROM `order` o
	LEFT JOIN `date` d ON o.order_date = d.date
	WHERE d.date IS NULL;

	-- 3.2 为字段创建索引
	#为 order 表的常用关联字段创建索引
	CREATE INDEX idx_order_product_id ON `order`(product_id);
	CREATE INDEX idx_order_customer_id ON `order`(customer_id);
	CREATE INDEX idx_order_order_date ON `order`(order_date);
	CREATE INDEX idx_order_year ON `order`(`year`);

	-- 3.3 添加主键和外键约束
	#为order添加自增主键（放在第一列）
	ALTER TABLE `order` 
	ADD COLUMN id INT AUTO_INCREMENT PRIMARY KEY FIRST;

	#添加外键约束
	ALTER TABLE `order` ADD CONSTRAINT fk_order_product
	FOREIGN KEY (product_id) REFERENCES product(product_id);
	ALTER TABLE `order` ADD CONSTRAINT fk_order_customer
	FOREIGN KEY (customer_id) REFERENCES customer(customer_id);
	ALTER TABLE `order` ADD CONSTRAINT fk_order_date
	FOREIGN KEY (order_date) REFERENCES `date`(date);

	-- 3.4检查结果
	#查看已创建的索引
	SHOW INDEX FROM `order`;

	#查看表结构
	DESCRIBE `order`;-- 查看 id 列的最大值和行数
	SELECT MAX(id), COUNT(*) FROM `order`;-- 两者应相等

	#查看外键约束
	SELECT 
		CONSTRAINT_NAME, 
		TABLE_NAME, 
		COLUMN_NAME, 
		REFERENCED_TABLE_NAME, 
		REFERENCED_COLUMN_NAME
	FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
	WHERE TABLE_SCHEMA = 'retail_analysis' 
	  AND REFERENCED_TABLE_NAME IS NOT NULL;
	  
	#最后人工确认四张表的情况
	SELECT * FROM customer LIMIT 10;
	SELECT * FROM product LIMIT 10;
	SELECT * FROM `date` LIMIT 10; 
	SELECT * FROM `order` LIMIT 10;