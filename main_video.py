import hashlib
import os
os.environ['PYDEVD_DISABLE_FILE_VALIDATION'] = '1'
import shutil
import time
from typing import List
import re
import cv2
from ultralytics import YOLO
from datetime import datetime

def main():
    try:    
        video_path = "for_detect/videos/Elon.mp4"
        cap = get_file_capture(video_path)
        # cap = get_camera_capture()

        if not os.path.exists("for_detect/yolov8l-face.pt"):
            raise FileNotFoundError("Файл модели не найден.")
        model = YOLO("for_detect/yolov8l-face.pt") 
        
        save_dir_full_photo = "for_detect/images_full_photo"
        save_dir_only_face = "for_detect/images_only_face"

        if not os.path.exists(save_dir_full_photo):
            os.mkdir(save_dir_full_photo)
        else:
            clear_directory(save_dir_full_photo)

        if not os.path.exists(save_dir_only_face):
            os.mkdir(save_dir_only_face)
        else:
            clear_directory(save_dir_only_face)
        count_op = 1
        count_fp = 1

        last_frame_time = 0
        save_interval = 1
        
        while True: 
            success, img = cap.read() 
            res = model(img, conf=0.6, device='mps')
            if success:
                current_time = time.time()
                boxes = res[0].boxes
                res_plotted = res[0].plot()
                cv2.namedWindow("Yolov8 big test", cv2.WINDOW_NORMAL)
                cv2.resizeWindow("Yolov8 big test", 640, 360)
                cv2.imshow("Yolov8 big test", res_plotted)

                if current_time - last_frame_time >= save_interval:
                    for box in boxes:
                        xyxy = box.xyxy
                        class_id = box.cls
                        class_mapping = {0: "Face"}

                        tensor_string_id = str(class_id)
                        clean_string_id = tensor_string_id.replace("tensor(", "").replace(")", "")
                        parts_id = clean_string_id.split(',')
                        number_id = float(parts_id[0].strip("[]"))
                        int_number_id = int(number_id)
                        class_name = class_mapping[int_number_id]

                        confidence_conf = box.conf
                        tensor_string_conf = str(confidence_conf)
                        clean_string_conf = tensor_string_conf.replace("tensor(", "").replace(")", "").replace("device='mps:0'", "")
                        number_string_conf = clean_string_conf.strip().strip("[]").strip(",").rstrip("]")
                        conf_hash = hashlib.sha1(number_string_conf.encode('utf-8')).hexdigest()[:8]

                        x1, y1, x2, y2 = map(int, xyxy[0])
                        padding_y = 65
                        padding_x = 50

                        height, width = img.shape[:2]

                        y1_new = max(0, y1 - padding_y)
                        y2_new = min(height, y2 + padding_y)

                        x1_new = max(0, x1 - padding_x)
                        x2_new = min(width, x2 + padding_x)

                        cropped_img = img[y1_new:y2_new, x1_new:x2_new]

                        if cropped_img.size > 0:
                            current_time_spec = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
                            cv2.imwrite(f"{save_dir_only_face}/op_{count_op}_{class_name}_{float(number_string_conf)}_{conf_hash}_{current_time_spec}.jpg", cropped_img)

                    cv2.imwrite(f"{save_dir_full_photo}/fp_{count_fp}.jpg", res_plotted)
                    
                    count_op += 1
                    count_fp += 1

                    last_frame_time = current_time 

                elapsed_time = time.time() - current_time
                print(f"Время обработки одного кадра: {elapsed_time:.5f} секунд")
                
                if cv2.waitKey(25) & 0xFF == ord('q'): 
                    break
            else:
                break
    except FileNotFoundError as e:
        print(f"Ошибка: {e}")
    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {e}")

def get_camera_capture(camera_num: int = 0) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(camera_num)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 20)
    return cap

def get_file_capture(video_path: str) -> cv2.VideoCapture:
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Файл {video_path} не найден.")
    cap = cv2.VideoCapture(video_path)
    return cap

def draw_frame_on_cropped_img(cropped_img: cv2.imread, text: str, ph_conf: float, thickness: int = 2, color: tuple = (0, 255, 0)) -> cv2.imread:
    framed_cropped_img = cropped_img.copy()
    h, w, _ = cropped_img.shape
    cv2.rectangle(framed_cropped_img, (0, 0), (w, h), color, thickness)

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_color = (0, 0, 255)
    font_thickness = 2
    max_text_width = int(w * 0.9)
    font_scale = 1
    text_width = w
    while text_width > max_text_width:
        font_scale -= 0.1
        (text_width, text_height), _ = cv2.getTextSize(text, font, font_scale, font_thickness)

    text_x = (w - text_width) // 2
    text_y = text_height + 10 

    cv2.putText(framed_cropped_img, text, (text_x, text_y), font, font_scale, font_color, font_thickness)

    second_line_text = str(round(ph_conf, 2))
    second_line_text_width = cv2.getTextSize(second_line_text, font, font_scale, font_thickness)[0][0]
    second_line_text_x = (w - second_line_text_width) // 2
    second_line_text_y = text_y + text_height + 10
    cv2.putText(framed_cropped_img, second_line_text, (second_line_text_x, second_line_text_y), font, font_scale, font_color, font_thickness)

    return framed_cropped_img

def get_last_created_file_in_images_full_photo(directory):
    files = os.listdir(directory)
    paths = [os.path.join(directory, file) for file in files]
    paths.sort(key=os.path.getmtime)
    return paths[-1] if paths else None

def clear_directory(directory: str):
    for file in os.listdir(directory):
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path):
            os.remove(file_path)

if __name__ == '__main__':
    main()