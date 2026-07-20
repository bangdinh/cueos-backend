import cv2
import os
import time

try:
    print("Testing Webcam 0...")
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    print("Webcam read ret:", ret)
    if ret:
        print("Frame shape:", frame.shape)
        # Test writing image
        clips_dir = os.path.abspath("clips")
        os.makedirs(clips_dir, exist_ok=True)
        img_path = os.path.join(clips_dir, "test_write.jpg")
        success = cv2.imwrite(img_path, frame)
        print("cv2.imwrite success:", success)
        print("File exists:", os.path.exists(img_path))
        
        # Test VideoWriter with different codecs
        codecs = ['mp4v', 'XVID', 'MJPG', 'H264']
        for codec in codecs:
            try:
                fourcc = cv2.VideoWriter_fourcc(*codec)
                test_vid = os.path.join(clips_dir, f"test_{codec}.mp4")
                out = cv2.VideoWriter(test_vid, fourcc, 15.0, (frame.shape[1], frame.shape[2] if len(frame.shape)>2 else frame.shape[0])) # Wait, shape is (h, w, c) so shape[1] is w, shape[0] is h
                # Let's write (w, h)
                out = cv2.VideoWriter(test_vid, fourcc, 15.0, (frame.shape[1], frame.shape[0]))
                out.write(frame)
                out.release()
                print(f"Codec {codec} file size:", os.path.getsize(test_vid))
            except Exception as ex:
                print(f"Codec {codec} error:", ex)
    cap.release()
except Exception as e:
    print("Webcam error:", e)
