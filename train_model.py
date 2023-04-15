from ultralytics import YOLO

model = YOLO("yolov8s.pt")

results = model.train(
    data="*******",
    epochs=100,
    imgsz=640,
    project="yolov8_test",
    name="model_test_1"
)