from typing import List, Optional
from sqlalchemy.orm import Session
from database.models import StoreModel

class StoreService:
    # In-memory cache for demonstration purposes
    # Key: store_id, Value: StoreModel dictionary representation or object
    # For a real production app, consider using Redis
    _cache_all_stores: Optional[List[StoreModel]] = None
    _cache_store_by_id = {}

    @classmethod
    def get_all_stores(cls, db: Session, bypass_cache: bool = False) -> List[StoreModel]:
        """
        Lấy danh sách tất cả cửa hàng.
        Sử dụng bộ nhớ đệm (cache) để tăng tốc độ truy vấn cho các lần gọi sau.
        """
        if not bypass_cache and cls._cache_all_stores is not None:
            return cls._cache_all_stores
        
        stores = db.query(StoreModel).order_by(StoreModel.id).all()
        
        # Lưu vào cache
        cls._cache_all_stores = stores
        for store in stores:
            cls._cache_store_by_id[store.id] = store
            
        return stores

    @classmethod
    def get_store_by_id(cls, db: Session, store_id: int, bypass_cache: bool = False) -> Optional[StoreModel]:
        """
        Lấy thông tin một cửa hàng theo ID.
        """
        if not bypass_cache and store_id in cls._cache_store_by_id:
            return cls._cache_store_by_id[store_id]
            
        store = db.query(StoreModel).filter(StoreModel.id == store_id).first()
        
        # Lưu vào cache nếu tìm thấy
        if store:
            cls._cache_store_by_id[store_id] = store
            
        return store

    @classmethod
    def invalidate_cache(cls):
        """
        Xóa cache khi có cập nhật thông tin cửa hàng.
        Nên gọi hàm này sau khi thêm/sửa/xóa cửa hàng.
        """
        cls._cache_all_stores = None
        cls._cache_store_by_id = {}
