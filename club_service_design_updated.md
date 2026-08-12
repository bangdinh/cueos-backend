# Club Service Design (Updated)
## Thiết kế Database chuẩn hóa (1NF, 2NF, 3NF)
## Authorization Service tách riêng

---

## 1. Mục đích
Club Service là service quản lý các chi nhánh/chuỗi club bida, bao gồm:
- thông tin chi nhánh (club/branch)
- thông tin nhân viên
- cấu hình chi nhánh
- gán roles từ Authorization Service cho nhân viên

**Lưu ý**: Roles và Permissions được quản lý tập trung bởi **Authorization Service** (riêng biệt).

Service này cung cấp dữ liệu nền tảng cho các service khác.

---

## 2. Vai trò của Club Service
- lưu trữ thông tin chi nhánh/club
- quản lý nhân viên
- gán roles cho nhân viên (role được lấy từ Authorization Service)
- cung cấp club_id cho các service khác
- quản lý user accounts cho nhân viên

---

## 3. Bounded Context

### 3.1 Club Management
Quản lý thông tin chi nhánh/chuỗi club:
- tên club
- địa chỉ
- thông tin liên lạc
- trạng thái hoạt động

### 3.2 Staff Management
Quản lý nhân viên:
- thông tin cá nhân
- vị trí công việc
- mapping nhân viên ↔ club
- thông tin liên hệ

### 3.3 User Account Management
Quản lý tài khoản đăng nhập:
- username/password
- mapping user ↔ staff
- status đăng nhập

### 3.4 Staff Role Assignment
Gán roles từ Authorization Service cho nhân viên:
- mapping nhân viên ↔ role
- role lấy từ Authorization Service (external reference)

### 3.5 Club Configuration
Cấu hình riêng cho từng club:
- giờ làm việc
- chính sách
- thiết lập vận hành

---

## 4. Thiết kế Database chuẩn hóa (1NF, 2NF, 3NF)

```sql
-- 1. Bảng clubs (1NF, 2NF, 3NF)
CREATE TABLE clubs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    address TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE', 'SUSPENDED')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- Phân tích: 1NF ✓ (mỗi cột là atomic)
--           2NF ✓ (tất cả thuộc tính phụ thuộc vào khóa chính ID)
--           3NF ✓ (không có phụ thuộc bắc cầu)

-- 2. Bảng staffs (1NF, 2NF, 3NF)
CREATE TABLE staffs (
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
-- Phân tích: 1NF ✓ 2NF ✓ 3NF ✓

-- 3. Bảng staff_roles (1NF, 2NF, 3NF)
-- Mapping staff ↔ role (role được quản lý bởi Authorization Service)
CREATE TABLE staff_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    staff_id INTEGER NOT NULL REFERENCES staffs(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL,
    assigned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (staff_id, role_id)
);
-- Phân tích: 1NF ✓ 2NF ✓ 3NF ✓
-- Lưu ý: role_id là reference đến Authorization Service (không phải local table)
-- Điều này không vi phạm 3NF vì Authorization Service là một service khác

-- 4. Bảng user_accounts (1NF, 2NF, 3NF)
CREATE TABLE user_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    staff_id INTEGER NOT NULL UNIQUE REFERENCES staffs(id) ON DELETE CASCADE,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    is_active TEXT NOT NULL DEFAULT 'true',
    last_login TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- Phân tích: 1NF ✓ (atomic values)
--           2NF ✓ (phụ thuộc vào khóa chính ID)
--           3NF ✓ (không có phụ thuộc bắc cầu)

-- 5. Bảng club_configurations (1NF, 2NF, 3NF)
CREATE TABLE club_configurations (
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
-- Phân tích: 1NF ✓ 2NF ✓ 3NF ✓
-- Tách riêng bảng config vì không phải mỗi club đều có config (sparse data)

-- 6. Bảng club_settings (key-value) (1NF, 2NF, 3NF)
CREATE TABLE club_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    club_id INTEGER NOT NULL REFERENCES clubs(id) ON DELETE CASCADE,
    setting_key TEXT NOT NULL,
    setting_value TEXT,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (club_id, setting_key)
);
-- Phân tích: 1NF ✓ 2NF ✓ 3NF ✓

-- Indexes để tối ưu performance
CREATE INDEX idx_staffs_club_id ON staffs(club_id);
CREATE INDEX idx_staff_roles_staff_id ON staff_roles(staff_id);
CREATE INDEX idx_user_accounts_staff_id ON user_accounts(staff_id);
CREATE INDEX idx_club_configurations_club_id ON club_configurations(club_id);
CREATE INDEX idx_club_settings_club_id ON club_settings(club_id);
```

---

## 5. Entity-Relationship Diagram (ERD)

```
┌─────────────┐
│   clubs     │
├─────────────┤
│ id (PK)     │
│ name        │
│ address     │
│ phone       │
│ email       │
│ status      │
│ created_at  │
└─────────────┘
      │
      │ 1:N
      ├──────────────────────────┐
      │                          │
      ▼                          ▼
┌──────────────┐        ┌────────────────────┐
│   staffs     │        │ club_configurations│
├──────────────┤        ├────────────────────┤
│ id (PK)      │        │ id (PK)            │
│ club_id (FK) │        │ club_id (FK)       │
│ full_name    │        │ working_hours_*    │
│ phone        │        │ timezone           │
│ email        │        │ currency           │
│ position     │        │ max_tables         │
│ status       │        └────────────────────┘
│ created_at   │
└──────────────┘
      │
      │ 1:N
      ▼
┌──────────────────┐
│  staff_roles     │
├──────────────────┤
│ id (PK)          │
│ staff_id (FK)    │
│ role_id          │ ──┐ (reference to Authorization Service)
│ assigned_at      │   │
└──────────────────┘   │
                       │
          ┌────────────┘
          │ (external reference)
          ▼
    ┌──────────────────┐
    │ Authorization    │
    │ Service          │
    │ - roles          │
    │ - permissions    │
    │ - role_perms     │
    └──────────────────┘

┌──────────────────────┐
│  user_accounts       │
├──────────────────────┤
│ id (PK)              │
│ staff_id (FK UNIQUE) │
│ username (UNIQUE)    │
│ password_hash        │
│ is_active            │
│ last_login           │
│ created_at           │
└──────────────────────┘

┌──────────────────────┐
│  club_settings       │
├──────────────────────┤
│ id (PK)              │
│ club_id (FK)         │
│ setting_key          │
│ setting_value        │
│ description          │
└──────────────────────┘
```

---

## 6. Quy tắc Chuẩn Hóa

### 6.1 1NF (First Normal Form)
✓ **Áp dụng**: Mỗi cột chỉ chứa giá trị nguyên tố
- Ví dụ: `staffs.phone` là một giá trị text, không phải tập hợp
- `staffs.email` là một giá trị, không phải danh sách email

### 6.2 2NF (Second Normal Form)
✓ **Áp dụng**: Thỏa 1NF + tất cả non-key attributes phụ thuộc toàn phần vào khóa chính
- Ví dụ: `staff_roles` là bảng riêng (không để roles trong staffs)
  - Vì một nhân viên có thể có nhiều roles
  - Role được quản lý bởi Authorization Service (không local)

### 6.3 3NF (Third Normal Form)
✓ **Áp dụng**: Thỏa 2NF + không có phụ thuộc bắc cầu
- Ví dụ: `user_accounts` tách riêng
  - Vì password chỉ phụ thuộc vào user_id
  - Không có phụ thuộc bắc cầu với staff_id
- Ví dụ: `club_configurations` tách riêng từ clubs
  - Vì configurations là optional (sparse data)

---

## 7. API Đề Xuất

### 7.1 Club APIs
- `GET /api/clubs` - danh sách tất cả clubs
- `GET /api/clubs/{id}` - chi tiết một club
- `POST /api/clubs` - tạo club mới
- `PUT /api/clubs/{id}` - cập nhật club
- `DELETE /api/clubs/{id}` - xóa club

### 7.2 Staff APIs
- `GET /api/clubs/{club_id}/staffs` - danh sách nhân viên
- `POST /api/clubs/{club_id}/staffs` - thêm nhân viên
- `PUT /api/staffs/{id}` - cập nhật thông tin nhân viên
- `DELETE /api/staffs/{id}` - xóa nhân viên

### 7.3 Staff Role APIs
- `GET /api/staffs/{staff_id}/roles` - danh sách roles của nhân viên
- `POST /api/staffs/{staff_id}/roles/{role_id}` - gán role cho nhân viên
- `DELETE /api/staffs/{staff_id}/roles/{role_id}` - xóa role khỏi nhân viên

### 7.4 User Account APIs
- `POST /api/user-accounts` - tạo tài khoản
- `PUT /api/user-accounts/{id}` - cập nhật tài khoản
- `DELETE /api/user-accounts/{id}` - xóa tài khoản

### 7.5 Configuration APIs
- `GET /api/clubs/{club_id}/configuration` - lấy cấu hình
- `PUT /api/clubs/{club_id}/configuration` - cập nhật cấu hình
- `GET /api/clubs/{club_id}/settings` - lấy settings
- `PUT /api/clubs/{club_id}/settings/{key}` - cập nhật setting

---

## 8. Mối Quan Hệ Với Các Service Khác

### 8.1 Với Auth Service
- Auth Service gọi Club Service để lấy thông tin staff + club_id
- Auth Service gọi Authorization Service để lấy roles + permissions

### 8.2 Với Authorization Service
- Club Service gọi Authorization Service để lấy danh sách roles
- Gán role cho nhân viên thông qua staff_roles
- Authorization Service lưu role_id, Club Service chỉ lưu mapping

### 8.3 Với Resource Service
- Resource Service sử dụng club_id từ token/header
- Lấy danh sách bàn, sản phẩm theo club

### 8.4 Với Customer Service
- Customer Service sử dụng club_id
- Có thể sử dụng cấu hình của club

### 8.5 Với Session Service
- Session Service sử dụng club_id từ token
- Tìm bàn và session của club tương ứng

---

## 9. Quy Tắc Nghiệp Vụ

### 9.1 Club Rules
- Tên club phải là duy nhất trong hệ thống
- Chỉ có một configuration cho mỗi club

### 9.2 Staff Rules
- Mỗi nhân viên phải thuộc về một club
- Một nhân viên có thể có nhiều roles
- Không thể xóa nhân viên nếu còn có user account hoạt động

### 9.3 Staff Role Rules
- Mỗi nhân viên có thể có nhiều roles
- Role được quản lý bởi Authorization Service
- Role_id phải tồn tại trong Authorization Service

### 9.4 User Account Rules
- Username phải là duy nhất
- Mỗi nhân viên chỉ có một user account
- Mật khẩu phải được hash trước khi lưu

---

## 10. Sample Seed Data

```sql
INSERT INTO clubs (id, name, address, phone, email, status) VALUES
(1, 'Club Bida Sài Gòn', '123 Nguyễn Văn Cừ, Quận 5', '0283456789', 'sg@club.com', 'ACTIVE'),
(2, 'Club Bida Hà Nội', '456 Bà Triệu, Hoàn Kiếm', '0243456789', 'hn@club.com', 'ACTIVE');

INSERT INTO staffs (id, club_id, full_name, phone, email, position, status) VALUES
(1, 1, 'Nguyễn Văn A', '0901234567', 'a@club.com', 'Quản lý', 'ACTIVE'),
(2, 1, 'Trần Thị B', '0902345678', 'b@club.com', 'Thu ngân', 'ACTIVE');

-- role_id tham chiếu đến Authorization Service (không phải local ID)
INSERT INTO staff_roles (id, staff_id, role_id, assigned_at) VALUES
(1, 1, 2, CURRENT_TIMESTAMP),  -- role 2 = CLUB_MANAGER (từ Authorization Service)
(2, 2, 5, CURRENT_TIMESTAMP);  -- role 5 = STAFF (từ Authorization Service)

INSERT INTO user_accounts (id, staff_id, username, password_hash, is_active) VALUES
(1, 1, 'manager_a', 'hashed_password_1', 'true'),
(2, 2, 'staff_b', 'hashed_password_2', 'true');

INSERT INTO club_configurations (id, club_id, working_hours_start, working_hours_end, timezone, currency, max_tables) VALUES
(1, 1, '08:00', '23:00', 'Asia/Ho_Chi_Minh', 'VND', 15),
(2, 2, '09:00', '24:00', 'Asia/Ho_Chi_Minh', 'VND', 20);

INSERT INTO club_settings (id, club_id, setting_key, setting_value, description) VALUES
(1, 1, 'table_price_default', '50000', 'Giá mặc định cho bàn thường'),
(2, 1, 'vip_table_price_default', '80000', 'Giá mặc định cho bàn VIP');
```

---

## 11. Kết Luận

Club Service được thiết kế theo đúng chuẩn hóa cơ sở dữ liệu 1NF, 2NF, 3NF:
- **1NF**: Tất cả cột đều chứa giá trị nguyên tố
- **2NF**: Không có partial dependency (tách bảng many-to-many)
- **3NF**: Không có transitive dependency (tách bảng sparse data)

**Tách biệt rõ ràng**:
- Role/Permission được quản lý tập trung bởi **Authorization Service**
- Club Service chỉ quản lý: clubs, staffs, user accounts, staff-role mapping
- staff_roles table chỉ lưu mapping giữa staff và role_id (từ Authorization Service)

Điều này giúp:
- ✓ Giảm redundancy
- ✓ Dễ bảo trì và mở rộng
- ✓ Tốc độ query nhanh
- ✓ Tính toàn vẹn dữ liệu cao
- ✓ Tách biệt trách nhiệm giữa các service (microservices architecture)
