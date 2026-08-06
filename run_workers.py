import multiprocessing as mp
import time
import sys
import io
from ai_workers.stream_processor import process_camera_stream

# Force stdout to UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
def main():
    store_id = int(os.getenv("STORE_ID", 1))
    # Sử dụng '0' cho Bàn 1 để AI tự động bật Webcam Laptop của bạn
    tables = [
        (1, "0"),
    ]
    processes = {}

    print(f"Khoi dong AI Workers System (Real Webcam) cho chi nhánh Store ID: {store_id}...")
    for table_id, rtsp_url in tables:
        p = mp.Process(target=process_camera_stream, args=(table_id, rtsp_url, store_id))
        p.start()
        processes[table_id] = p

    try:
        while True:
            for table_id, p in processes.items():
                if not p.is_alive():
                    print(f"[Watchdog] Tien trinh ban {table_id} chet. Dang restart...")
                    rtsp_url = next(url for tid, url in tables if tid == table_id)
                    new_p = mp.Process(target=process_camera_stream, args=(table_id, rtsp_url, store_id))
                    new_p.start()
                    processes[table_id] = new_p
            time.sleep(5)
    except KeyboardInterrupt:
        print("\nDang tat tat ca AI Workers...")
        for p in processes.values():
            p.terminate()

if __name__ == "__main__":
    main()
