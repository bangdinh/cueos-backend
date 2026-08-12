# Session Service Design
## Thiết kế Database chuẩn hóa (1NF, 2NF, 3NF)

---

## 1. Mục đích
Session Service là service quản lý phiên chơi (play sessions) tại club bida:
- Tracking session (khi mở bàn cho khách)
- Quản lý thời gian chơi (start time, end time, duration)
- Quản lý người chơi (customers, members)
- Theo dõi bàn sử dụng (table status, availability)
- Tính giá dựa trên duration + table type
- Kết nối với Order Service (tạo order cho session)

Service này cung cấp:
- Real-time tracking phiên chơi
- Pricing calculation dựa trên bàn + thời gian
- Session history & analytics
- Dữ liệu cho reporting, statistics

---

## 2. Vai trò của Session Service
- Lưu trữ thông tin phiên chơi
- Track thời gian sử dụng bàn
- Quản lý người chơi tham gia
- Tính toán giá dựa trên duration
- Cung cấp dữ liệu cho Order Service
- Support real-time status (ACTIVE, PAUSED, COMPLETED, CANCELLED)
- Tracking bàn availability

---

## 3. Bounded Context

### 3.1 Session Management
Quản lý thông tin phiên chơi:
- Thời gian bắt đầu (start_time)
- Thời gian kết thúc (end_time)
- Thời lượng (duration in minutes)
- Trạng thái (ACTIVE, PAUSED, COMPLETED, CANCELLED)
- Bàn sử dụng
- Staff who opened the session

### 3.2 Session Participants
Quản lý người chơi:
- Customers/Members tham gia
- Role (PRIMARY, SECONDARY, SPECTATOR)
- Phí chia sẻ (split payment nếu cần)

### 3.3 Table Usage Tracking
Theo dõi sử dụng bàn:
- Table ID
- Start time
- End time
- Pause count (bàn bị pause bao lần)
- Total active time (loại trừ pause time)

### 3.4 Session Pricing
Tính giá phiên chơi:
- Base price (từ Resource Service)
- Duration (start → end)
- Surcharge (nếu vượt quá time slot)
- Extras (add-ons, accessories)
- Final price

### 3.5 Session History & Analytics
Lưu lịch sử:
- Mỗi status change
- Mỗi participant addition/removal
- Mỗi pricing change
- Support for reporting, analytics

---

## 4. Thiết kế Database chuẩn hóa (1NF, 2NF, 3NF)

```sql
-- 1. Bảng sessions (1NF, 2NF, 3NF)
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    club_id INTEGER NOT NULL,
    table_id INTEGER NOT NULL,
    staff_id INTEGER NOT NULL,
    order_id INTEGER,
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'PAUSED', 'COMPLETED', 'CANCELLED')),
    start_time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    pause_start_time TEXT,
    end_time TEXT,
    total_pause_duration INTEGER DEFAULT 0,
    calculated_price REAL NOT NULL DEFAULT 0,
    final_price REAL,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- Phân tích: 1NF ✓ (mỗi cột là atomic)
--           2NF ✓ (tất cả thuộc tính phụ thuộc vào khóa chính ID)
--           3NF ✓ (không có phụ thuộc bắc cầu)
-- Lưu ý: table_id, club_id references Resource Service
--        staff_id references Club Service
--        order_id references Order Service (khi session kết thúc)
--        total_pause_duration = tổng thời gian pause (seconds)

-- 2. Bảng session_participants (1NF, 2NF, 3NF)
CREATE TABLE session_participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    customer_id INTEGER NOT NULL,
    participant_role TEXT NOT NULL DEFAULT 'PRIMARY' CHECK (participant_role IN ('PRIMARY', 'SECONDARY', 'SPECTATOR')),
    payment_share REAL DEFAULT 100,
    notes TEXT,
    added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- Phân tích: 1NF ✓ 2NF ✓ 3NF ✓
-- Lưu ý: customer_id references Customer Service
--        payment_share = % chia thanh toán (phần trăm hoặc VND)
--        Cho phép nhiều người chơi 1 bàn (split payments)

-- 3. Bảng session_pricing_history (1NF, 2NF, 3NF)
CREATE TABLE session_pricing_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    price_type TEXT NOT NULL CHECK (price_type IN ('BASE', 'SURCHARGE', 'EXTRA', 'DISCOUNT')),
    amount REAL NOT NULL,
    description TEXT,
    calculated_by INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- Phân tích: 1NF ✓ 2NF ✓ 3NF ✓
-- Lưu ý: Track từng component của pricing
--        price_type = loại giá (base, surcharge, extra, discount)
--        calculated_by = staff_id (ai tính)

-- 4. Bảng session_pause_history (1NF, 2NF, 3NF)
CREATE TABLE session_pause_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    pause_start TEXT NOT NULL,
    pause_end TEXT,
    pause_duration INTEGER,
    reason TEXT,
    paused_by INTEGER NOT NULL,
    resumed_by INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- Phân tích: 1NF ✓ 2NF ✓ 3NF ✓
-- Lưu ý: Track mỗi pause/resume action
--        pause_duration = tính từ pause_end - pause_start (seconds)
--        Dùng cho audit trail, dispute resolution

-- 5. Bảng session_status_history (1NF, 2NF, 3NF)
CREATE TABLE session_status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    from_status TEXT,
    to_status TEXT NOT NULL,
    changed_by INTEGER NOT NULL,
    reason TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- Phân tích: 1NF ✓ 2NF ✓ 3NF ✓
-- Lưu ý: Track mỗi status change (ACTIVE → PAUSED → ACTIVE → COMPLETED)
--        changed_by = staff_id

-- 6. Bảng session_notes (1NF, 2NF, 3NF)
CREATE TABLE session_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    note_text TEXT NOT NULL,
    noted_by INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- Phân tích: 1NF ✓ 2NF ✓ 3NF ✓
-- Lưu ý: Separate notes table cho sparse data (không phải session nào cũng có notes)
--        Cho phép multiple notes per session

-- Indexes để tối ưu performance
CREATE INDEX idx_sessions_club_id ON sessions(club_id);
CREATE INDEX idx_sessions_table_id ON sessions(table_id);
CREATE INDEX idx_sessions_staff_id ON sessions(staff_id);
CREATE INDEX idx_sessions_order_id ON sessions(order_id);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_start_time ON sessions(start_time);
CREATE INDEX idx_sessions_end_time ON sessions(end_time);
CREATE INDEX idx_session_participants_session_id ON session_participants(session_id);
CREATE INDEX idx_session_participants_customer_id ON session_participants(customer_id);
CREATE INDEX idx_session_pricing_history_session_id ON session_pricing_history(session_id);
CREATE INDEX idx_session_pause_history_session_id ON session_pause_history(session_id);
CREATE INDEX idx_session_status_history_session_id ON session_status_history(session_id);
CREATE INDEX idx_session_notes_session_id ON session_notes(session_id);
```

---

## 5. Entity-Relationship Diagram (ERD)

```
┌──────────────────┐
│    sessions      │
├──────────────────┤
│ id (PK)          │
│ club_id          │ ──┐
│ table_id         │ ──┤─── references Resource Service
│ staff_id         │ ──┴─── references Club Service
│ order_id         │ ──┐
│ status           │   ├─── references Order Service
│ start_time       │   │
│ pause_start_time │   │
│ end_time         │   │
│ total_pause_dur. │   │
│ calculated_price │   │
│ final_price      │   │
│ created_at       │   │
└──────────────────┘   │
      │                │
      │ 1:N            │
      ├─────────────────┘
      │
      ├──────────────────────────────────────┐
      │                                      │
      ▼                                      ▼
┌──────────────────────┐     ┌──────────────────────┐
│ session_participants │     │ session_pricing_hist │
├──────────────────────┤     ├──────────────────────┤
│ id (PK)              │     │ id (PK)              │
│ session_id (FK)      │     │ session_id (FK)      │
│ customer_id          │     │ price_type           │
│ participant_role     │     │ amount               │
│ payment_share        │     │ description          │
│ added_at             │     │ calculated_by        │
└──────────────────────┘     │ created_at           │
                             └──────────────────────┘

      ┌─────────────────────────────────────────────────────┐
      │                                                     │
      ▼                                                     ▼
┌────────────────────────┐       ┌────────────────────────┐
│ session_pause_history  │       │ session_status_history │
├────────────────────────┤       ├────────────────────────┤
│ id (PK)                │       │ id (PK)                │
│ session_id (FK)        │       │ session_id (FK)        │
│ pause_start            │       │ from_status            │
│ pause_end              │       │ to_status              │
│ pause_duration         │       │ changed_by             │
│ reason                 │       │ reason                 │
│ paused_by              │       │ created_at             │
│ resumed_by             │       └────────────────────────┘
│ created_at             │
└────────────────────────┘

┌──────────────────┐
│ session_notes    │
├──────────────────┤
│ id (PK)          │
│ session_id (FK)  │
│ note_text        │
│ noted_by         │
│ created_at       │
└──────────────────┘
```

---

## 6. Quy tắc Chuẩn Hóa

### 6.1 1NF (First Normal Form)
✓ **Áp dụng**: Mỗi cột chỉ chứa giá trị nguyên tố
- `sessions.total_pause_duration` - tổng thời gian pause (atomic, in seconds)
- `session_pricing_history.amount` - giá từng loại (atomic)
- `session_participants.payment_share` - phần chia thanh toán (atomic)

### 6.2 2NF (Second Normal Form)
✓ **Áp dụng**: Thỏa 1NF + tất cả non-key attributes phụ thuộc toàn phần vào khóa chính
- `session_participants` - phụ thuộc vào session_id + customer_id
  - Tách riêng vì 1 session có nhiều participants
- `session_pricing_history` - phụ thuộc vào session_id
  - Tách riêng vì tracking từng component giá
- `session_pause_history` - phụ thuộc vào session_id
  - Tách riêng vì 1 session có nhiều pause/resume actions

### 6.3 3NF (Third Normal Form)
✓ **Áp dụng**: Thỏa 2NF + không có phụ thuộc bắc cầu
- `session_pause_history` - tách riêng từ sessions
  - Vì pause history là dữ liệu tách biệt (sparse)
  - Không phải session nào cũng có pause
- `session_pricing_history` - tách riêng từ sessions
  - Vì pricing components là dữ liệu tách biệt
  - Allow flexibility trong pricing calculation
- `session_notes` - tách riêng
  - Sparse data (không phải session nào cũng có notes)

---

## 7. API Đề Xuất

### 7.1 Session APIs
- `POST /api/sessions` - tạo session mới (mở bàn)
- `GET /api/sessions/{id}` - chi tiết session
- `PUT /api/sessions/{id}` - cập nhật session
- `PATCH /api/sessions/{id}/status` - thay đổi status (ACTIVE → PAUSED, PAUSED → ACTIVE, → COMPLETED)
- `POST /api/sessions/{id}/complete` - kết thúc session (COMPLETED)
- `POST /api/sessions/{id}/cancel` - hủy session (CANCELLED)
- `GET /api/sessions` - danh sách sessions (filter by club, table, status, date)

### 7.2 Participant APIs
- `GET /api/sessions/{session_id}/participants` - danh sách người chơi
- `POST /api/sessions/{session_id}/participants` - thêm người chơi
- `PUT /api/sessions/{session_id}/participants/{participant_id}` - cập nhật role/payment_share
- `DELETE /api/sessions/{session_id}/participants/{participant_id}` - xóa người chơi

### 7.3 Pricing APIs
- `GET /api/sessions/{session_id}/pricing` - chi tiết giá
- `POST /api/sessions/{session_id}/pricing` - thêm surcharge/extra/discount
- `GET /api/sessions/{session_id}/pricing/calculate` - tính giá hiện tại

### 7.4 Pause APIs
- `POST /api/sessions/{session_id}/pause` - tạm dừng session
- `POST /api/sessions/{session_id}/resume` - tiếp tục session
- `GET /api/sessions/{session_id}/pause-history` - lịch sử pause/resume

### 7.5 Notes APIs
- `GET /api/sessions/{session_id}/notes` - danh sách notes
- `POST /api/sessions/{session_id}/notes` - thêm note
- `DELETE /api/sessions/{session_id}/notes/{note_id}` - xóa note

### 7.6 Analytics APIs
- `GET /api/reports/sessions/summary` - tổng hợp (by club, date, table)
- `GET /api/reports/sessions/popular-tables` - bàn được sử dụng nhiều nhất
- `GET /api/reports/sessions/revenue` - doanh thu từ sessions

---

## 8. Mối Quan Hệ Với Các Service Khác

### 8.1 Với Resource Service
- Lấy table info (table_id, table_type, base_price_per_hour)
- Check table availability trước khi tạo session
- Update table status (AVAILABLE → IN_USE → AVAILABLE)

### 8.2 Với Order Service
- Khi tạo session → tạo draft order (TABLE item)
- Khi session ACTIVE → update order total_amount theo duration
- Khi session COMPLETED → finalize order (ready for payment)
- session.order_id → order.id mapping

### 8.3 Với Customer Service
- Lấy customer info (name, loyalty points, membership status)
- Update loyalty points khi session COMPLETED
- Apply membership discount nếu customer là member

### 8.4 Với Club Service
- Lấy staff_id, club_id (who opened session)
- Lấy club configuration (timezone, currency, pricing rules)

### 8.5 Với Billing Service
- Gửi COMPLETED sessions → Billing tạo invoice
- Sync dữ liệu cho revenue report, tax calculation

### 8.6 Với Authorization Service
- Check quyền: chỉ STAFF+ mới được tạo session
- Check quyền: chỉ MANAGER+ mới được pause/resume/cancel session

---

## 9. Quy Tắc Nghiệp Vụ

### 9.1 Session Rules
- Mỗi session phải có table_id, club_id, staff_id
- Session status flow: ACTIVE → (PAUSED →) COMPLETED (hoặc CANCELLED)
- Chỉ có 1 ACTIVE session per table (exclusive use)
- Khi tạo session → tự động tạo draft order
- Không thể tạo session nếu table là UNAVAILABLE (maintenance)

### 9.2 Pricing Rules
- Giá cơ sở = table_id.price_per_hour (từ Resource Service)
- Duration = (end_time - start_time) - total_pause_duration
- calculated_price = (duration in hours) × base_price
- Nếu duration > 1 hour → có thể có surcharge rules (per club config)
- final_price = calculated_price + sum(extras) - sum(discounts)
- Không thể thay đổi giá sau khi session COMPLETED

### 9.3 Participant Rules
- Ít nhất 1 PRIMARY participant per session
- Có thể có multiple SECONDARY và SPECTATOR
- payment_share của mỗi participant phải > 0
- Tổng payment_share có thể = 100% hoặc chia lẻ (split payment logic xử lý ở Order Service)

### 9.4 Pause/Resume Rules
- Chỉ STAFF+ mới được pause/resume session
- Pause chỉ có hiệu lực nếu session status = ACTIVE
- Resume chỉ có hiệu lực nếu session status = PAUSED
- Mỗi pause → tạo entry trong session_pause_history
- total_pause_duration = sum(pause_end - pause_start)

### 9.5 Status History Rules
- Mỗi status change phải record lại (audit trail)
- Không thể thay đổi từ COMPLETED/CANCELLED sang trạng thái khác

---

## 10. Sample Seed Data

```sql
INSERT INTO sessions (id, club_id, table_id, staff_id, order_id, status, start_time, end_time, total_pause_duration, calculated_price, final_price) VALUES
(1, 1, 1, 1, 1, 'COMPLETED', '2026-08-12 10:00:00', '2026-08-12 12:30:00', 0, 125000, 125000),
(2, 1, 2, 1, 2, 'COMPLETED', '2026-08-12 11:00:00', '2026-08-12 13:00:00', 600, 100000, 100000),
(3, 1, 3, 1, NULL, 'ACTIVE', '2026-08-12 14:00:00', NULL, 0, 0, NULL);

INSERT INTO session_participants (id, session_id, customer_id, participant_role, payment_share) VALUES
(1, 1, 1, 'PRIMARY', 100),
(2, 2, 2, 'PRIMARY', 50),
(3, 2, 3, 'SECONDARY', 50),
(4, 3, 1, 'PRIMARY', 100);

INSERT INTO session_pricing_history (id, session_id, price_type, amount, description, calculated_by) VALUES
(1, 1, 'BASE', 125000, '2.5 hours × 50000/hour', 1),
(2, 2, 'BASE', 100000, '2 hours × 50000/hour', 1),
(3, 3, 'BASE', 50000, '1 hour × 50000/hour (estimated)', 1);

INSERT INTO session_pause_history (id, session_id, pause_start, pause_end, pause_duration, reason, paused_by, resumed_by) VALUES
(1, 2, '2026-08-12 12:00:00', '2026-08-12 12:10:00', 600, 'Customer break', 1, 1);

INSERT INTO session_status_history (id, session_id, from_status, to_status, changed_by, reason) VALUES
(1, 1, NULL, 'ACTIVE', 1, 'Session created - table opened'),
(2, 1, 'ACTIVE', 'COMPLETED', 1, 'Session ended - customer paid'),
(3, 2, NULL, 'ACTIVE', 1, 'Session created - table opened'),
(4, 2, 'ACTIVE', 'PAUSED', 1, 'Customer took break'),
(5, 2, 'PAUSED', 'ACTIVE', 1, 'Session resumed'),
(6, 2, 'ACTIVE', 'COMPLETED', 1, 'Session ended - customer paid'),
(7, 3, NULL, 'ACTIVE', 1, 'Session created - table opened');

INSERT INTO session_notes (id, session_id, note_text, noted_by) VALUES
(1, 2, 'Customer asked for cue extension', 1),
(2, 3, 'VIP customer - check loyalty status', 1);
```

---

## 11. Session Lifecycle Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  1. CREATE SESSION (Staff mở bàn)                                  │
│     ├─ POST /api/sessions                                          │
│     ├─ Insert into sessions (status = ACTIVE)                      │
│     ├─ Call Order Service → tạo draft order (TABLE item)           │
│     ├─ Call Resource Service → update table status → IN_USE        │
│     └─ Session created ✓                                           │
│                                                                     │
│  2. ADD PARTICIPANTS (Thêm người chơi)                             │
│     ├─ POST /api/sessions/{id}/participants                        │
│     ├─ Insert into session_participants                            │
│     └─ Participants added ✓                                        │
│                                                                     │
│  3. PAUSE/RESUME (Tạm dừng/tiếp tục)                              │
│     ├─ POST /api/sessions/{id}/pause                               │
│     ├─ Update sessions (status = PAUSED, pause_start_time = now)  │
│     ├─ Insert into session_pause_history (pause_start)             │
│     ├─ POST /api/sessions/{id}/resume                              │
│     ├─ Update sessions (status = ACTIVE)                           │
│     ├─ Update session_pause_history (pause_end, pause_duration)   │
│     ├─ Update sessions (total_pause_duration += pause_duration)    │
│     └─ Pause/resume tracked ✓                                      │
│                                                                     │
│  4. COMPLETE SESSION (Kết thúc chơi)                               │
│     ├─ POST /api/sessions/{id}/complete                            │
│     ├─ Calculate final_price:                                      │
│     │  ├─ duration = (end_time - start_time) - total_pause_duration│
│     │  ├─ calculated_price = (duration/60) × base_price            │
│     │  ├─ Fetch extras/discounts từ session_pricing_history        │
│     │  ├─ final_price = calculated + extras - discounts            │
│     │  └─ Update sessions (status = COMPLETED, end_time, final_price)
│     ├─ Update Order Service:                                       │
│     │  ├─ Update order.total_amount = session.final_price          │
│     │  ├─ Update order.status = PROCESSING                         │
│     │  └─ Order ready for payment                                  │
│     ├─ Call Resource Service → update table status → AVAILABLE     │
│     ├─ Insert into session_status_history                          │
│     └─ Session completed ✓                                         │
│                                                                     │
│  5. CANCEL SESSION (Hủy session)                                   │
│     ├─ POST /api/sessions/{id}/cancel                              │
│     ├─ Update sessions (status = CANCELLED)                        │
│     ├─ Call Order Service → cancel order                           │
│     ├─ Call Resource Service → update table status → AVAILABLE     │
│     ├─ Insert into session_status_history                          │
│     └─ Session cancelled ✓                                         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 12. Kết Luận

Session Service được thiết kế theo đúng chuẩn hóa cơ sở dữ liệu 1NF, 2NF, 3NF:
- **1NF**: Tất cả cột đều chứa giá trị nguyên tố
- **2NF**: Không có partial dependency (tách bảng chi tiết participants, pricing, pause history)
- **3NF**: Không có transitive dependency (tách bảng sparse data)

**Thiết kế linh hoạt**:
- ✓ Hỗ trợ multiple participants per session (split payment)
- ✓ Hỗ trợ pause/resume tracking
- ✓ Hỗ trợ flexible pricing (base + extras + discounts)
- ✓ Hỗ trợ audit trail (status history, pause history)
- ✓ Tách biệt history data (sparse) từ transaction data (sessions)

Điều này giúp:
- ✓ Giảm redundancy
- ✓ Dễ bảo trì và mở rộng
- ✓ Tốc độ query nhanh (proper indexes)
- ✓ Tính toàn vẹn dữ liệu cao
- ✓ Support complex business logic (pause/resume, pricing calculation, split payments)
- ✓ Tách biệt trách nhiệm giữa các service (microservices architecture)
- ✓ Real-time session tracking capability
