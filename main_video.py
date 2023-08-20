# https://github.com/ultralytics/ultralytics
import hashlib
import os
os.environ['PYDEVD_DISABLE_FILE_VALIDATION'] = '1'
import shutil
import time
from typing import List
import re
import cv2
import pytube
from ultralytics import YOLO
from blockchain import write_block
from deepface import DeepFace

def main():
    try:    
        # video_path = "videos/1.mp4"
        # cap = get_file_capture(video_path)
        cap = get_camera_capture()

        # Проверка на наличие файла модели
        if not os.path.exists("yolov8_test/model_test_main_part2/weights/best.pt"):
            raise FileNotFoundError("Файл модели не найден.")
        model = YOLO("yolov8_test/model_test_main_part2/weights/best.pt")
        
        save_dir_full_photo = "images_full_photo"
        save_dir_only_face = "images_only_face"

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

                # Сохранение результатов с определенным интервалом
                if current_time - last_frame_time >= save_interval:
                    for box in boxes:
                        xyxy = box.xyxy
                        class_id = box.cls
                        class_mapping = {0: "APro", 1:"Cap", 2:"Face"}

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
                        cropped_img = img[y1-35:y2+10, x1-10:x2+10]

                        if cropped_img.size > 0:
                            cv2.imwrite(f"{save_dir_only_face}/op_{count_op}_{class_name}_{float(number_string_conf)}_{conf_hash}.jpg", cropped_img)
                            if int_number_id==2:
                                result = DeepFace.analyze(img_path=cropped_img, actions=['age', 'gender', 'emotion', 'race'], enforce_detection=False)
                                age = result[0]['age']

                                gender_probabilities = result[0]['gender']
                                genderM = gender_probabilities['Man']
                                genderW = gender_probabilities['Woman']

                                emotions_dict = result[0]['emotion']
                                sorted_emotions_dict = sorted(emotions_dict.items(), key=lambda x: x[1], reverse=True)

                                races = result[0]['race']
                                sorted_races = sorted(races.items(), key=lambda x: x[1], reverse=True)

                            write_block(f"op_{count_op}_{class_name}_{float(number_string_conf)}_{conf_hash}.jpg", 
                                class_name, age, genderM, genderW, sorted_emotions_dict, sorted_races)

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

"""Захват видеопотока с камеры."""
def get_camera_capture(camera_num: int = 0) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(camera_num)
    return cap

"""Захват видеопотока из файла."""
def get_file_capture(video_path: str) -> cv2.VideoCapture:
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Файл {video_path} не найден.")
    cap = cv2.VideoCapture(video_path)
    return cap

"""Добавляет рамку и текст к обрезанному изображению."""
def draw_frame_on_cropped_img(cropped_img: cv2.imread, text: str, ph_conf: float, thickness: int = 2, color: tuple = (0, 255, 0)) -> cv2.imread:
    framed_cropped_img = cropped_img.copy()
    h, w, _ = cropped_img.shape
    cv2.rectangle(framed_cropped_img, (0, 0), (w, h), color, thickness)

    # Настройка параметров шрифта
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

    # Добавление дополнительной строки текста
    second_line_text = str(round(ph_conf, 2))
    second_line_text_width = cv2.getTextSize(second_line_text, font, font_scale, font_thickness)[0][0]
    second_line_text_x = (w - second_line_text_width) // 2
    second_line_text_y = text_y + text_height + 10
    cv2.putText(framed_cropped_img, second_line_text, (second_line_text_x, second_line_text_y), font, font_scale, font_color, font_thickness)

    return framed_cropped_img

"""Возвращает путь к последнему созданному файлу в указанной директории."""
def get_last_created_file_in_images_full_photo(directory):
    files = os.listdir(directory)
    paths = [os.path.join(directory, file) for file in files]
    paths.sort(key=os.path.getmtime)
    return paths[-1] if paths else None

"""Очищает содержимое указанной директории."""
def clear_directory(directory: str):
    for file in os.listdir(directory):
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path):
            os.remove(file_path)

if __name__ == '__main__':
    main()