from database.database import SessionLocal
from services.table_service import TableService
from services.store_service import StoreService

def run_test():
    print("=== BẮT ĐẦU TEST LOCAL SERVICES ===")
    
    # Khởi tạo kết nối DB cục bộ
    db = SessionLocal()
    
    try:
        # 1. Test StoreService
        print("\n[1] Đang test StoreService...")
        stores = StoreService.get_all_stores(db)
        print(f"-> Tìm thấy {len(stores)} cửa hàng.")
        for s in stores:
            print(f"   - ID: {s.id} | Tên: {s.name}")

        # 2. Test ProductService (Lấy menu của chi nhánh đầu tiên)
        if stores:
            first_store_id = stores[0].id
            print(f"\n[2] Đang test ProductService cho chi nhánh ID={first_store_id}...")
            from services.product_service import ProductService
            products = ProductService.get_menu_by_store(db, first_store_id)
            print(f"-> Tìm thấy {len(products)} món trong Menu.")
            for p in products:
                print(f"   - Món: {p.name} | Giá: {p.price} | Tồn kho: {p.stock}")
        
    except Exception as e:
        print(f"❌ LỖI TRONG QUÁ TRÌNH TEST: {e}")
    finally:
        db.close()
        print("\n=== KẾT THÚC TEST ===")

if __name__ == "__main__":
    run_test()
