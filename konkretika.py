import dlib
import cv2
import numpy as np

def extract_landmarks(image_path):
    # Загрузка изображения
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Загрузка детектора лиц и предиктора ключевых точек из dlib
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

    # Детектирование лиц
    faces = detector(gray)
    for face in faces:
        landmarks = predictor(gray, face)
        landmarks_points = []
        for n in range(0, 68):
            x = landmarks.part(n).x
            y = landmarks.part(n).y
            landmarks_points.append((x, y))
            cv2.circle(image, (x, y), 2, (255, 0, 0), -1)
    
        # Пример вычисления биометрической характеристики: расстояние между глазами
        left_eye_center = np.array(landmarks_points[42])
        right_eye_center = np.array(landmarks_points[39])
        inter_eye_distance = np.linalg.norm(left_eye_center - right_eye_center)
        
        # Оценка симметрии лица и анализ угла наклона головы
        symmetry_score = evaluate_symmetry(landmarks_points)
        tilt_angle = head_tilt_angle(landmarks_points)

        print(f"Оценка симметрии лица: {symmetry_score}")
        print(f"Угол наклона головы: {tilt_angle} градусов")
        print(f"Расстояние между глазами: {inter_eye_distance}")

    cv2.imshow("Landmarks", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def evaluate_symmetry(landmarks_points):
    # Мы будем использовать точки лица с 1 по 17 для оценки симметрии.
    left_side = np.array(landmarks_points[0:8])  # Левая сторона лица
    right_side = np.array(landmarks_points[9:17])  # Правая сторона лица

    right_side = np.flip(right_side, axis=0)  # Переворачиваем массив точек правой стороны

    # Вычисляем среднее расстояние между соответствующими точками
    distances = np.linalg.norm(left_side - right_side, axis=1)
    mean_distance = np.mean(distances)

    return mean_distance

def head_tilt_angle(landmarks_points):
    # Для определения угла наклона головы мы будем использовать глаза
    left_eye_center = np.array(landmarks_points[42])
    right_eye_center = np.array(landmarks_points[39])

    # Вычисление угла наклона
    dY = right_eye_center[1] - left_eye_center[1]
    dX = right_eye_center[0] - left_eye_center[0]
    angle = np.degrees(np.arctan2(dY, dX))

    return angle


extract_landmarks("images_only_face/op_12_Face_0.9333_4fc552b9.jpg")
