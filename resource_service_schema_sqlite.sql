-- Enriched SQLite schema for Resource Service (Smart Billiard Club System)
-- Based on BA Specification in resource_service_design.md

-- 1. BẢNG CHI NHÁNH / CLUB
CREATE TABLE IF NOT EXISTS clubs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    address TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. BẢNG PHÂN VÙNG / KHU VỰC CLUB (AREAS)
CREATE TABLE IF NOT EXISTS areas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    club_id INTEGER NOT NULL REFERENCES clubs(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 3. BẢNG BÀN BIDA TÍCH HỢP IOT & CẢNH BÁO BẢO TRÌ
CREATE TABLE IF NOT EXISTS tables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    club_id INTEGER NOT NULL REFERENCES clubs(id) ON DELETE CASCADE,
    area_id INTEGER REFERENCES areas(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    table_type TEXT NOT NULL DEFAULT 'POOL_9BALL' CHECK (table_type IN ('POOL_9BALL', 'CAROM_3CUSHION', 'SNOOKER')),
    table_tier TEXT NOT NULL DEFAULT 'STANDARD' CHECK (table_tier IN ('STANDARD', 'VIP', 'SUPER_VIP')),
    hourly_rate REAL NOT NULL DEFAULT 60000.0 CHECK (hourly_rate >= 0),
    current_status TEXT NOT NULL DEFAULT 'EMPTY' CHECK (current_status IN ('EMPTY', 'RESERVED', 'PREPARING', 'PLAYING', 'PAUSED', 'CLEANING', 'MAINTENANCE')),
    iot_device_id TEXT,                     -- Topic MQTT hoặc IP Rơ-le điều khiển đèn
    camera_rtsp_url TEXT,                   -- Luồng Camera AI
    total_playing_hours REAL NOT NULL DEFAULT 0.0,   -- Tích lũy giờ chơi
    maintenance_threshold_hours REAL NOT NULL DEFAULT 300.0, -- Ngưỡng báo bọc lại nỉ bàn
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 4. BẢNG BẢNG GIÁ ĐỘNG THEO KHUNG GIỜ & NGÀY LỄ (DYNAMIC PRICING MATRIX)
CREATE TABLE IF NOT EXISTS table_pricing_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    club_id INTEGER NOT NULL REFERENCES clubs(id) ON DELETE CASCADE,
    table_tier TEXT NOT NULL CHECK (table_tier IN ('STANDARD', 'VIP', 'SUPER_VIP')),
    day_of_week INTEGER CHECK (day_of_week BETWEEN 1 AND 7), -- 1: Mon, 7: Sun, NULL: All days
    start_time TEXT NOT NULL, -- Format 'HH:MM'
    end_time TEXT NOT NULL,   -- Format 'HH:MM'
    hourly_rate REAL NOT NULL CHECK (hourly_rate >= 0),
    is_holiday TEXT NOT NULL DEFAULT 'false',
    description TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 5. BẢNG SẢN PHẨM, KHO F&B & QUY ĐỔI ĐƠN VỊ TÍNH
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    club_id INTEGER NOT NULL REFERENCES clubs(id) ON DELETE CASCADE,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('THUC_UONG', 'DO_AN', 'THUOC_LA', 'CHO_THUE', 'DICH_VU')),
    base_unit TEXT NOT NULL DEFAULT 'Lon', -- Đơn vị bán lẻ (Lon, Chai, Gói)
    import_unit TEXT DEFAULT 'Thung',      -- Đơn vị nhập kho (Thùng, Két)
    conversion_rate INTEGER DEFAULT 1,     -- 1 Thùng = 24 Lon
    cost_price REAL DEFAULT 0,             -- Giá vốn
    selling_price REAL NOT NULL CHECK (selling_price >= 0), -- Giá bán
    stock_quantity INTEGER NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    min_stock_alert INTEGER DEFAULT 10,    -- Ngưỡng cảnh báo sắp hết hàng
    is_bom TEXT NOT NULL DEFAULT 'false',  -- Hàng pha chế có định lượng
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (club_id, name)
);

-- 6. BẢNG QUẢN LÝ TÀI SẢN & PHỤ KIỆN BIDA (CƠ, BI, MÁY LAU BI, IOT)
CREATE TABLE IF NOT EXISTS equipment_assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    club_id INTEGER NOT NULL REFERENCES clubs(id) ON DELETE CASCADE,
    assigned_table_id INTEGER REFERENCES tables(id) ON DELETE SET NULL,
    asset_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    asset_type TEXT NOT NULL CHECK (asset_type IN ('BALL_SET', 'STANDARD_CUE', 'PREMIUM_CUE', 'SMART_RELAY', 'CAMERA', 'BILLIARD_LIGHT', 'BALL_CLEANER')),
    condition_status TEXT NOT NULL DEFAULT 'GOOD' CHECK (condition_status IN ('NEW', 'GOOD', 'WARNED', 'DAMAGED', 'LOST')),
    status TEXT NOT NULL DEFAULT 'AVAILABLE' CHECK (status IN ('AVAILABLE', 'IN_USE', 'UNDER_MAINTENANCE', 'DISCARDED')),
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 7. BẢNG NHẬT KÝ BẢO TRÌ VÀ THAY THẾ TÀI SẢN
CREATE TABLE IF NOT EXISTS maintenance_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    club_id INTEGER NOT NULL REFERENCES clubs(id) ON DELETE CASCADE,
    table_id INTEGER REFERENCES tables(id) ON DELETE SET NULL,
    asset_id INTEGER REFERENCES equipment_assets(id) ON DELETE SET NULL,
    maintenance_type TEXT NOT NULL CHECK (maintenance_type IN ('FELT_REPLACEMENT', 'TIP_REPLACEMENT', 'CUE_STRAIGHTENING', 'BALL_POLISHING', 'LIGHT_REPAIR', 'ROUTER_RESET')),
    cost REAL DEFAULT 0.0,
    performed_by TEXT NOT NULL,
    description TEXT,
    completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 8. BẢNG CẤU HÌNH TÀI NGUYÊN GENERAL
CREATE TABLE IF NOT EXISTS resource_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    club_id INTEGER NOT NULL REFERENCES clubs(id) ON DELETE CASCADE,
    key_name TEXT NOT NULL,
    value_text TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (club_id, key_name)
);

-- INDEXES DÙNG CHO TOÁN TỬ VẬN HÀNH & TRA CỨU MẠNH
CREATE INDEX IF NOT EXISTS idx_areas_club_id ON areas(club_id);
CREATE INDEX IF NOT EXISTS idx_tables_club_id ON tables(club_id);
CREATE INDEX IF NOT EXISTS idx_tables_area_id ON tables(area_id);
CREATE INDEX IF NOT EXISTS idx_tables_status ON tables(current_status);
CREATE INDEX IF NOT EXISTS idx_table_pricing_rules_lookup ON table_pricing_rules(club_id, table_tier);
CREATE INDEX IF NOT EXISTS idx_products_club_id ON products(club_id);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_equipment_assets_table_id ON equipment_assets(assigned_table_id);
CREATE INDEX IF NOT EXISTS idx_maintenance_logs_table_id ON maintenance_logs(table_id);

-- SEED DATA MẪU
INSERT OR IGNORE INTO clubs (id, name, address, status) VALUES
(1, 'Club Bida Sài Gòn Q5', '123 Nguyễn Văn Cừ, Quận 5', 'ACTIVE'),
(2, 'Club Bida Sài Gòn Q3', '456 Lê Văn Sỹ, Quận 3', 'ACTIVE');

INSERT OR IGNORE INTO areas (id, club_id, name, description, status) VALUES
(1, 1, 'Khu vực Thường (Sảnh chính)', 'Bàn bida tiêu chuẩn', 'ACTIVE'),
(2, 1, 'Khu vực VIP (Phòng lạnh)', 'Bàn bida cao cấp', 'ACTIVE');

INSERT OR IGNORE INTO tables (id, club_id, area_id, name, table_type, table_tier, hourly_rate, current_status, iot_device_id, camera_rtsp_url, total_playing_hours, maintenance_threshold_hours) VALUES
(1, 1, 1, 'Bàn 01', 'POOL_9BALL', 'STANDARD', 60000, 'EMPTY', 'bida/q5/table01/relay', 'rtsp://192.168.1.101/stream1', 120.5, 300.0),
(2, 1, 1, 'Bàn 02', 'POOL_9BALL', 'STANDARD', 60000, 'PLAYING', 'bida/q5/table02/relay', 'rtsp://192.168.1.102/stream1', 285.0, 300.0),
(3, 1, 2, 'Bàn VIP 01', 'CAROM_3CUSHION', 'VIP', 90000, 'EMPTY', 'bida/q5/tablevip01/relay', 'rtsp://192.168.1.103/stream1', 45.0, 400.0);

INSERT OR IGNORE INTO table_pricing_rules (id, club_id, table_tier, day_of_week, start_time, end_time, hourly_rate, is_holiday, description) VALUES
(1, 1, 'STANDARD', NULL, '08:00', '14:00', 40000, 'false', 'Happy hour sáng'),
(2, 1, 'STANDARD', NULL, '14:00', '18:00', 60000, 'false', 'Giờ tiêu chuẩn chiều'),
(3, 1, 'STANDARD', NULL, '18:00', '23:00', 85000, 'false', 'Giờ cao điểm buổi tối'),
(4, 1, 'VIP', NULL, '08:00', '23:00', 100000, 'false', 'Bàn VIP cố định');

INSERT OR IGNORE INTO products (id, club_id, code, name, category, base_unit, import_unit, conversion_rate, cost_price, selling_price, stock_quantity, min_stock_alert, is_bom, status) VALUES
(1, 1, 'P001', 'Bia Heineken Silver', 'THUC_UONG', 'Lon', 'Thung', 24, 16000, 28000, 120, 24, 'false', 'ACTIVE'),
(2, 1, 'P002', 'Redbull (Bò húc)', 'THUC_UONG', 'Lon', 'Thung', 24, 12000, 25000, 96, 24, 'false', 'ACTIVE'),
(3, 1, 'P003', 'Mì xào bò đặc biệt', 'DO_AN', 'Dĩa', 'Dĩa', 1, 20000, 45000, 50, 10, 'true', 'ACTIVE'),
(4, 1, 'P004', 'Cho thuê cơ Carbon VIP', 'CHO_THUE', 'Lượt', 'Lượt', 1, 0, 30000, 5, 1, 'false', 'ACTIVE');

INSERT OR IGNORE INTO equipment_assets (id, club_id, assigned_table_id, asset_code, name, asset_type, condition_status, status, notes) VALUES
(1, 1, 1, 'BALL-01', 'Bộ bi Aramith Tournament Pool', 'BALL_SET', 'GOOD', 'AVAILABLE', 'Đủ 16 bi'),
(2, 1, 1, 'CUE-01', 'Bộ 4 cơ tiêu chuẩn Bàn 01', 'STANDARD_CUE', 'GOOD', 'AVAILABLE', 'Đã thay đầu tẩy mới'),
(3, 1, 1, 'RELAY-01', 'Sonoff Smart Switch 16A (Đèn bàn 1)', 'SMART_RELAY', 'GOOD', 'IN_USE', 'Tích hợp MQTT');

INSERT OR IGNORE INTO maintenance_logs (id, club_id, table_id, asset_id, maintenance_type, cost, performed_by, description) VALUES
(1, 1, 2, NULL, 'FELT_REPLACEMENT', 1200000, 'Kỹ thuật viên Tuấn', 'Bọc lại nỉ Simonis 860 xanh dương cho Bàn 02'),
(2, 1, 1, 2, 'TIP_REPLACEMENT', 150000, 'Nhân viên Nam', 'Thay 2 đầu tẩy Kamui nâu mềm cho cơ bàn 1');
