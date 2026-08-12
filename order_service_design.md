# Order Service Design
## Thiết kế Database chuẩn hóa (1NF, 2NF, 3NF)

---

## 1. Mục đích
Order Service là service quản lý đơn hàng/hóa đơn cho:
- Đơn hàng bàn (table rentals - thanh toán giờ chơi)
- Đơn hàng sản phẩm (products - nước, ăn vặt, v.v.)
- Đơn hàng phụ kiện (accessories - cơ, bộ cách, v.v.)
- Tracking lịch sử giao dịch
- Hỗ trợ discount/voucher

Service này cung cấp:
- Quản lý đơn hàng
- Tính tổng tiền
- Trạng thái thanh toán
- Lịch sử toàn bộ giao dịch
- Dữ liệu cho Billing Service (tạo hóa đơn)

---

## 2. Vai trò của Order Service
- Lưu trữ thông tin đơn hàng
- Quản lý items trong đơn hàng
- Theo dõi trạng thái thanh toán
- Hỗ trợ discount/voucher
- Cung cấp dữ liệu cho báo cáo, phân tích
- Đồng bộ với Resource Service (check stock)
- Đồng bộ với Session Service (khi mở table, tạo order)

---

## 3. Bounded Context

### 3.1 Order Management
Quản lý thông tin đơn hàng:
- Thông tin khách hàng (nếu không phải guest)
- Thời gian tạo/cập nhật
- Bàn sử dụng
- Trạng thái đơn (PENDING, PROCESSING, PAID, CANCELLED)
- Club_id (từ club service)

### 3.2 Order Item Management
Quản lý items trong đơn:
- Product/Table/Accessory được order
- Quantity (số lượng)
- Unit price (giá tại thời điểm order)
- Subtotal (quantity × unit_price)
- Notes (ghi chú đặc biệt)

### 3.3 Discount & Voucher Management
Quản lý giảm giá:
- Voucher codes
- Discount amount (VND hoặc %)
- Validity period
- Usage limits
- Applied discounts

### 3.4 Payment Tracking
Theo dõi thanh toán:
- Total order value
- Discount applied
- Final amount
- Payment status
- Payment method (CASH, CARD, TRANSFER)
- Payment timestamp

### 3.5 Order History & Analytics
Lưu lịch sử:
- Tất cả giao dịch
- Support for reporting, analytics

---

## 4. Thiết kế Database chuẩn hóa (1NF, 2NF, 3NF)

```sql
-- 1. Bảng orders (1NF, 2NF, 3NF)
CREATE TABLE orders (
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
-- Phân tích: 1NF ✓ (mỗi cột là atomic)
--           2NF ✓ (tất cả thuộc tính phụ thuộc vào khóa chính ID)
--           3NF ✓ (không có phụ thuộc bắc cầu)
-- Lưu ý: table_id, customer_id là references tới Resource Service, Customer Service
--        staff_id là reference tới Club Service
--        club_id dùng để partition data

-- 2. Bảng order_items (1NF, 2NF, 3NF)
CREATE TABLE order_items (
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
-- Phân tích: 1NF ✓ (mỗi cột là atomic - subtotal = quantity × unit_price tính từ 2 cột khác)
--           2NF ✓ (tất cả thuộc tính phụ thuộc toàn phần vào composite key order_id + item_id)
--           3NF ✓ (không có phụ thuộc bắc cầu)
-- Lưu ý: item_id là reference tới Resource Service (product/table/accessory)
--        unit_price lưu giá tại thời điểm order (không lấy giá hiện tại)
--        subtotal = quantity × unit_price (có thể tính lại, nhưng lưu để query nhanh)

-- 3. Bảng vouchers (1NF, 2NF, 3NF)
CREATE TABLE vouchers (
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
-- Phân tích: 1NF ✓ 2NF ✓ 3NF ✓
-- Lưu ý: club_id cho phép voucher khác nhau cho từng club
--        max_discount (cho discount type PERCENT)

-- 4. Bảng order_discounts (1NF, 2NF, 3NF)
CREATE TABLE order_discounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    voucher_id INTEGER REFERENCES vouchers(id) ON DELETE SET NULL,
    discount_type TEXT NOT NULL CHECK (discount_type IN ('VOUCHER', 'MANUAL')),
    discount_amount REAL NOT NULL CHECK (discount_amount >= 0),
    applied_by INTEGER NOT NULL,
    reason TEXT,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- Phân tích: 1NF ✓ 2NF ✓ 3NF ✓
-- Lưu ý: Tách riêng để track từng discount
--        applied_by là staff_id (ai apply discount)
--        Cho phép nhiều discount cho 1 order

-- 5. Bảng order_payments (1NF, 2NF, 3NF)
CREATE TABLE order_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    amount REAL NOT NULL CHECK (amount > 0),
    payment_method TEXT NOT NULL CHECK (payment_method IN ('CASH', 'CARD', 'TRANSFER')),
    reference_code TEXT,
    notes TEXT,
    recorded_by INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- Phân tích: 1NF ✓ 2NF ✓ 3NF ✓
-- Lưu ý: Cho phép nhiều payment cho 1 order (PARTIAL payments)
--        reference_code cho bank transfer traceability

-- 6. Bảng order_status_history (1NF, 2NF, 3NF)
CREATE TABLE order_status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    from_status TEXT,
    to_status TEXT NOT NULL,
    changed_by INTEGER NOT NULL,
    reason TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- Phân tích: 1NF ✓ 2NF ✓ 3NF ✓
-- Lưu ý: Track mỗi status change cho audit trail

-- Indexes để tối ưu performance
CREATE INDEX idx_orders_club_id ON orders(club_id);
CREATE INDEX idx_orders_table_id ON orders(table_id);
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_staff_id ON orders(staff_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_payment_status ON orders(payment_status);
CREATE INDEX idx_orders_created_at ON orders(created_at);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_item_type ON order_items(item_type);
CREATE INDEX idx_vouchers_club_id ON vouchers(club_id);
CREATE INDEX idx_vouchers_code ON vouchers(code);
CREATE INDEX idx_order_discounts_order_id ON order_discounts(order_id);
CREATE INDEX idx_order_discounts_voucher_id ON order_discounts(voucher_id);
CREATE INDEX idx_order_payments_order_id ON order_payments(order_id);
CREATE INDEX idx_order_status_history_order_id ON order_status_history(order_id);
```

---

## 5. Entity-Relationship Diagram (ERD)

```
┌─────────────┐
│   orders    │
├─────────────┤
│ id (PK)     │
│ club_id     │ ──┐
│ table_id    │ ──┤─── references Resource Service
│ customer_id │ ──┤─── references Customer Service
│ staff_id    │ ──┴─── references Club Service
│ status      │
│ total_amount│
│ discount_amt│
│ final_amt   │
│ payment_*   │
│ created_at  │
└─────────────┘
      │
      │ 1:N
      ▼
┌──────────────────┐
│  order_items     │
├──────────────────┤
│ id (PK)          │
│ order_id (FK)    │
│ item_type        │
│ item_id          │
│ quantity         │
│ unit_price       │
│ subtotal         │
└──────────────────┘

      ┌─────────────────────┐
      │ order_discounts     │
      ├─────────────────────┤
      │ id (PK)             │
      │ order_id (FK)       │
      │ voucher_id (FK)     │
      │ discount_type       │
      │ discount_amount     │
      └─────────────────────┘
            │
            │ N:1
            ▼
      ┌─────────────────────┐
      │   vouchers          │
      ├─────────────────────┤
      │ id (PK)             │
      │ club_id             │
      │ code (UNIQUE)       │
      │ discount_type       │
      │ discount_value      │
      │ valid_from          │
      │ valid_to            │
      │ max_usage           │
      │ current_usage       │
      └─────────────────────┘

      ┌─────────────────────┐
      │ order_payments      │
      ├─────────────────────┤
      │ id (PK)             │
      │ order_id (FK)       │
      │ amount              │
      │ payment_method      │
      │ reference_code      │
      │ created_at          │
      └─────────────────────┘

      ┌────────────────────────┐
      │ order_status_history   │
      ├────────────────────────┤
      │ id (PK)                │
      │ order_id (FK)          │
      │ from_status            │
      │ to_status              │
      │ changed_by             │
      │ created_at             │
      └────────────────────────┘
```

---

## 6. Quy tắc Chuẩn Hóa

### 6.1 1NF (First Normal Form)
✓ **Áp dụng**: Mỗi cột chỉ chứa giá trị nguyên tố
- `order_items.unit_price` - giá đơn vị (atomic)
- `order_items.subtotal` - tổng cộng (atomic, mặc dù có thể tính từ quantity × unit_price)
- `vouchers.discount_value` - giá trị giảm (atomic)

### 6.2 2NF (Second Normal Form)
✓ **Áp dụng**: Thỏa 1NF + tất cả non-key attributes phụ thuộc toàn phần vào khóa chính
- `order_items` - phụ thuộc vào composite key (order_id, item_id)
  - Tách riêng vì một order có nhiều items
- `order_discounts` - phụ thuộc vào order_id
  - Tách riêng vì một order có thể áp dụng nhiều discount
- `order_payments` - phụ thuộc vào order_id
  - Tách riêng vì order có thể thanh toán nhiều lần (PARTIAL payments)

### 6.3 3NF (Third Normal Form)
✓ **Áp dụng**: Thỏa 2NF + không có phụ thuộc bắc cầu
- `vouchers` - tách riêng từ order_discounts
  - Vì voucher là master data, không phụ thuộc vào order
  - Cho phép tái sử dụng voucher cho nhiều orders
- `order_status_history` - tách riêng
  - Vì là audit trail (sparse data), không phải mọi order có lịch sử đầy đủ
- `order_payments` - tách riêng từ orders
  - Vì payment history là dữ liệu tách biệt (sparse)

---

## 7. API Đề Xuất

### 7.1 Order APIs
- `GET /api/orders` - danh sách orders (filter by club, status, date)
- `GET /api/orders/{id}` - chi tiết order
- `POST /api/orders` - tạo order mới
- `PUT /api/orders/{id}` - cập nhật order
- `PATCH /api/orders/{id}/status` - thay đổi trạng thái order
- `DELETE /api/orders/{id}` - hủy order

### 7.2 Order Item APIs
- `GET /api/orders/{order_id}/items` - danh sách items
- `POST /api/orders/{order_id}/items` - thêm item vào order
- `PUT /api/orders/{order_id}/items/{item_id}` - cập nhật quantity/price
- `DELETE /api/orders/{order_id}/items/{item_id}` - xóa item

### 7.3 Discount APIs
- `GET /api/orders/{order_id}/discounts` - danh sách discounts
- `POST /api/orders/{order_id}/discounts` - áp dụng discount/voucher
- `DELETE /api/orders/{order_id}/discounts/{discount_id}` - xóa discount

### 7.4 Voucher APIs
- `GET /api/clubs/{club_id}/vouchers` - danh sách vouchers
- `POST /api/clubs/{club_id}/vouchers` - tạo voucher
- `PUT /api/vouchers/{id}` - cập nhật voucher
- `GET /api/vouchers/check/{code}` - kiểm tra voucher có dùng được không

### 7.5 Payment APIs
- `GET /api/orders/{order_id}/payments` - lịch sử thanh toán
- `POST /api/orders/{order_id}/payments` - ghi nhận thanh toán
- `PUT /api/orders/{order_id}/payments/{payment_id}` - cập nhật payment

### 7.6 Report APIs
- `GET /api/reports/orders/summary` - tổng hợp doanh thu (by club, by date, by product)
- `GET /api/reports/orders/top-products` - top products bán chạy
- `GET /api/reports/orders/payment-status` - trạng thái thanh toán

---

## 8. Mối Quan Hệ Với Các Service Khác

### 8.1 Với Club Service
- Lấy staff_id, club_id để ghi nhận ai tạo order
- Lấy club configuration (timezone, currency, v.v.)

### 8.2 Với Resource Service
- Lấy product/table/accessory info (name, giá mặc định)
- Check stock availability trước khi thêm item
- Update stock khi order được PAID

### 8.3 Với Customer Service
- Lấy customer_id, loyalty points
- Update loyalty points khi order PAID (tích điểm)
- Apply membership discounts

### 8.4 Với Session Service
- Khi session bắt đầu → tạo order (TABLE item)
- Khi session kết thúc → finalize order total_amount
- Customer gọi thêm products → thêm order_items

### 8.5 Với Billing Service
- Order Service gửi PAID orders → Billing Service tạo hóa đơn
- Sync dữ liệu cho report, tax calculation

### 8.6 Với Authorization Service
- Check quyền: chỉ MANAGER+ mới được tạo/approve/delete order
- Check quyền: chỉ ACCOUNTANT mới được record payment

---

## 9. Quy Tắc Nghiệp Vụ

### 9.1 Order Rules
- Mỗi order phải thuộc về một club
- Mỗi order phải có ít nhất một item
- Chỉ STAFF+ mới được tạo order
- Order status flow: PENDING → PROCESSING → PAID (hoặc CANCELLED)
- final_amount = total_amount - sum(discount_amount)
- Không thể xóa order PAID (chỉ có thể CANCEL)

### 9.2 Order Item Rules
- item_type phải là một trong: TABLE, PRODUCT, ACCESSORY
- item_id phải tồn tại trong Resource Service
- quantity phải > 0
- unit_price phải bằng giá tại thời điểm tạo order (không lấy giá hiện tại)
- subtotal = quantity × unit_price
- Không thể xóa item nếu order đã PAID

### 9.3 Discount Rules
- Mỗi order có thể áp dụng nhiều discount
- Discount VOUCHER cần check voucher còn valid không
- Discount MANUAL chỉ MANAGER+ mới được áp dụng
- Tổng discount không thể vượt quá total_amount
- Khi áp dụng voucher → increment voucher.current_usage
- Voucher expires sau valid_to date

### 9.4 Payment Rules
- Payment chỉ được ghi nhận khi order status = PROCESSING hoặc PAID
- Tổng payments phải <= final_amount
- Khi tổng payments = final_amount → payment_status = PAID
- Khi 0 < tổng payments < final_amount → payment_status = PARTIAL
- Không thể record payment âm

### 9.5 Status History Rules
- Mỗi thay đổi status phải record lại với changed_by, reason
- Dùng cho audit trail, dispute resolution

---

## 10. Sample Seed Data

```sql
INSERT INTO orders (id, club_id, table_id, customer_id, staff_id, status, total_amount, discount_amount, final_amount, payment_method, payment_status) VALUES
(1, 1, 1, NULL, 1, 'PAID', 150000, 0, 150000, 'CASH', 'PAID'),
(2, 1, 2, 1, 1, 'PROCESSING', 200000, 20000, 180000, NULL, 'PARTIAL'),
(3, 1, NULL, 2, 1, 'PENDING', 80000, 0, 80000, NULL, 'UNPAID');

INSERT INTO order_items (id, order_id, item_type, item_id, quantity, unit_price, subtotal) VALUES
(1, 1, 'TABLE', 1, 3, 50000, 150000),
(2, 2, 'TABLE', 2, 2, 50000, 100000),
(3, 2, 'PRODUCT', 1, 2, 50000, 100000),
(4, 3, 'PRODUCT', 2, 2, 40000, 80000);

INSERT INTO vouchers (id, club_id, code, discount_type, discount_value, max_discount, valid_from, valid_to, max_usage, current_usage, status) VALUES
(1, 1, 'WELCOME10', 'PERCENT', 10, 50000, '2026-08-01', '2026-12-31', 100, 5, 'ACTIVE'),
(2, 1, 'CASHBACK20K', 'FIXED', 20000, NULL, '2026-08-01', '2026-12-31', 50, 3, 'ACTIVE');

INSERT INTO order_discounts (id, order_id, voucher_id, discount_type, discount_amount, applied_by, reason) VALUES
(1, 2, 1, 'VOUCHER', 20000, 1, 'WELCOME10 coupon');

INSERT INTO order_payments (id, order_id, amount, payment_method, reference_code, recorded_by) VALUES
(1, 1, 150000, 'CASH', NULL, 1),
(2, 2, 100000, 'CARD', 'CARD-2026-08-12-001', 1);

INSERT INTO order_status_history (id, order_id, from_status, to_status, changed_by, reason) VALUES
(1, 1, NULL, 'PENDING', 1, 'Order created'),
(2, 1, 'PENDING', 'PROCESSING', 1, 'Customer started playing'),
(3, 1, 'PROCESSING', 'PAID', 1, 'Payment received in full'),
(4, 2, NULL, 'PENDING', 1, 'Order created'),
(5, 2, 'PENDING', 'PROCESSING', 1, 'Customer started playing');
```

---

## 11. Kết Luận

Order Service được thiết kế theo đúng chuẩn hóa cơ sở dữ liệu 1NF, 2NF, 3NF:
- **1NF**: Tất cả cột đều chứa giá trị nguyên tố
- **2NF**: Không có partial dependency (tách bảng chi tiết items, discounts, payments)
- **3NF**: Không có transitive dependency (tách bảng master data vouchers)

**Thiết kế linh hoạt**:
- ✓ Hỗ trợ multiple items per order
- ✓ Hỗ trợ multiple discounts per order
- ✓ Hỗ trợ partial payments
- ✓ Hỗ trợ audit trail (status history)
- ✓ Tách biệt master data (vouchers) từ transaction data (orders)

Điều này giúp:
- ✓ Giảm redundancy
- ✓ Dễ bảo trì và mở rộng (thêm discount type, payment method dễ dàng)
- ✓ Tốc độ query nhanh (proper indexes)
- ✓ Tính toàn vẹn dữ liệu cao (foreign keys, constraints)
- ✓ Support complex business logic (discounts, vouchers, partial payments)
- ✓ Tách biệt trách nhiệm giữa các service (microservices architecture)
