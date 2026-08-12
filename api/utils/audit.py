from sqlalchemy.orm import Session
from database.models.auth_business import AuditLog
from fastapi import Request

def log_audit_action(
    db: Session,
    action: str,
    target_type: str,
    target_id: int,
    user_id: int = None,
    store_id: int = None,
    ip_address: str = None,
    request: Request = None
):
    """
    Hàm hỗ trợ ghi nhận Audit Log.
    Nếu truyền `request` vào, hàm sẽ cố gắng tự động trích xuất ip_address.
    """
    if request and not ip_address:
        # Lấy IP từ X-Forwarded-For nếu đi qua gateway/proxy
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip_address = forwarded.split(",")[0].strip()
        else:
            ip_address = request.client.host if request.client else None
            
    log_entry = AuditLog(
        user_id=user_id,
        store_id=store_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        ip_address=ip_address
    )
    
    db.add(log_entry)
    db.commit()
    
    return log_entry
