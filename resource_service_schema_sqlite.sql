-- SQLite schema for Resource Service
-- Simple and fast for local development

CREATE TABLE IF NOT EXISTS clubs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS areas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    club_id INTEGER NOT NULL REFERENCES clubs(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    club_id INTEGER NOT NULL REFERENCES clubs(id) ON DELETE CASCADE,
    area_id INTEGER REFERENCES areas(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    table_type TEXT NOT NULL DEFAULT 'STANDARD',
    table_tier TEXT NOT NULL DEFAULT 'REGULAR',
    price_per_hour REAL NOT NULL DEFAULT 50000.0,
    camera_url TEXT,
    current_status TEXT NOT NULL DEFAULT 'EMPTY',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    club_id INTEGER NOT NULL REFERENCES clubs(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'THUC_UONG',
    price REAL NOT NULL DEFAULT 0 CHECK (price >= 0),
    stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    image_url TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (club_id, name)
);

CREATE TABLE IF NOT EXISTS table_accessories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    club_id INTEGER NOT NULL REFERENCES clubs(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    accessory_type TEXT NOT NULL,
    quantity_available INTEGER NOT NULL DEFAULT 0 CHECK (quantity_available >= 0),
    condition_status TEXT NOT NULL DEFAULT 'GOOD',
    status TEXT NOT NULL DEFAULT 'AVAILABLE',
    assigned_table_id INTEGER REFERENCES tables(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS equipments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    club_id INTEGER NOT NULL REFERENCES clubs(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    equipment_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    location TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS resource_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    club_id INTEGER NOT NULL REFERENCES clubs(id) ON DELETE CASCADE,
    key_name TEXT NOT NULL,
    value_text TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (club_id, key_name)
);

CREATE INDEX IF NOT EXISTS idx_areas_club_id ON areas(club_id);
CREATE INDEX IF NOT EXISTS idx_tables_club_id ON tables(club_id);
CREATE INDEX IF NOT EXISTS idx_tables_area_id ON tables(area_id);
CREATE INDEX IF NOT EXISTS idx_products_club_id ON products(club_id);
CREATE INDEX IF NOT EXISTS idx_table_accessories_club_id ON table_accessories(club_id);
CREATE INDEX IF NOT EXISTS idx_table_accessories_table_id ON table_accessories(assigned_table_id);
CREATE INDEX IF NOT EXISTS idx_equipments_club_id ON equipments(club_id);
CREATE INDEX IF NOT EXISTS idx_resource_configs_club_id ON resource_configs(club_id);

INSERT OR IGNORE INTO clubs (id, name, address, status) VALUES
(1, 'Club Bida A', '123 Nguyễn Văn Cừ, Quận 5', 'ACTIVE'),
(2, 'Club Bida B', '456 Lê Văn Sỹ, Quận 3', 'ACTIVE');

INSERT OR IGNORE INTO areas (id, club_id, name, description, status) VALUES
(1, 1, 'Khu vực chính', 'Bàn bida chính', 'ACTIVE'),
(2, 1, 'Khu vực VIP', 'Bàn bida VIP', 'ACTIVE');

INSERT OR IGNORE INTO tables (id, club_id, area_id, name, table_type, table_tier, price_per_hour, camera_url, current_status) VALUES
(1, 1, 1, 'Bàn 01', 'STANDARD', 'REGULAR', 50000, 'rtsp://camera1', 'EMPTY'),
(2, 1, 2, 'Bàn VIP 01', 'VIP', 'PREMIUM', 80000, 'rtsp://camera2', 'PLAYING');

INSERT OR IGNORE INTO products (id, club_id, name, category, price, stock, image_url, status) VALUES
(1, 1, 'Coca Cola', 'THUC_UONG', 25000, 50, '', 'ACTIVE'),
(2, 1, 'Bia', 'THUC_UONG', 35000, 30, '', 'ACTIVE');

INSERT OR IGNORE INTO table_accessories (id, club_id, name, accessory_type, quantity_available, condition_status, status, assigned_table_id) VALUES
(1, 1, 'Cơ bida', 'CUE', 10, 'GOOD', 'AVAILABLE', 1),
(2, 1, 'Bi bida', 'BALL', 3, 'GOOD', 'AVAILABLE', 1);

INSERT OR IGNORE INTO equipments (id, club_id, name, equipment_type, status, location) VALUES
(1, 1, 'Camera 01', 'CAMERA', 'ACTIVE', 'Bàn 01'),
(2, 1, 'Máy in hóa đơn', 'PRINTER', 'ACTIVE', 'Quầy thu ngân');

INSERT OR IGNORE INTO resource_configs (id, club_id, key_name, value_text, description) VALUES
(1, 1, 'table_price_default', '50000', 'Giá mặc định cho bàn thường'),
(2, 1, 'vip_table_price_default', '80000', 'Giá mặc định cho bàn VIP');
