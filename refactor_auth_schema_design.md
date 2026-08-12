# Kế hoạch Tái cấu trúc CSDL Auth (Auth DB Refactor Plan)

Tài liệu này mô tả chi tiết kiến trúc của cơ sở dữ liệu `auth.db` (database-per-service SQLite), tập trung vào thiết kế Many-to-Many (M-N) cho hệ thống đa chi nhánh và tích hợp các lớp bảo mật. Tài liệu dành cho team kỹ thuật tham khảo và điều chỉnh.

## 1. Mục tiêu Tái cấu trúc (Refactoring Goals)

1.  **Phục hồi cấu trúc Many-to-Many:** Tách `store_id` và `role` ra khỏi bảng `users`, trả về bảng trung gian `user_store_roles` để cho phép 1 nhân sự làm việc tại nhiều chi nhánh với các role khác nhau.
2.  **Tích hợp Cơ chế Bảo mật (Security Context):**
    *   **Brute-force protection:** Đếm số lần đăng nhập sai và khoá tài khoản (cột `failed_login_attempts`, `locked_until` trong `users`).
    *   **Audit Logging:** Truy vết hành động nhạy cảm của người dùng (bảng `audit_logs`).
    *   **Token Management:** Quản lý vòng đời Refresh Token và Token Đổi mật khẩu (bảng `refresh_tokens`, `password_reset_tokens`).
    *   **Staff Onboarding:** Quản lý quy trình mời nhân viên vào chi nhánh (bảng `staff_invitations`).

## 2. Sơ đồ Cơ sở dữ liệu (ER Diagram)

```mermaid
erDiagram
    USERS {
        INTEGER id PK "AUTOINCREMENT"
        VARCHAR username "UNIQUE"
        VARCHAR password_hash 
        INTEGER failed_login_attempts "Đếm số lần đăng nhập sai"
        DATETIME locked_until "Thời gian mở khoá"
        DATETIME last_login_at 
        DATETIME created_at 
        DATETIME updated_at 
    }

    STORES {
        INTEGER id PK "AUTOINCREMENT"
        VARCHAR name 
        INTEGER owner_id FK "REFERENCES users(id)"
        DATETIME created_at 
        DATETIME updated_at 
    }

    USER_STORE_ROLES {
        INTEGER id PK "AUTOINCREMENT"
        INTEGER user_id FK "REFERENCES users(id)"
        INTEGER store_id FK "REFERENCES stores(id)"
        VARCHAR role "SUPER_ADMIN, OWNER, STORE_MANAGER, CASHIER"
        DATETIME created_at 
    }

    REFRESH_TOKENS {
        INTEGER id PK "AUTOINCREMENT"
        INTEGER user_id FK "REFERENCES users(id)"
        VARCHAR token "UNIQUE"
        DATETIME expires_at 
        DATETIME revoked_at "Nullable"
        DATETIME created_at 
    }

    PASSWORD_RESET_TOKENS {
        INTEGER id PK "AUTOINCREMENT"
        INTEGER user_id FK "REFERENCES users(id)"
        VARCHAR token "UNIQUE"
        DATETIME expires_at 
        DATETIME used_at "Nullable"
        DATETIME created_at 
    }

    AUDIT_LOGS {
        INTEGER id PK "AUTOINCREMENT"
        INTEGER user_id "FK (Nullable) - Người thực hiện"
        INTEGER store_id "FK (Nullable) - Chi nhánh (nếu có)"
        VARCHAR action "e.g., ACCOUNT_LOCKED, TOKENS_REVOKED"
        VARCHAR target_type "e.g., USER, USER_STORE_ROLE"
        INTEGER target_id "ID của đối tượng bị tác động"
        VARCHAR ip_address 
        DATETIME created_at 
    }

    STAFF_INVITATIONS {
        INTEGER id PK "AUTOINCREMENT"
        INTEGER store_id FK "REFERENCES stores(id)"
        INTEGER inviter_id FK "REFERENCES users(id)"
        VARCHAR phone_number 
        VARCHAR role "Quyền sẽ được cấp"
        VARCHAR token "Mã xác nhận UNIQUE"
        DATETIME expires_at 
        DATETIME accepted_at "Nullable"
        DATETIME created_at 
    }

    %% Relationships
    USERS ||--o{ USER_STORE_ROLES : "has roles (M-N)"
    STORES ||--o{ USER_STORE_ROLES : "managed by"
    USERS ||--o{ STORES : "owns (1-N)"
    USERS ||--o{ REFRESH_TOKENS : "has sessions"
    USERS ||--o{ PASSWORD_RESET_TOKENS : "requests reset"
    USERS ||--o{ AUDIT_LOGS : "performs action"
    USERS ||--o{ STAFF_INVITATIONS : "invites"
    STORES ||--o{ STAFF_INVITATIONS : "receives staff"
```

## 3. Checklist & Lưu ý Kỹ thuật (Technical Constraints)

1.  **Ràng buộc Dữ liệu (Constraints):**
    *   **`user_store_roles`:** Bắt buộc áp dụng `UniqueConstraint('user_id', 'store_id')` trong SQLAlchemy để chống trùng lặp quyền tại một chi nhánh.
2.  **Chỉ mục (Indexes):**
    *   **`audit_logs`:** Bổ sung Composite Index trên `(target_type, target_id)` hoặc Index trên `user_id` để tối ưu truy vấn khi cần filter lịch sử.
3.  **Migration (SQLite & Alembic):**
    *   Sử dụng Batch Operations (`with op.batch_alter_table(...)`) vì SQLite không hỗ trợ DROP/ALTER COLUMN trực tiếp.
    *   Đảm bảo Script down-migration xử lý rollback dữ liệu đầy đủ.
