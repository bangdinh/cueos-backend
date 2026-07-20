import cv2
import time

def run_direct_ai():
    print("Khởi động AI Camera (Hiển thị trực tiếp)...")
    # Thay bằng rtsp_url nếu dùng camera IP, số 0 là webcam laptop
    cap = cv2.VideoCapture(0)
    
    ret, frame1 = cap.read()
    ret, frame2 = cap.read()
    
    if not ret:
        print("Lỗi: Không thể mở Camera!")
        return

    print("✅ Camera đã bật. Bấm phím 'q' trên bàn phím để thoát.")

    last_alert_time = 0

    while cap.isOpened():
        # Xử lý ảnh để tìm chuyển động
        diff = cv2.absdiff(frame1, frame2)
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
        dilated = cv2.dilate(thresh, None, iterations=3)
        contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        motion_detected = False
        for contour in contours:
            if cv2.contourArea(contour) > 2000: 
                (x, y, w, h) = cv2.boundingRect(contour)
                # Vẽ khung xanh lá quanh vật thể chuyển động
                cv2.rectangle(frame1, (x, y), (x+w, y+h), (0, 255, 0), 2)
                motion_detected = True
        
        current_time = time.time()
        
        # Nếu phát hiện chuyển động, hiện chữ đỏ to
        if motion_detected:
            cv2.putText(frame1, "⚠️ PHAT HIEN KHACH VAY TAY!", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
            last_alert_time = current_time
        
        # Giữ cảnh báo trên màn hình thêm 2 giây để dễ nhìn
        elif current_time - last_alert_time < 2:
            cv2.putText(frame1, "⚠️ PHAT HIEN KHACH VAY TAY!", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

        # Hiển thị cửa sổ Video
        cv2.imshow("Bida AI System - Live Camera", frame1)
        
        frame1 = frame2
        ret, frame2 = cap.read()

        # Bấm 'q' để thoát
        if cv2.waitKey(10) == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_direct_ai()
