import cv2
import json
import time
import redis
import base64
import os
import traceback
import numpy as np
from collections import deque
from datetime import datetime

# Redis (Synchronous client)
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Thu muc luu clips va archives
CLIPS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "clips")
ARCHIVE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "archive")

os.makedirs(CLIPS_DIR, exist_ok=True)
os.makedirs(ARCHIVE_DIR, exist_ok=True)

# === CAU HINH AI ===
MOTION_THRESHOLD = 3000       # Dien tich chuyen dong de nhan dien cuon menu
HAND_ZONE_RATIO = 0.4         
WAVE_COUNT_REQUIRED = 3       
WAVE_WINDOW_SECONDS = 4       
COOLDOWN_SECONDS = 30         
BUFFER_SECONDS = 30           
FPS_ESTIMATE = 15
MAX_ARCHIVE_MINUTES = 30      

# === CAU HINH NHAN DIEN MENU MAU SAC ===
MENU_HSV_LOWER = [10, 100, 100]    # Mau Vang/Cam lower limit
MENU_HSV_UPPER = [35, 255, 255]    # Mau Vang/Cam upper limit
MENU_MIN_PIXELS = 150             # So luong pixel mau toi thieu de tinh la cam menu


def log_to_file(table_id, message):
    log_path = os.path.join(CLIPS_DIR, f"worker_{table_id}_debug.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")


def cleanup_old_archives(table_id, max_minutes=30):
    try:
        files = [f for f in os.listdir(ARCHIVE_DIR) if f.startswith(f"ban{table_id}_") and f.endswith(".mp4")]
        files.sort()
        if len(files) > max_minutes:
            for f in files[:-max_minutes]:
                filepath = os.path.join(ARCHIVE_DIR, f)
                if os.path.exists(filepath):
                    os.remove(filepath)
                    log_to_file(table_id, f"Da xoa archive cu: {f}")
    except Exception as e:
        log_to_file(table_id, f"Loi xoa archive cu: {e}")


def save_highlight_clip(table_id, frame_buffer, fps=15):
    if len(frame_buffer) < 10:
        log_to_file(table_id, "Chua du frame de tao clip")
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"highlight_ban{table_id}_{timestamp}.mp4"
    filepath = os.path.join(CLIPS_DIR, filename)

    h, w = frame_buffer[0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filepath, fourcc, fps, (w, h))

    frame_count = 0
    for frame in frame_buffer:
        overlay = frame.copy()
        cv2.putText(overlay, "Bida AI Highlight", (10, h - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(overlay, f"Ban {table_id}", (10, h - 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        out.write(overlay)
        frame_count += 1

    out.release()
    log_to_file(table_id, f"Da luu clip: {filename} ({frame_count} frames)")
    return filename


def process_camera_stream(table_id: int, rtsp_url: str):
    log_to_file(table_id, "--- Bat dau khoi dong AI stream ---")
    try:
        cam_source = int(rtsp_url) if str(rtsp_url).isdigit() else rtsp_url
        cap = cv2.VideoCapture(cam_source)

        last_alert_time = 0
        current_minute = ""
        video_writer = None

        frame_buffer = deque(maxlen=BUFFER_SECONDS * FPS_ESTIMATE)
        wave_timestamps = deque(maxlen=20)

        ret, frame1 = cap.read()
        ret, frame2 = cap.read()

        if not ret:
            log_to_file(table_id, "Loi: Khong the doc tu camera")
            return

        frame_height = frame1.shape[0]
        hand_zone_y = int(frame_height * HAND_ZONE_RATIO)

        log_to_file(table_id, f"Webcam bat thanh cong. Size: {frame1.shape[1]}x{frame_height}")

        while cap.isOpened() and ret:
            frame_buffer.append(frame1.copy())

            # 1. Ghi anh live camera truc tiep vao Redis (In-memory, tranh loi file lock tren Windows)
            if len(frame_buffer) % 3 == 0:
                ret_jpg, buffer = cv2.imencode('.jpg', frame1)
                if ret_jpg:
                    try:
                        redis_client.set(f"live_frame_{table_id}", buffer.tobytes())
                    except Exception as ex:
                        log_to_file(table_id, f"Loi ghi live frame len Redis: {ex}")

            # 2. Ghi hinh 24/7
            now = datetime.now()
            minute_str = now.strftime("%H%M")
            
            if minute_str != current_minute:
                if video_writer is not None:
                    video_writer.release()
                    log_to_file(table_id, f"Da dong archive phut: {current_minute}")
                
                current_minute = minute_str
                archive_path = os.path.join(ARCHIVE_DIR, f"ban{table_id}_{minute_str}.mp4")
                h, w = frame1.shape[:2]
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                video_writer = cv2.VideoWriter(archive_path, fourcc, FPS_ESTIMATE, (w, h))
                
                if not video_writer.isOpened():
                    log_to_file(table_id, f"Loi: VideoWriter khong the mo voi codec mp4v")
                else:
                    log_to_file(table_id, f"Mo archive moi: {archive_path}")
                
                cleanup_old_archives(table_id, MAX_ARCHIVE_MINUTES)
                
            if video_writer is not None and video_writer.isOpened():
                video_writer.write(frame1)

            # 3. Phan tich chuyen dong va xac thuc cuon Menu (Da go bo vi dung QR Code)
            pass

            # 4. Highlight
            clip_request = redis_client.get(f"clip_request_{table_id}")
            if clip_request:
                redis_client.delete(f"clip_request_{table_id}")
                log_to_file(table_id, "Nhan lenh quay highlight")
                clip_filename = save_highlight_clip(table_id, frame_buffer, FPS_ESTIMATE)
                if clip_filename:
                    redis_client.set(f"clip_ready_{table_id}", clip_filename)
                    event_data = {
                        "table_id": table_id,
                        "event_type": "CLIP_READY",
                        "confidence": 1.0,
                        "message": f"Clip Highlight Ban {table_id} da san sang tai ve!",
                        "clip_url": f"/clips/{clip_filename}",
                        "image": ""
                    }
                    redis_client.set('latest_ai_event', json.dumps(event_data))

            frame1 = frame2
            ret, frame2 = cap.read()

        if video_writer is not None:
            video_writer.release()
        cap.release()
        log_to_file(table_id, "Worker ket thuc binh thuong")
    except Exception as e:
        log_to_file(table_id, f"CRITICAL CRASH in worker: {e}\n{traceback.format_exc()}")
