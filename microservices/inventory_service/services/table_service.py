from sqlalchemy.orm import Session
from database.models import BilliardTable, TableStatus, PlaySession
from services.notification_service import NotificationService

class TableService:
    @staticmethod
    def get_tables(db: Session, store_id: int):
        """Lấy danh sách các bàn của chi nhánh."""
        return db.query(BilliardTable).filter(BilliardTable.store_id == store_id).all()
        
    @staticmethod
    def get_table_by_id(db: Session, table_id: int):
        """Lấy thông tin chi tiết của một bàn cụ thể."""
        return db.query(BilliardTable).filter(BilliardTable.id == table_id).first()

    @staticmethod
    def update_table_status(db: Session, table_id: int, status: str):
        """Cập nhật trạng thái của bàn (TRỐNG, ĐANG CHƠI, BẢO TRÌ)."""
        table = TableService.get_table_by_id(db, table_id)
        if table:
            table.current_status = status
            db.commit()
        return table

    @staticmethod
    def transfer_table(db: Session, from_table_id: int, to_table_id: int):
        """
        Xử lý nghiệp vụ đổi bàn cho khách.
        """
        if from_table_id == to_table_id:
            raise ValueError("Không thể chuyển sang cùng bàn!")
            
        from_table = db.query(BilliardTable).filter(BilliardTable.id == from_table_id).first()
        to_table = db.query(BilliardTable).filter(BilliardTable.id == to_table_id).first()
        
        if not from_table or not to_table:
            raise ValueError("Bàn không tồn tại!")
            
        if from_table.current_status != "PLAYING":
            raise ValueError(f"{from_table.name} không ở trạng thái đang chơi!")
            
        if to_table.current_status == "PLAYING":
            raise ValueError(f"{to_table.name} đã có khách chơi, không thể chuyển sang!")
            
        active_session = db.query(PlaySession).filter(
            PlaySession.table_id == from_table_id,
            PlaySession.status == "ACTIVE"
        ).first()
        
        if not active_session:
            raise ValueError("Không tìm thấy phiên chơi active!")
            
        active_session.table_id = to_table_id
        from_table.current_status = "EMPTY"
        to_table.current_status = "PLAYING"
        
        db.commit()

        from api.routes.sessions import generate_table_token
        to_token = generate_table_token(to_table_id)
        new_url = f"/menu/{to_table_id}/{to_token}"
        
        # Notify the client they have been transferred
        NotificationService.notify_client_qr(
            from_table_id,
            message=f"Yêu cầu đổi bàn đã được chấp nhận! Bạn đã được chuyển từ {from_table.name} sang {to_table.name}.",
            message_type="redirect",
            redirect_url=new_url
        )
        
        return from_table, to_table
