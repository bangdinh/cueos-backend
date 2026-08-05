import math
from datetime import datetime
from sqlalchemy.orm import Session
from database.models import PlaySession, BilliardTable, SessionOrderItem
from typing import List, Dict, Any

class SessionService:
    @staticmethod
    def start_session(db: Session, table_id: int) -> PlaySession:
        """
        Mở bàn và bắt đầu một phiên chơi mới.
        """
        table = db.query(BilliardTable).filter(BilliardTable.id == table_id).first()
        if not table:
            raise ValueError("Không tìm thấy bàn")
        if table.current_status == "PLAYING":
            raise ValueError("Bàn đang chơi rồi")
            
        table.current_status = "PLAYING"
        new_session = PlaySession(table_id=table_id, store_id=table.store_id)
        db.add(new_session)
        db.commit()
        return new_session

    @staticmethod
    def stop_session_and_checkout(db: Session, table_id: int) -> Dict[str, Any]:
        """
        Tính tiền và kết thúc phiên chơi.
        """
        table = db.query(BilliardTable).filter(BilliardTable.id == table_id).first()
        if not table:
            raise ValueError("Không tìm thấy bàn")
        if table.current_status != "PLAYING":
            raise ValueError("Bàn chưa bật tính giờ")
            
        active_session = db.query(PlaySession).filter(
            PlaySession.table_id == table_id,
            PlaySession.status == "ACTIVE"
        ).first()
        if not active_session:
            raise ValueError("Không tìm thấy phiên chơi active")
            
        end_time = datetime.utcnow()
        duration = end_time - active_session.start_time
        total_minutes = max(1, math.ceil(duration.total_seconds() / 60))
        
        play_fee = math.ceil((total_minutes / 60.0) * table.price_per_hour)
        
        active_session.end_time = end_time
        active_session.total_minutes = total_minutes
        active_session.play_fee = play_fee
        active_session.status = "COMPLETED"
        
        table.current_status = "EMPTY"
        
        items = db.query(SessionOrderItem).filter(SessionOrderItem.session_id == active_session.id).all()
        service_total = sum(i.total_price for i in items)
        total_bill = play_fee + service_total
        
        active_session.services_fee = service_total
        active_session.total_amount = total_bill
        db.commit()
        
        return {
            "session_id": active_session.id,
            "store_id": table.store_id or 1,
            "table_name": table.name,
            "start_time": active_session.start_time.isoformat() + "Z",
            "end_time": end_time.isoformat() + "Z",
            "total_minutes": total_minutes,
            "play_fee": play_fee,
            "service_total": service_total,
            "total_bill": total_bill,
            "items": [{"name": i.item_name, "item_name": i.item_name, "quantity": i.quantity, "price": i.price, "total_price": i.total_price} for i in items]
        }

    @staticmethod
    def get_active_session(db: Session, table_id: int) -> PlaySession:
        """Lấy thông tin phiên chơi đang diễn ra của một bàn."""
        return db.query(PlaySession).filter(
            PlaySession.table_id == table_id,
            PlaySession.status == "ACTIVE"
        ).first()

    @staticmethod
    def get_history(db: Session, store_id: int = None, is_hq: bool = False) -> List[Dict[str, Any]]:
        """Lấy danh sách các phiên chơi đã hoàn thành (lịch sử hóa đơn)."""
        now = datetime.utcnow()
        query = db.query(PlaySession).filter(PlaySession.status == "COMPLETED")
        if not is_hq:
            query = query.filter(PlaySession.store_id == store_id)
        elif store_id is not None:
            query = query.filter(PlaySession.store_id == store_id)
        sessions = query.order_by(PlaySession.end_time.desc()).all()
        
        result = []
        for s in sessions:
            table = db.query(BilliardTable).filter(BilliardTable.id == s.table_id).first()
            items = db.query(SessionOrderItem).filter(SessionOrderItem.session_id == s.id).all()
            
            service_total = sum(i.total_price for i in items)
            total_bill = (s.play_fee or 0) + service_total
            
            can_delete = False
            if s.end_time:
                diff_hours = (now - s.end_time).total_seconds() / 3600.0
                if diff_hours <= 2.0:
                    can_delete = True
                    
            result.append({
                "id": s.id,
                "store_id": s.store_id or (table.store_id if table else 1),
                "table_id": s.table_id,
                "table_name": table.name if table else f"Bàn {s.table_id}",
                "start_time": s.start_time.isoformat() + "Z",
                "end_time": s.end_time.isoformat() + "Z" if s.end_time else None,
                "total_minutes": s.total_minutes or 0,
                "play_fee": s.play_fee or 0,
                "service_total": service_total,
                "total_bill": total_bill,
                "can_delete": can_delete,
                "items": [{"name": i.item_name, "item_name": i.item_name, "quantity": i.quantity, "price": i.price, "total_price": i.total_price} for i in items]
            })
        return result
        
    @staticmethod
    def delete_history_sessions(db: Session, session_ids: List[int]) -> Dict[str, Any]:
        """
        Xóa lịch sử hóa đơn. 
        """
        now = datetime.utcnow()
        deleted_count = 0
        cannot_delete_count = 0
        
        for hid in session_ids:
            session = db.query(PlaySession).filter(PlaySession.id == hid, PlaySession.status == "COMPLETED").first()
            if not session:
                continue
                
            if session.end_time:
                diff_hours = (now - session.end_time).total_seconds() / 3600.0
                if diff_hours > 2.0:
                    cannot_delete_count += 1
                    continue
                    
            db.query(SessionOrderItem).filter(SessionOrderItem.session_id == session.id).delete()
            db.delete(session)
            deleted_count += 1
            
        db.commit()
        return {
            "deleted_count": deleted_count,
            "cannot_delete_count": cannot_delete_count
        }
