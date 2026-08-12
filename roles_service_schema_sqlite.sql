-- SQLite schema for Roles / Authorization Service
-- Generated from roles_service_design.md

-- 1. Bảng roles
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. Bảng permissions
CREATE TABLE IF NOT EXISTS permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    resource TEXT NOT NULL,
    action TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (resource, action)
);

-- 3. Bảng role_permissions (Junction Table)
CREATE TABLE IF NOT EXISTS role_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    assigned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (role_id, permission_id)
);

-- 4. Bảng permission_hierarchy (Phân cấp permission tùy chọn)
CREATE TABLE IF NOT EXISTS permission_hierarchy (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
    child_permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    UNIQUE (parent_permission_id, child_permission_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_roles_status ON roles(status);
CREATE INDEX IF NOT EXISTS idx_permissions_resource ON permissions(resource);
CREATE INDEX IF NOT EXISTS idx_permissions_action ON permissions(action);
CREATE INDEX IF NOT EXISTS idx_role_permissions_role_id ON role_permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_role_permissions_permission_id ON role_permissions(permission_id);

-- Sample Seed Data
INSERT OR IGNORE INTO roles (id, name, description, status) VALUES
(1, 'SUPER_ADMIN', 'Quản trị viên toàn hệ thống', 'ACTIVE'),
(2, 'HQ_MANAGER', 'Quản lý tập đoàn HQ', 'ACTIVE'),
(3, 'CLUB_ADMIN', 'Quản trị viên club', 'ACTIVE'),
(4, 'CLUB_MANAGER', 'Quản lý club', 'ACTIVE'),
(5, 'STAFF', 'Nhân viên', 'ACTIVE');

-- Products permissions
INSERT OR IGNORE INTO permissions (id, name, resource, action, description, status) VALUES
(1, 'CREATE_PRODUCT', 'product', 'create', 'Tạo sản phẩm mới', 'ACTIVE'),
(2, 'READ_PRODUCT', 'product', 'read', 'Xem sản phẩm', 'ACTIVE'),
(3, 'UPDATE_PRODUCT', 'product', 'update', 'Cập nhật sản phẩm', 'ACTIVE'),
(4, 'DELETE_PRODUCT', 'product', 'delete', 'Xóa sản phẩm', 'ACTIVE');

-- Tables permissions
INSERT OR IGNORE INTO permissions (id, name, resource, action, description, status) VALUES
(5, 'CREATE_TABLE', 'table', 'create', 'Tạo bàn mới', 'ACTIVE'),
(6, 'READ_TABLE', 'table', 'read', 'Xem bàn', 'ACTIVE'),
(7, 'UPDATE_TABLE', 'table', 'update', 'Cập nhật bàn', 'ACTIVE'),
(8, 'DELETE_TABLE', 'table', 'delete', 'Xóa bàn', 'ACTIVE');

-- Reports permissions
INSERT OR IGNORE INTO permissions (id, name, resource, action, description, status) VALUES
(9, 'VIEW_REPORT', 'report', 'read', 'Xem báo cáo', 'ACTIVE'),
(10, 'EXPORT_REPORT', 'report', 'export', 'Xuất báo cáo', 'ACTIVE');

-- Session permissions
INSERT OR IGNORE INTO permissions (id, name, resource, action, description, status) VALUES
(11, 'START_SESSION', 'session', 'create', 'Bắt đầu phiên chơi', 'ACTIVE'),
(12, 'END_SESSION', 'session', 'update', 'Kết thúc phiên chơi', 'ACTIVE');

-- Assign permissions to SUPER_ADMIN (tất cả permissions)
INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES
(1, 1), (1, 2), (1, 3), (1, 4),
(1, 5), (1, 6), (1, 7), (1, 8),
(1, 9), (1, 10), (1, 11), (1, 12);

-- Assign permissions to CLUB_ADMIN (tất cả permissions trong club)
INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES
(3, 1), (3, 2), (3, 3), (3, 4),
(3, 5), (3, 6), (3, 7), (3, 8),
(3, 9), (3, 10);

-- Assign permissions to CLUB_MANAGER (xem và cập nhật)
INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES
(4, 2), (4, 3), (4, 6), (4, 7),
(4, 9), (4, 11), (4, 12);

-- Assign permissions to STAFF (chỉ xem và thao tác phiên chơi)
INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES
(5, 2), (5, 6), (5, 9), (5, 11);
