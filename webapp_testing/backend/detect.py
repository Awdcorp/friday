from ultralytics import YOLO

model = YOLO("yolov8s.pt")

def detect_objects_from_frame(frame):
    results = model(frame)
    labels = set()
    for r in results:
        for cls in r.boxes.cls:
            labels.add(model.names[int(cls)])
    return list(labels)
