# Roles Service Design
## Quản lý Roles, Permissions và Access Control

---

## 1. Mục đích
Roles Service là service tập trung quản lý:
- định nghĩa role (vai trò)
- định nghĩa permission (quyền hạn)
- gán permission cho role
- cung cấp authorization data cho các service khác

Service này là "master data" cho quyền hạn của toàn hệ thống.

---

## 2. Vai trò của Roles Service
- lưu trữ tất cả roles được định nghĩa trong hệ thống
- lưu trữ tất cả permissions (tài nguyên và hành động)
- quản lý mối quan hệ role-permission
- cung cấp API để check quyền hạn
- hỗ trợ cache/Redis cho performance

---

## 3. Bounded Context

### 3.1 Role Management
- tên role (ADMIN, MANAGER, STAFF, v.v.)
- mô tả role
- trạng thái

### 3.2 Permission Management
- tên permission
- resource (sản phẩm, bàn, báo cáo, v.v.)
- action (create, read, update, delete, v.v.)
- mô tả chi tiết

### 3.3 Role-Permission Assignment
- gán permission cho role
- một role có nhiều permission
- một permission có thể thuộc về nhiều role

### 3.4 Permission Validation
- API để check "user này có quyền làm việc X không?"
- cache kết quả để tối ưu

---

## 4. Thiết kế Database chuẩn hóa (1NF, 2NF, 3NF)

```sql
-- 1. Bảng roles (1NF, 2NF, 3NF)
CREATE TABLE roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- Phân tích: 1NF ✓ 2NF ✓ 3NF ✓
-- Mỗi role tự độc lập, không có dependency bắc cầu

-- 2. Bảng permissions (1NF, 2NF, 3NF)
CREATE TABLE permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    resource TEXT NOT NULL,
    action TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (resource, action)
);
-- Phân tích: 1NF ✓ 2NF ✓ 3NF ✓
-- resource + action là duy nhất, không trùng

-- 3. Bảng role_permissions (1NF, 2NF, 3NF - Junction Table)
CREATE TABLE role_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    assigned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (role_id, permission_id)
);
-- Phân tích: 1NF ✓ 2NF ✓ 3NF ✓
-- Tách bảng many-to-many để tránh redundancy

-- 4. Bảng permission_hierarchy (tùy chọn - cho phép phân cấp permission)
-- Ví dụ: admin có thể có parent permission, staff không có
CREATE TABLE permission_hierarchy (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
    child_permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    UNIQUE (parent_permission_id, child_permission_id)
);
-- Phân tích: 1NF ✓ 2NF ✓ 3NF ✓

-- Indexes
CREATE INDEX idx_roles_status ON roles(status);
CREATE INDEX idx_permissions_resource ON permissions(resource);
CREATE INDEX idx_permissions_action ON permissions(action);
CREATE INDEX idx_role_permissions_role_id ON role_permissions(role_id);
CREATE INDEX idx_role_permissions_permission_id ON role_permissions(permission_id);
```

---

## 5. Entity-Relationship Diagram

```
┌──────────────┐
│   roles      │
├──────────────┤
│ id (PK)      │
│ name         │
│ description  │
│ status       │
│ created_at   │
└──────────────┘
      │
      │ 1:N
      │
┌────────────────────┐
│  role_permissions  │
├────────────────────┤
│ id (PK)            │
│ role_id (FK)       │
│ permission_id (FK) │
│ assigned_at        │
└────────────────────┘
      │
      │ N:1
      ▼
┌──────────────────┐
│  permissions     │
├──────────────────┤
│ id (PK)          │
│ name             │
│ resource         │
│ action           │
│ description      │
│ status           │
│ created_at       │
└──────────────────┘
      │
      │ 0:N (optional hierarchy)
      │
┌──────────────────────┐
│ permission_hierarchy │
├──────────────────────┤
│ id (PK)              │
│ parent_permission_id │
│ child_permission_id  │
└──────────────────────┘
```

---

## 6. Quy tắc Chuẩn Hóa

### 6.1 1NF (First Normal Form)
✓ Mỗi cột chỉ chứa giá trị nguyên tố
- `roles.name` là text đơn
- `permissions.resource` là text đơn (không phải array)

### 6.2 2NF (Second Normal Form)
✓ Thỏa 1NF + tất cả non-key attributes phụ thuộc toàn phần vào khóa chính
- Dùng junction table `role_permissions` để tránh partial dependency
- Không để permission trong roles table

### 6.3 3NF (Third Normal Form)
✓ Thỏa 2NF + không có phụ thuộc bắc cầu
- Không có attribute phụ thuộc vào attribute không phải khóa chính
- Mỗi bảng có trách nhiệm rõ ràng

---

## 7. Dữ liệu mẫu

```sql
INSERT INTO roles (id, name, description, status) VALUES
(1, 'SUPER_ADMIN', 'Quản trị viên toàn hệ thống', 'ACTIVE'),
(2, 'HQ_MANAGER', 'Quản lý tập đoàn HQ', 'ACTIVE'),
(3, 'CLUB_ADMIN', 'Quản trị viên club', 'ACTIVE'),
(4, 'CLUB_MANAGER', 'Quản lý club', 'ACTIVE'),
(5, 'STAFF', 'Nhân viên', 'ACTIVE');

-- Products permissions
INSERT INTO permissions (id, name, resource, action, description, status) VALUES
(1, 'CREATE_PRODUCT', 'product', 'create', 'Tạo sản phẩm mới', 'ACTIVE'),
(2, 'READ_PRODUCT', 'product', 'read', 'Xem sản phẩm', 'ACTIVE'),
(3, 'UPDATE_PRODUCT', 'product', 'update', 'Cập nhật sản phẩm', 'ACTIVE'),
(4, 'DELETE_PRODUCT', 'product', 'delete', 'Xóa sản phẩm', 'ACTIVE');

-- Tables permissions
INSERT INTO permissions (id, name, resource, action, description, status) VALUES
(5, 'CREATE_TABLE', 'table', 'create', 'Tạo bàn mới', 'ACTIVE'),
(6, 'READ_TABLE', 'table', 'read', 'Xem bàn', 'ACTIVE'),
(7, 'UPDATE_TABLE', 'table', 'update', 'Cập nhật bàn', 'ACTIVE'),
(8, 'DELETE_TABLE', 'table', 'delete', 'Xóa bàn', 'ACTIVE');

-- Reports permissions
INSERT INTO permissions (id, name, resource, action, description, status) VALUES
(9, 'VIEW_REPORT', 'report', 'read', 'Xem báo cáo', 'ACTIVE'),
(10, 'EXPORT_REPORT', 'report', 'export', 'Xuất báo cáo', 'ACTIVE');

-- Session permissions
INSERT INTO permissions (id, name, resource, action, description, status) VALUES
(11, 'START_SESSION', 'session', 'create', 'Bắt đầu phiên chơi', 'ACTIVE'),
(12, 'END_SESSION', 'session', 'update', 'Kết thúc phiên chơi', 'ACTIVE');

-- Assign permissions to SUPER_ADMIN (có tất cả)
INSERT INTO role_permissions (role_id, permission_id) VALUES
(1, 1), (1, 2), (1, 3), (1, 4),
(1, 5), (1, 6), (1, 7), (1, 8),
(1, 9), (1, 10), (1, 11), (1, 12);

-- Assign permissions to CLUB_ADMIN (có tất cả trong club mình)
INSERT INTO role_permissions (role_id, permission_id) VALUES
(3, 1), (3, 2), (3, 3), (3, 4),
(3, 5), (3, 6), (3, 7), (3, 8),
(3, 9), (3, 10);

-- Assign permissions to CLUB_MANAGER (xem và cập nhật)
INSERT INTO role_permissions (role_id, permission_id) VALUES
(4, 2), (4, 3), (4, 6), (4, 7),
(4, 9), (4, 11), (4, 12);

-- Assign permissions to STAFF (chỉ xem)
INSERT INTO role_permissions (role_id, permission_id) VALUES
(5, 2), (5, 6), (5, 9), (5, 11);
```

---

## 8. API Đề Xuất

### 8.1 Role APIs
- `GET /api/auth/roles` - danh sách tất cả roles
- `GET /api/auth/roles/{id}` - chi tiết role
- `POST /api/auth/roles` - tạo role mới
- `PUT /api/auth/roles/{id}` - cập nhật role
- `DELETE /api/auth/roles/{id}` - xóa role

### 8.2 Permission APIs
- `GET /api/auth/permissions` - danh sách tất cả permissions
- `GET /api/auth/permissions?resource={resource}` - lấy permission theo resource
- `POST /api/auth/permissions` - tạo permission mới
- `PUT /api/auth/permissions/{id}` - cập nhật permission
- `DELETE /api/auth/permissions/{id}` - xóa permission

### 8.3 Role-Permission APIs
- `GET /api/auth/roles/{id}/permissions` - lấy permissions của role
- `POST /api/auth/roles/{id}/permissions/{permission_id}` - thêm permission cho role
- `DELETE /api/auth/roles/{id}/permissions/{permission_id}` - xóa permission khỏi role

### 8.4 Authorization Check APIs
- `POST /api/auth/check` - check "user có quyền làm action trên resource không?"
  - Request: `{ user_id, resource, action }`
  - Response: `{ allowed: true/false }`

---

## 9. Cách Hoạt Động Trong Hệ Thống

### Luồng xác thực và phân quyền
1. User đăng nhập → Auth Service
2. Auth Service gọi Club Service lấy staff info + role
3. Auth Service gọi Authorization Service lấy permissions của role
4. Auth Service tạo JWT token chứa user_id, role, club_id
5. Khi user thực hiện action → Gateway/Service kiểm tra token
6. Gateway có thể gọi Authorization Service để check quyền

### Caching Strategy
- Cache roles/permissions trong Redis
- TTL: 1 giờ
- Invalidate cache khi có update role/permission

---

## 10. Mối Quan Hệ Với Các Service Khác

### 10.1 Với Auth Service
- Auth Service gọi Authorization Service để check quyền
- Auth Service lưu roles/permissions trong token (cache)

### 10.2 Với Club Service
- Club Service gọi Authorization Service để lấy danh sách role
- Gán role cho nhân viên

### 10.3 Với Gateway
- Gateway có thể gọi Authorization Service để check quyền trước khi forward request

### 10.4 Với các service khác (Resource, Session, Order, Billing, Customer)
- Có thể gọi Authorization Service để check "user này có quyền không?"
- Hoặc dùng thông tin trong JWT token

---

## 11. Quy Tắc Nghiệp Vụ

### 11.1 Role Rules
- Tên role phải là duy nhất
- Không thể xóa role đang được sử dụng bởi nhân viên
- SUPER_ADMIN role không thể bị xóa

### 11.2 Permission Rules
- Tên permission phải là duy nhất
- Resource + Action phải là duy nhất
- Permission không thể được xóa nếu được gán cho role
- Phải có ít nhất 1 permission để khởi tạo role

### 11.3 Assignment Rules
- Một role có thể có nhiều permissions
- Không thể gán cùng permission hai lần cho một role
- Khi xóa role, tất cả role_permissions cũng bị xóa

---

## 12. Performance Considerations

### 12.1 Caching
```python
# Pseudo code
cache_key = f"role:{role_id}:permissions"
permissions = redis.get(cache_key)
if not permissions:
    permissions = db.query(role_permissions where role_id=role_id)
    redis.set(cache_key, json.dumps(permissions), ex=3600)
return permissions
```

### 12.2 Batch Permission Check
```
POST /api/auth/check-batch
Body: { user_id, checks: [{ resource, action }, ...] }
Response: { results: [{ resource, action, allowed }, ...] }
```

---

## 13. Kết Luận

Authorization Service là một service độc lập, chuyên quản lý roles và permissions:
- ✓ Tập trung hóa quản lý quyền
- ✓ Dễ mở rộng khi thêm role/permission mới
- ✓ Dễ cache và tối ưu performance
- ✓ Được dùng chung bởi nhiều service
- ✓ Chuẩn hóa 1NF, 2NF, 3NF

Kết hợp với Club Service, tạo thành một hệ thống xác thực và phân quyền hoàn chỉnh.
