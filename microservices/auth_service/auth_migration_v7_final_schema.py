import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "auth.db")

def upgrade():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Checking for old roles in user_store_roles and staff_invitations...")
    cursor.execute("SELECT DISTINCT role FROM user_store_roles")
    old_roles_usr = [r[0] for r in cursor.fetchall() if r[0] not in ('SUPER_ADMIN', 'OWNER', 'MANAGER', 'STAFF')]
    
    cursor.execute("SELECT DISTINCT role FROM staff_invitations")
    old_roles_si = [r[0] for r in cursor.fetchall() if r[0] not in ('SUPER_ADMIN', 'OWNER', 'MANAGER', 'STAFF')]
    
    if old_roles_usr or old_roles_si:
        print(f"FOUND OLD ROLES! user_store_roles: {old_roles_usr}, staff_invitations: {old_roles_si}")
        conn.close()
        return False
        
    print("No old roles found. Proceeding with migration...")
    
    # 1. Add Unique Index for staff_invitations(token)
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_staff_invitations_token ON staff_invitations(token);")
    
    # 2. Add Composite Index for audit_logs(target_type, target_id)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_target ON audit_logs(target_type, target_id);")
    
    # 3. Add CHECK constraints to user_store_roles and staff_invitations
    # SQLite requires table recreation to add CHECK constraints
    
    print("Recreating user_store_roles to add CHECK constraint...")
    cursor.execute("CREATE TABLE user_store_roles_new ("
                   "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                   "user_id INTEGER NOT NULL REFERENCES users(id), "
                   "store_id INTEGER NOT NULL REFERENCES stores(id), "
                   "role VARCHAR(50) NOT NULL CHECK (role IN ('OWNER', 'MANAGER', 'STAFF')), "
                   "created_at DATETIME DEFAULT CURRENT_TIMESTAMP, "
                   "updated_at DATETIME DEFAULT CURRENT_TIMESTAMP)")
    cursor.execute("INSERT INTO user_store_roles_new SELECT * FROM user_store_roles")
    cursor.execute("DROP TABLE user_store_roles")
    cursor.execute("ALTER TABLE user_store_roles_new RENAME TO user_store_roles")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_user_store ON user_store_roles(user_id, store_id)")
    
    print("Recreating staff_invitations to add CHECK constraint...")
    cursor.execute("CREATE TABLE staff_invitations_new ("
                   "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                   "store_id INTEGER NOT NULL REFERENCES stores(id), "
                   "phone VARCHAR(20) NOT NULL, "
                   "role VARCHAR(50) NOT NULL CHECK (role IN ('OWNER', 'MANAGER', 'STAFF')), "
                   "token VARCHAR(255) NOT NULL, "
                   "invited_by INTEGER NOT NULL REFERENCES users(id), "
                   "expires_at DATETIME NOT NULL, "
                   "accepted_at DATETIME, "
                   "created_at DATETIME DEFAULT CURRENT_TIMESTAMP)")
    cursor.execute("INSERT INTO staff_invitations_new SELECT * FROM staff_invitations")
    cursor.execute("DROP TABLE staff_invitations")
    cursor.execute("ALTER TABLE staff_invitations_new RENAME TO staff_invitations")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_staff_invitations_token ON staff_invitations(token)")
    
    conn.commit()
    conn.close()
    print("Migration successful.")
    return True

if __name__ == "__main__":
    upgrade()
