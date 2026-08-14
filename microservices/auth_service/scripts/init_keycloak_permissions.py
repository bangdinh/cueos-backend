"""
Script khởi tạo toàn bộ Roles chuẩn và Permissions (Client Roles) trong Client 'bida-app' của Keycloak.
Chạy: python -m microservices.auth_service.scripts.init_keycloak_permissions
"""
import sys
import requests
from domain.store.permissions import StandardPermission, PERMISSION_DESCRIPTIONS
from microservices.auth_service.keycloak_admin import (
    get_client_uuid,
    get_client_roles,
    get_client_role,
    get_role_composites,
    create_client_role,
    add_composite_roles,
    get_keycloak_admin_token,
    KEYCLOAK_URL,
    KEYCLOAK_REALM,
)

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Bo 4 Role chuan cua he thong trong Client bida-app
STANDARD_CLIENT_ROLES = {
    "SUPER_ADMIN": "Quan tri vien cap cao nhat he thong (HQ)",
    "OWNER": "Chu chuoi / Chu chi nhanh quan bida",
    "MANAGER": "Quan ly chi nhanh quan bida",
    "STAFF": "Nhan vien van hanh chi nhanh"
}

# -------------------------------------------------------------------
# Bang phan quyen chuan — CHOT CUOI CUNG
# SUPER_ADMIN: chi quyen view, khong thao tac nghiep vu
# OWNER: toan bo 8 quyen
# MANAGER: 7 quyen — thieu manage_staff
# STAFF: 3 quyen van hanh tai ban
# -------------------------------------------------------------------
ROLE_PERMISSION_MATRIX = {
    "SUPER_ADMIN": [
        "perm:view_inventory",
        "perm:view_revenue",
        "perm:view_own_shift",
    ],
    "OWNER": [
        "perm:view_inventory",
        "perm:manage_inventory",
        "perm:view_revenue",
        "perm:approve_refund",
        "perm:manage_staff",
        "perm:checkout",
        "perm:manage_tables",
        "perm:view_own_shift",
    ],
    "MANAGER": [
        "perm:view_inventory",
        "perm:manage_inventory",
        "perm:view_revenue",
        "perm:approve_refund",
        "perm:checkout",
        "perm:manage_tables",
        "perm:view_own_shift",
    ],
    "STAFF": [
        "perm:checkout",
        "perm:manage_tables",
        "perm:view_own_shift",
    ],
}


def _remove_all_composites(client_uuid: str, role_name: str):
    """Xoa toan bo Composite Roles hien co cua role_name truoc khi sync lai."""
    token = get_keycloak_admin_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    current = get_role_composites(client_uuid, role_name)
    if not current:
        return

    url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/clients/{client_uuid}/roles/{role_name}/composites"
    resp = requests.delete(url, headers=headers, json=current, timeout=5)
    if resp.status_code not in (200, 204):
        raise RuntimeError(f"Loi xoa composites cua '{role_name}' ({resp.status_code}): {resp.text}")


def sync_composite_permissions(client_uuid: str):
    """
    Reset va dong bo Composite Permissions cho 4 Role chuan theo ROLE_PERMISSION_MATRIX.
    Moi lan chay se xoa composite cu va gan lai dung danh sach moi (idempotent).
    """
    print("\n" + "=" * 60)
    print("DONG BO COMPOSITE PERMISSIONS CHO 4 ROLE CHUAN")
    print("=" * 60)

    for role_name, perm_list in ROLE_PERMISSION_MATRIX.items():
        print(f"\n[{role_name}]")

        role_obj = get_client_role(client_uuid, role_name)
        if not role_obj:
            print(f"  WARN: Role '{role_name}' chua ton tai — bo qua (hay chay init_permissions() truoc)")
            continue

        # Buoc 1: Xoa composite cu
        try:
            _remove_all_composites(client_uuid, role_name)
            print(f"  OK: Da xoa composite cu")
        except Exception as e:
            print(f"  ERROR: Loi xoa composite cu: {e}")
            continue

        # Buoc 2: Lay representation cua tung permission
        perm_reps = []
        missing = []
        for perm_code in perm_list:
            rep = get_client_role(client_uuid, perm_code)
            if rep:
                perm_reps.append(rep)
            else:
                missing.append(perm_code)

        if missing:
            print(f"  WARN: Permission chua ton tai tren Keycloak, bo qua: {missing}")

        if not perm_reps:
            print(f"  WARN: Khong co permission nao de gan — bo qua role {role_name}")
            continue

        # Buoc 3: Gan composite moi
        try:
            add_composite_roles(client_uuid, role_name, perm_reps)
            names = [p["name"] for p in perm_reps]
            print(f"  OK: Gan {len(perm_reps)} permissions: {names}")
        except Exception as e:
            print(f"  ERROR: Loi gan composite: {e}")

    print("\n" + "=" * 60)
    print("HOAN TAT dong bo Composite Permissions!")
    print("=" * 60)


def init_permissions():
    print("=" * 60)
    print("KHOI TAO CLIENT ROLES CHUAN & DANH MUC PERMISSION TREN KEYCLOAK")
    print("=" * 60)

    client_name = "bida-app"
    try:
        client_uuid = get_client_uuid(client_name)
        print(f"OK: Tim thay Client '{client_name}' (UUID: {client_uuid})")
    except Exception as e:
        print(f"ERROR: Khong tim thay client '{client_name}': {e}")
        print("Hay dam bao Keycloak dang chay o cong 8080 va da tao client bida-app.")
        return False

    existing_roles = {r["name"]: r for r in get_client_roles(client_uuid)}

    # 1. Khoi tao 4 Role chuan trong Client bida-app
    print("\n--- 1. Khoi tao 4 Role chuan (Client Roles) trong Client 'bida-app' ---")
    std_created = 0
    std_skipped = 0
    for r_name, r_desc in STANDARD_CLIENT_ROLES.items():
        if r_name in existing_roles:
            print(f"  SKIP [DA TON TAI] {r_name}")
            std_skipped += 1
        else:
            try:
                create_client_role(client_uuid, r_name, description=r_desc)
                print(f"  CREATED [MOI] {r_name}")
                std_created += 1
            except Exception as e:
                print(f"  ERROR [LOI TAO] {r_name}: {e}")

    # 2. Khoi tao 8 Permissions (Client Roles) trong Client bida-app
    print("\n--- 2. Khoi tao 8 Permissions (Client Roles) trong Client 'bida-app' ---")
    perm_created = 0
    perm_skipped = 0

    for perm in StandardPermission:
        perm_code = perm.value
        description = PERMISSION_DESCRIPTIONS[perm]

        if perm_code in existing_roles:
            print(f"  SKIP [DA TON TAI] {perm_code}")
            perm_skipped += 1
        else:
            try:
                create_client_role(client_uuid, perm_code, description=description)
                print(f"  CREATED [MOI] {perm_code}")
                perm_created += 1
            except Exception as e:
                print(f"  ERROR [LOI TAO] {perm_code}: {e}")

    print("\n" + "-" * 60)
    print(f"Hoan tat! Roles moi: {std_created} (co san {std_skipped}), Permissions moi: {perm_created} (co san {perm_skipped})")
    print("=" * 60)

    # 3. Dong bo Composite Permissions theo bang phan quyen chuan
    sync_composite_permissions(client_uuid)
    return True


if __name__ == "__main__":
    init_permissions()
