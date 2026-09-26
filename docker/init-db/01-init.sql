-- 创建数据库扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==================== 用户表 ====================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);

-- ==================== 会话表 ====================
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) DEFAULT '新对话',
    session_type VARCHAR(50) DEFAULT 'chat', -- chat, deepsearch
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX idx_sessions_created_at ON chat_sessions(created_at DESC);

-- ==================== 消息表 ====================
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL, -- user, assistant, system
    content TEXT NOT NULL,
    thinking TEXT, -- 思考过程
    references_data JSONB, -- 引用的文档
    image_results JSONB, -- 图片搜索结果
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_messages_created_at ON chat_messages(created_at);

-- ==================== 知识库表 ====================
CREATE TABLE IF NOT EXISTS knowledge_bases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    document_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_kb_user_id ON knowledge_bases(user_id);

-- ==================== 文档表 ====================
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    knowledge_base_id UUID REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50),
    file_size BIGINT,
    file_path VARCHAR(500),
    status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    chunk_count INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_docs_kb_id ON documents(knowledge_base_id);
CREATE INDEX idx_docs_user_id ON documents(user_id);
CREATE INDEX idx_docs_status ON documents(status);

-- ==================== 长期记忆表 ====================
CREATE TABLE IF NOT EXISTS long_term_memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES chat_sessions(id) ON DELETE SET NULL,
    summary TEXT NOT NULL, -- 记忆摘要
    key_insights JSONB, -- 关键洞察
    milvus_ids TEXT[], -- Milvus 中的向量 ID
    token_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_memory_user_id ON long_term_memories(user_id);
CREATE INDEX idx_memory_session_id ON long_term_memories(session_id);

-- ==================== Text2SQL 数据表示例 ====================

-- 餐饮行业: 餐厅表
CREATE TABLE IF NOT EXISTS restaurants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50), -- 中餐、西餐、日料等
    city VARCHAR(50),
    district VARCHAR(50),
    address VARCHAR(255),
    rating DECIMAL(2,1),
    avg_price INTEGER, -- 人均消费
    total_reviews INTEGER DEFAULT 0,
    monthly_sales INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 餐饮行业: 订单表
CREATE TABLE IF NOT EXISTS restaurant_orders (
    id SERIAL PRIMARY KEY,
    restaurant_id INTEGER REFERENCES restaurants(id),
    order_date DATE NOT NULL,
    total_amount DECIMAL(10,2),
    customer_count INTEGER,
    order_type VARCHAR(20), -- dine_in, takeout, delivery
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 金融行业: 股票表
CREATE TABLE IF NOT EXISTS stocks (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) NOT NULL,
    name VARCHAR(50) NOT NULL,
    industry VARCHAR(50),
    market VARCHAR(20), -- 上海、深圳、北京
    list_date DATE,
    total_shares BIGINT,
    circulating_shares BIGINT
);

-- 金融行业: 股票日行情表
CREATE TABLE IF NOT EXISTS stock_daily (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    open_price DECIMAL(10,2),
    close_price DECIMAL(10,2),
    high_price DECIMAL(10,2),
    low_price DECIMAL(10,2),
    volume BIGINT,
    amount DECIMAL(15,2),
    change_pct DECIMAL(6,2)
);

CREATE INDEX idx_stock_daily_code ON stock_daily(stock_code);
CREATE INDEX idx_stock_daily_date ON stock_daily(trade_date);

-- 法律行业: 案件表
CREATE TABLE IF NOT EXISTS legal_cases (
    id SERIAL PRIMARY KEY,
    case_number VARCHAR(50) NOT NULL,
    case_type VARCHAR(50), -- 民事、刑事、行政
    court VARCHAR(100),
    plaintiff VARCHAR(100),
    defendant VARCHAR(100),
    judge VARCHAR(50),
    filing_date DATE,
    verdict_date DATE,
    status VARCHAR(20), -- 立案、审理中、已判决
    verdict_summary TEXT
);

-- 交通运输行业: 车辆表
CREATE TABLE IF NOT EXISTS vehicles (
    id SERIAL PRIMARY KEY,
    plate_number VARCHAR(20) NOT NULL,
    vehicle_type VARCHAR(50), -- 货车、客车、危险品运输
    brand VARCHAR(50),
    model VARCHAR(50),
    owner_company VARCHAR(100),
    registration_date DATE,
    annual_inspection_date DATE,
    status VARCHAR(20) -- 正常、停运、报废
);

-- 交通运输行业: 运输记录表
CREATE TABLE IF NOT EXISTS transport_records (
    id SERIAL PRIMARY KEY,
    vehicle_id INTEGER REFERENCES vehicles(id),
    driver_name VARCHAR(50),
    origin VARCHAR(100),
    destination VARCHAR(100),
    cargo_type VARCHAR(50),
    cargo_weight DECIMAL(10,2),
    departure_time TIMESTAMP,
    arrival_time TIMESTAMP,
    distance DECIMAL(10,2),
    fuel_cost DECIMAL(10,2)
);

-- ==================== 插入示例数据 ====================

-- 餐厅示例数据
INSERT INTO restaurants (name, category, city, district, avg_price, rating, total_reviews, monthly_sales) VALUES
('海底捞火锅(三里屯店)', '火锅', '北京', '朝阳区', 150, 4.8, 12580, 8520),
('西贝莜面村(国贸店)', '西北菜', '北京', '朝阳区', 98, 4.6, 8960, 6230),
('外婆家(王府井店)', '杭帮菜', '北京', '东城区', 68, 4.5, 15620, 9850),
('鼎泰丰(国贸店)', '台湾菜', '北京', '朝阳区', 128, 4.7, 6580, 4120),
('喜茶(三里屯店)', '饮品', '北京', '朝阳区', 32, 4.4, 28960, 18520),
('星巴克(CBD店)', '咖啡', '北京', '朝阳区', 45, 4.3, 9650, 12580),
('麦当劳(西单店)', '快餐', '北京', '西城区', 35, 4.2, 32580, 25630),
('全聚德(前门店)', '烤鸭', '北京', '东城区', 188, 4.1, 18960, 3520),
('便宜坊(崇文门店)', '烤鸭', '北京', '东城区', 158, 4.3, 12580, 2890),
('南京大牌档(蓝色港湾店)', '江苏菜', '北京', '朝阳区', 78, 4.5, 8520, 5620);

-- 股票示例数据
INSERT INTO stocks (code, name, industry, market, list_date, total_shares, circulating_shares) VALUES
('600519', '贵州茅台', '白酒', '上海', '2001-08-27', 1256198000, 1256198000),
('000858', '五粮液', '白酒', '深圳', '1998-04-27', 3882198000, 3882198000),
('601318', '中国平安', '保险', '上海', '2007-03-01', 18280241410, 16523658410),
('600036', '招商银行', '银行', '上海', '2002-04-09', 25219845000, 20622845000),
('000001', '平安银行', '银行', '深圳', '1991-04-03', 19405918198, 19405918198),
('002594', '比亚迪', '新能源汽车', '深圳', '2011-06-30', 2911145652, 2422648652),
('300750', '宁德时代', '新能源', '深圳', '2018-06-11', 2401081468, 2188456468),
('601012', '隆基绿能', '光伏', '上海', '2012-04-11', 7584936204, 7511256204),
('600900', '长江电力', '电力', '上海', '2003-11-18', 24569522722, 22825212722),
('601398', '工商银行', '银行', '上海', '2006-10-27', 356406260753, 269550260753);

-- 股票日行情示例数据
INSERT INTO stock_daily (stock_code, trade_date, open_price, close_price, high_price, low_price, volume, amount, change_pct) VALUES
('600519', '2024-12-20', 1520.00, 1535.50, 1540.00, 1515.00, 2856000, 4368580000, 1.02),
('600519', '2024-12-19', 1510.00, 1520.00, 1525.00, 1505.00, 2456000, 3723600000, 0.66),
('600519', '2024-12-18', 1498.00, 1510.00, 1518.00, 1495.00, 2985000, 4492350000, 0.80),
('000858', '2024-12-20', 138.50, 140.20, 141.00, 137.80, 15680000, 2192256000, 1.23),
('000858', '2024-12-19', 136.80, 138.50, 139.20, 136.00, 14520000, 2010720000, 1.24),
('601318', '2024-12-20', 42.50, 43.20, 43.50, 42.30, 58960000, 2547072000, 1.65),
('601318', '2024-12-19', 41.80, 42.50, 42.80, 41.50, 52360000, 2225300000, 1.67),
('002594', '2024-12-20', 258.00, 262.50, 265.00, 256.50, 12580000, 3302250000, 1.74),
('002594', '2024-12-19', 254.00, 258.00, 260.00, 252.00, 11860000, 3059880000, 1.57),
('300750', '2024-12-20', 185.00, 188.50, 190.00, 184.00, 8960000, 1689040000, 1.89);

-- 法律案件示例数据
INSERT INTO legal_cases (case_number, case_type, court, plaintiff, defendant, judge, filing_date, verdict_date, status, verdict_summary) VALUES
('(2024)京01民初12345', '民事', '北京市第一中级人民法院', '张三', '某科技公司', '李法官', '2024-03-15', '2024-08-20', '已判决', '判决被告赔偿原告经济损失50万元'),
('(2024)沪02刑初6789', '刑事', '上海市第二中级人民法院', '上海市人民检察院', '王某', '赵法官', '2024-05-10', NULL, '审理中', NULL),
('(2024)粤03行初3456', '行政', '深圳市中级人民法院', '某环保公司', '深圳市生态环境局', '陈法官', '2024-06-20', '2024-11-15', '已判决', '撤销被告作出的行政处罚决定'),
('(2024)浙01民初8901', '民事', '杭州市中级人民法院', '某电商平台', '某网红主播', '周法官', '2024-07-08', NULL, '审理中', NULL),
('(2024)川01民初4567', '民事', '成都市中级人民法院', '李四', '某房地产公司', '吴法官', '2024-04-25', '2024-10-30', '已判决', '判决被告交付房屋并支付违约金20万元');

-- 车辆示例数据
INSERT INTO vehicles (plate_number, vehicle_type, brand, model, owner_company, registration_date, annual_inspection_date, status) VALUES
('京A12345', '货车', '解放', 'J6P', '北京顺丰物流有限公司', '2020-05-15', '2024-05-15', '正常'),
('沪B67890', '客车', '宇通', 'ZK6127', '上海旅游客运公司', '2019-08-20', '2024-08-20', '正常'),
('粤C11111', '危险品运输', '东风', 'DFL1250', '广州危化品运输公司', '2021-03-10', '2024-03-10', '正常'),
('浙D22222', '货车', '重汽', 'HOWO', '杭州中通物流有限公司', '2022-01-05', '2025-01-05', '正常'),
('苏E33333', '货车', '陕汽', 'X3000', '南京德邦物流有限公司', '2021-11-20', '2024-11-20', '正常');

-- 运输记录示例数据
INSERT INTO transport_records (vehicle_id, driver_name, origin, destination, cargo_type, cargo_weight, departure_time, arrival_time, distance, fuel_cost) VALUES
(1, '王师傅', '北京市', '天津市', '电子产品', 8.5, '2024-12-18 08:00:00', '2024-12-18 11:30:00', 135.5, 450.00),
(1, '王师傅', '天津市', '北京市', '食品', 6.2, '2024-12-18 14:00:00', '2024-12-18 17:30:00', 135.5, 420.00),
(4, '李师傅', '杭州市', '上海市', '服装', 12.0, '2024-12-19 06:00:00', '2024-12-19 10:00:00', 180.0, 580.00),
(5, '张师傅', '南京市', '苏州市', '机械配件', 15.5, '2024-12-19 07:30:00', '2024-12-19 12:00:00', 220.0, 720.00),
(3, '陈师傅', '广州市', '深圳市', '化工原料', 5.0, '2024-12-20 05:00:00', '2024-12-20 08:00:00', 140.0, 680.00);

-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为需要的表添加触发器
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON chat_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_kb_updated_at BEFORE UPDATE ON knowledge_bases FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_docs_updated_at BEFORE UPDATE ON documents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
