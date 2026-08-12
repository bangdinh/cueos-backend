-- SQLite schema for Club Service (Updated)
-- Generated from club_service_design_updated.md

-- 1. Bảng clubs
CREATE TABLE IF NOT EXISTS clubs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    address TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE', 'SUSPENDED')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. Bảng staffs
CREATE TABLE IF NOT EXISTS staffs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    club_id INTEGER NOT NULL REFERENCES clubs(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    position TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 3. Bảng staff_roles (Mapping staff ↔ role từ Authorization Service)
CREATE TABLE IF NOT EXISTS staff_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    staff_id INTEGER NOT NULL REFERENCES staffs(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL,
    assigned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (staff_id, role_id)
);

-- 4. Bảng user_accounts
CREATE TABLE IF NOT EXISTS user_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    staff_id INTEGER NOT NULL UNIQUE REFERENCES staffs(id) ON DELETE CASCADE,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    is_active TEXT NOT NULL DEFAULT 'true',
    last_login TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 5. Bảng club_configurations
CREATE TABLE IF NOT EXISTS club_configurations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    club_id INTEGER NOT NULL UNIQUE REFERENCES clubs(id) ON DELETE CASCADE,
    working_hours_start TEXT,
    working_hours_end TEXT,
    timezone TEXT DEFAULT 'Asia/Ho_Chi_Minh',
    currency TEXT DEFAULT 'VND',
    max_tables INTEGER DEFAULT 20,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 6. Bảng club_settings (key-value)
CREATE TABLE IF NOT EXISTS club_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    club_id INTEGER NOT NULL REFERENCES clubs(id) ON DELETE CASCADE,
    setting_key TEXT NOT NULL,
    setting_value TEXT,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (club_id, setting_key)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_staffs_club_id ON staffs(club_id);
CREATE INDEX IF NOT EXISTS idx_staff_roles_staff_id ON staff_roles(staff_id);
CREATE INDEX IF NOT EXISTS idx_user_accounts_staff_id ON user_accounts(staff_id);
CREATE INDEX IF NOT EXISTS idx_club_configurations_club_id ON club_configurations(club_id);
CREATE INDEX IF NOT EXISTS idx_club_settings_club_id ON club_settings(club_id);

-- Sample Seed Data
INSERT OR IGNORE INTO clubs (id, name, address, phone, email, status) VALUES
(1, 'Club Bida Sài Gòn', '123 Nguyễn Văn Cừ, Quận 5', '0283456789', 'sg@club.com', 'ACTIVE'),
(2, 'Club Bida Hà Nội', '456 Bà Triệu, Hoàn Kiếm', '0243456789', 'hn@club.com', 'ACTIVE');

INSERT OR IGNORE INTO staffs (id, club_id, full_name, phone, email, position, status) VALUES
(1, 1, 'Nguyễn Văn A', '0901234567', 'a@club.com', 'Quản lý', 'ACTIVE'),
(2, 1, 'Trần Thị B', '0902345678', 'b@club.com', 'Thu ngân', 'ACTIVE');

INSERT OR IGNORE INTO staff_roles (id, staff_id, role_id, assigned_at) VALUES
(1, 1, 2, CURRENT_TIMESTAMP),  -- role 2 = CLUB_MANAGER (từ Authorization Service)
(2, 2, 5, CURRENT_TIMESTAMP);  -- role 5 = STAFF (từ Authorization Service)

INSERT OR IGNORE INTO user_accounts (id, staff_id, username, password_hash, is_active) VALUES
(1, 1, 'manager_a', 'hashed_password_1', 'true'),
(2, 2, 'staff_b', 'hashed_password_2', 'true');

INSERT OR IGNORE INTO club_configurations (id, club_id, working_hours_start, working_hours_end, timezone, currency, max_tables) VALUES
(1, 1, '08:00', '23:00', 'Asia/Ho_Chi_Minh', 'VND', 15),
(2, 2, '09:00', '24:00', 'Asia/Ho_Chi_Minh', 'VND', 20);

INSERT OR IGNORE INTO club_settings (id, club_id, setting_key, setting_value, description) VALUES
(1, 1, 'table_price_default', '50000', 'Giá mặc định cho bàn thường'),
(2, 1, 'vip_table_price_default', '80000', 'Giá mặc định cho bàn VIP');
