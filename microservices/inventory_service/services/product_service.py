from sqlalchemy.orm import Session
from database.models import Product

class ProductService:
    @staticmethod
    def decrease_stock(db: Session, product_id: int, quantity: int) -> bool:
        """
        Trừ số lượng tồn kho của một sản phẩm.
        
        [CACHE INVALIDATION]: Nhớ gọi hàm xóa cache danh sách sản phẩm (ví dụ: product_service.invalidate_store_menu(store_id)) 
        sau khi update thành công để đảm bảo menu được cập nhật mới nhất.
        """
        product = db.query(Product).filter(Product.deleted_at == None).filter(Product.id == product_id).first()
        if product:
            product.stock -= quantity
            if product.stock < 0:
                product.stock = 0
            db.commit()
            return True
        return False
        
    @staticmethod
    def decrease_stock_by_name(db: Session, product_name: str, quantity: int) -> Product:
        """
        Trừ tồn kho bằng tên sản phẩm.
        
        [CACHE INVALIDATION]: Nhớ gọi hàm xóa cache danh sách sản phẩm 
        nếu hệ thống đang áp dụng cơ chế caching cho menu thực đơn.
        """
        product = db.query(Product).filter(Product.deleted_at == None).filter(Product.name == product_name).first()
        if product:
            product.stock -= quantity
            if product.stock < 0:
                product.stock = 0
            db.commit()
        return product

    @staticmethod
    def increase_stock(db: Session, product_id: int, quantity: int):
        """
        Cộng số lượng tồn kho.
        
        [CACHE INVALIDATION]: Nhớ gọi hàm xóa cache nếu có sử dụng bộ nhớ đệm cho danh sách sản phẩm.
        """
        product = db.query(Product).filter(Product.deleted_at == None).filter(Product.id == product_id).first()
        if product:
            product.stock += quantity
            db.commit()
            
    @staticmethod
    def get_menu_by_store(db: Session, store_id: int):
        """
        Lấy toàn bộ thực đơn của quán.
        """
        return db.query(Product).filter(Product.deleted_at == None).filter(Product.store_id == store_id).all()
