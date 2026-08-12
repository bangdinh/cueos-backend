-- SQLite schema for Order Service
-- Generated from order_service_design.md

-- 1. Bảng orders
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    club_id INTEGER NOT NULL,
    table_id INTEGER,
    customer_id INTEGER,
    staff_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'PROCESSING', 'PAID', 'CANCELLED')),
    total_amount REAL NOT NULL DEFAULT 0,
    discount_amount REAL NOT NULL DEFAULT 0,
    final_amount REAL NOT NULL DEFAULT 0,
    payment_method TEXT CHECK (payment_method IN ('CASH', 'CARD', 'TRANSFER', NULL)),
    payment_status TEXT NOT NULL DEFAULT 'UNPAID' CHECK (payment_status IN ('UNPAID', 'PAID', 'PARTIAL')),
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    paid_at TEXT
);

-- 2. Bảng order_items
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    item_type TEXT NOT NULL CHECK (item_type IN ('TABLE', 'PRODUCT', 'ACCESSORY')),
    item_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
    unit_price REAL NOT NULL CHECK (unit_price >= 0),
    subtotal REAL NOT NULL CHECK (subtotal >= 0),
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 3. Bảng vouchers
CREATE TABLE IF NOT EXISTS vouchers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    club_id INTEGER NOT NULL,
    code TEXT NOT NULL UNIQUE,
    discount_type TEXT NOT NULL CHECK (discount_type IN ('FIXED', 'PERCENT')),
    discount_value REAL NOT NULL CHECK (discount_value > 0),
    max_discount REAL CHECK (max_discount >= 0),
    valid_from TEXT NOT NULL,
    valid_to TEXT NOT NULL,
    max_usage INTEGER CHECK (max_usage > 0),
    current_usage INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE', 'EXPIRED')),
    description TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 4. Bảng order_discounts
CREATE TABLE IF NOT EXISTS order_discounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    voucher_id INTEGER REFERENCES vouchers(id) ON DELETE SET NULL,
    discount_type TEXT NOT NULL CHECK (discount_type IN ('VOUCHER', 'MANUAL')),
    discount_amount REAL NOT NULL CHECK (discount_amount >= 0),
    applied_by INTEGER NOT NULL,
    reason TEXT,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 5. Bảng order_payments
CREATE TABLE IF NOT EXISTS order_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    amount REAL NOT NULL CHECK (amount > 0),
    payment_method TEXT NOT NULL CHECK (payment_method IN ('CASH', 'CARD', 'TRANSFER')),
    reference_code TEXT,
    notes TEXT,
    recorded_by INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 6. Bảng order_status_history
CREATE TABLE IF NOT EXISTS order_status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    from_status TEXT,
    to_status TEXT NOT NULL,
    changed_by INTEGER NOT NULL,
    reason TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_orders_club_id ON orders(club_id);
CREATE INDEX IF NOT EXISTS idx_orders_table_id ON orders(table_id);
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_staff_id ON orders(staff_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_payment_status ON orders(payment_status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_item_type ON order_items(item_type);
CREATE INDEX IF NOT EXISTS idx_vouchers_club_id ON vouchers(club_id);
CREATE INDEX IF NOT EXISTS idx_vouchers_code ON vouchers(code);
CREATE INDEX IF NOT EXISTS idx_order_discounts_order_id ON order_discounts(order_id);
CREATE INDEX IF NOT EXISTS idx_order_discounts_voucher_id ON order_discounts(voucher_id);
CREATE INDEX IF NOT EXISTS idx_order_payments_order_id ON order_payments(order_id);
CREATE INDEX IF NOT EXISTS idx_order_status_history_order_id ON order_status_history(order_id);

-- Sample Seed Data
INSERT OR IGNORE INTO orders (id, club_id, table_id, customer_id, staff_id, status, total_amount, discount_amount, final_amount, payment_method, payment_status) VALUES
(1, 1, 1, NULL, 1, 'PAID', 150000, 0, 150000, 'CASH', 'PAID'),
(2, 1, 2, 1, 1, 'PROCESSING', 200000, 20000, 180000, NULL, 'PARTIAL'),
(3, 1, NULL, 2, 1, 'PENDING', 80000, 0, 80000, NULL, 'UNPAID');

INSERT OR IGNORE INTO order_items (id, order_id, item_type, item_id, quantity, unit_price, subtotal) VALUES
(1, 1, 'TABLE', 1, 3, 50000, 150000),
(2, 2, 'TABLE', 2, 2, 50000, 100000),
(3, 2, 'PRODUCT', 1, 2, 50000, 100000),
(4, 3, 'PRODUCT', 2, 2, 40000, 80000);

INSERT OR IGNORE INTO vouchers (id, club_id, code, discount_type, discount_value, max_discount, valid_from, valid_to, max_usage, current_usage, status) VALUES
(1, 1, 'WELCOME10', 'PERCENT', 10, 50000, '2026-08-01', '2026-12-31', 100, 5, 'ACTIVE'),
(2, 1, 'CASHBACK20K', 'FIXED', 20000, NULL, '2026-08-01', '2026-12-31', 50, 3, 'ACTIVE');

INSERT OR IGNORE INTO order_discounts (id, order_id, voucher_id, discount_type, discount_amount, applied_by, reason) VALUES
(1, 2, 1, 'VOUCHER', 20000, 1, 'WELCOME10 coupon');

INSERT OR IGNORE INTO order_payments (id, order_id, amount, payment_method, reference_code, recorded_by) VALUES
(1, 1, 150000, 'CASH', NULL, 1),
(2, 2, 100000, 'CARD', 'CARD-2026-08-12-001', 1);

INSERT OR IGNORE INTO order_status_history (id, order_id, from_status, to_status, changed_by, reason) VALUES
(1, 1, NULL, 'PENDING', 1, 'Order created'),
(2, 1, 'PENDING', 'PROCESSING', 1, 'Customer started playing'),
(3, 1, 'PROCESSING', 'PAID', 1, 'Payment received in full'),
(4, 2, NULL, 'PENDING', 1, 'Order created'),
(5, 2, 'PENDING', 'PROCESSING', 1, 'Customer started playing');
