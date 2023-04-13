import hashlib
import os
import shutil
import time
from typing import List
import re
import cv2
import pytube
from ultralytics import YOLO
from blockchain import write_block

def download_youtube_video(youtube_url: str, save_dir_full_video: str = 'videos/youtube') -> cv2.VideoCapture:
    if not os.path.exists(save_dir_full_video):
        os.makedirs(save_dir_full_video)

    yt = pytube.YouTube(youtube_url)
    stream = yt.streams.filter(res="1080p", file_extension="mp4").first()
    file_path = os.path.join(save_dir_full_video, stream.default_filename)
    stream.download(output_path=save_dir_full_video)

    cap = cv2.VideoCapture(file_path)
    return cap

def get_camera_capture(camera_num: int = 0) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(camera_num)
    return cap

def get_file_capture(video_path: str) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(video_path)
    return cap

def draw_frame_on_cropped_img(cropped_img: cv2.imread, text: str, ph_conf: float, thickness: int = 2, color: tuple = (0, 255, 0)) -> cv2.imread:
    framed_cropped_img = cropped_img.copy()
    h, w, _ = cropped_img.shape
    cv2.rectangle(framed_cropped_img, (0, 0), (w, h), color, thickness)

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_color = (0, 0, 255)  # Красный цвет
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

def main():
    youtube_url = 'https://www.youtube.com/watch?v=h2MfDmyBFt8'
    save_dir_full_video = 'videos/youtube'
    video_path = "videos/my_video.mp4"

    # cap = get_file_capture(video_path)
    # cap = download_youtube_video(youtube_url, save_dir_full_video)
    cap = get_camera_capture()

    # model = YOLO("yolov8n-face.pt") 
    model = YOLO("yolov8_test/model_test_main_part2/weights/best.pt") 


    save_dir_full_photo = "images_full_photo"
    save_dir_only_face = "images_only_face"

    if os.path.exists(save_dir_full_photo):
        shutil.rmtree(save_dir_full_photo)
    os.mkdir(save_dir_full_photo)
    if os.path.exists(save_dir_only_face):
        shutil.rmtree(save_dir_only_face)
    os.mkdir(save_dir_only_face)
    count_op = 0
    count_fp = 0

    # last_created_file_in_images_full_photo = get_last_created_file_in_images_full_photo(save_dir_full_photo)
    # count_fp = int(last_created_file_in_images_full_photo.split("_")[-1].split(".")[0])
    # last_created_file_in_save_dir_only_face = get_last_created_file_in_images_full_photo(save_dir_only_face)
    # match = re.search(r"op_(\d+)_", last_created_file_in_save_dir_only_face)
    # count_op = int(match.group(1)) if match else None

    count_op += 1
    count_fp += 1
    last_frame_time = 0
    save_interval = 1

    while True: 
        success, img = cap.read() 
        res = model(img, device='mps')
        if success:
            current_time = time.time()
            boxes = res[0].boxes
            cropped_imgs = []

            res_plotted = res[0].plot()
            cv2.namedWindow("Yolov8 big test", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("Yolov8 big test", 640, 360)
            cv2.imshow("Yolov8 big test", res_plotted)

            if current_time - last_frame_time >= save_interval:
                for box in boxes:
                    xyxy = box.xyxy
                    class_id = box.cls
                    class_mapping = {0: "APro", 1:"Cap", 2:"Face"}

                    tensor_string_id = str(class_id) # Извлекаем название объекта
                    clean_string_id = tensor_string_id.replace("tensor(", "").replace(")", "")
                    parts_id = clean_string_id.split(',')
                    number_id = float(parts_id[0].strip("[]"))
                    int_number_id = int(number_id)
                    class_name = class_mapping[int_number_id]

                    confidence_conf = box.conf  # Извлекаем вероятность распознавания объекта (confidence)
                    tensor_string_conf = str(confidence_conf)
                    clean_string_conf = tensor_string_conf.replace("tensor(", "").replace(")", "").replace("device='mps:0'", "")
                    number_string_conf = clean_string_conf.strip().strip("[]").strip(",").rstrip("]")
                    conf_hash = hashlib.sha1(number_string_conf.encode('utf-8')).hexdigest()[:8]  # Generate hash value from confidence value

                    x1, y1, x2, y2 = map(int, xyxy[0])
                    cropped_img = img[y1-35:y2+10, x1-10:x2+10]
                    cropped_imgs.append(cropped_img)

                    if cropped_img.size > 0:
                        framed_cropped_img = draw_frame_on_cropped_img(cropped_img, class_name, float(number_string_conf)) 
                        cv2.imwrite(f"{save_dir_only_face}/op_{count_op}_{class_name}_{float(number_string_conf)}_{conf_hash}.jpg", framed_cropped_img)
                        write_block(f"op_{count_op}_{class_name}_{float(number_string_conf)}_{conf_hash}.jpg", class_name)
                
                cv2.imwrite(f"{save_dir_full_photo}/fp_{count_fp}.jpg", res_plotted)
                count_op += 1
                count_fp += 1
                last_frame_time = current_time 

            if cv2.waitKey(25) & 0xFF == ord('q'): 
                break
        else:
            break

if __name__ == '__main__':
    main()