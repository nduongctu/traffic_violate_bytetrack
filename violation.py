import cv2
import os
import pandas as pd
from ultralytics import YOLO
from tracker import *
from detect import *

model = YOLO('yolov9e.pt')

class_list = ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush']

tracking_class = [2, 3, 5, 7, 9]  # car, motorcycle, bus, truck
count = 0

traffic_light_detector = TrafficLightDetector()
tracker = Tracker()

# Video
cap = cv2.VideoCapture('C:/Users/Duong/PycharmProjects/nienluannganh/traffic_violations/data/1.mp4')

# Kích thước của video đầu vào và các thông số khác
width = 1420
height = 980
conf_threshold = 0.5

# Khởi tạo video writer sử dụng kích thước của video đầu vào
output_video = cv2.VideoWriter('output_video.avi', cv2.VideoWriter_fourcc(*'XVID'), 30, (width, height))

# Tạo thư mục vipham nếu chưa tồn tại
vipham_dir = 'vipham'
if not os.path.exists(vipham_dir):
    os.makedirs(vipham_dir)

violate = {}
traffic_light_colors = {}
counter_violate = set()

# Đọc và lưu giá trị x1, y1, x2, y2 từ file tọa độ
def read_coordinates_from_file(toado_file):
    x1_f, y1_f, x2_f, y2_f = 0, 0, 0, 0
    with open(toado_file, 'r') as file:
        lines = file.readlines()
        for line in lines:
            # Phân tích tọa độ từ dòng văn bản
            coordinates = line.strip().split(',')
            for coord in coordinates:
                if coord.startswith('x1='):
                    x1_f = int(coord.split('=')[1])
                elif coord.startswith('y1='):
                    y1_f = int(coord.split('=')[1])
                elif coord.startswith('x2='):
                    x2_f = int(coord.split('=')[1])
                elif coord.startswith('y2='):
                    y2_f = int(coord.split('=')[1])
    return x1_f, y1_f, x2_f, y2_f

# Sử dụng hàm để đọc giá trị từ file
x1_f, y1_f, x2_f, y2_f = read_coordinates_from_file('toado.txt')
print("x1 =", x1_f)
print("y1 =", y1_f)
print("x2 =", x2_f)
print("y2 =", y2_f)

while True:
    ret,frame = cap.read()
    if not ret:
        break
    count += 1

    frame = cv2.resize(frame, (width, height))

    results = model.predict(frame, classes=[2, 3, 5, 7, 9], conf=conf_threshold)

    a = results[0].boxes.data
    a = a.detach().cpu().numpy()
    px = pd.DataFrame(a).astype("float")

    list = []

    for index, row in px.iterrows():
        x1 = int(row[0])
        y1 = int(row[1])
        x2 = int(row[2])
        y2 = int(row[3])
        d = int(row[5])
        c = class_list[d]
        if d in tracking_class:
            if d == 9:  # Nếu đối tượng là đèn giao thông
                frame, traffic_light_color = traffic_light_detector.detect_traffic_light_color(frame, (x1, y1, x2 - x1, y2 - y1))
                traffic_light_colors[(x1, y1, x2, y2)] = traffic_light_color
            else:
                list.append([x1, y1, x2, y2])

    bbox_id = tracker.update(list)
    if traffic_light_color in ['red', 'yellow']:
        for bbox in bbox_id:
            x3, y3, x4, y4, id = bbox
            cx = int(x3 + x4) // 2
            cy = int(y3 + y4) // 2
            cv2.rectangle(frame, (x3, y3), (x4, y4), (0, 255, 0), 2)  # Draw bounding box

            y = y1_f
            offset = 10

            # Kiểm tra nếu xe di chuyển qua đường và màu đèn giao thông là đỏ hoặc vàng
            if y < (cy + offset) and y > (cy - offset):
                violate[id] = cy
                if id in violate:
                    cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)
                    cv2.putText(frame, str(id), (cx, cy), cv2.FONT_HERSHEY_COMPLEX, 0.8, (0, 255, 255), 2)
                    counter_violate.add(id)

                    # Cắt vùng hình ảnh lớn hơn bounding box của phương tiện vi phạm
                    padding = 20
                    x1_crop = max(0, x3 - padding)
                    y1_crop = max(0, y3 - padding)
                    x2_crop = min(frame.shape[1], x4 + padding)
                    y2_crop = min(frame.shape[0], y4 + padding)
                    violate_img = frame[y1_crop:y2_crop, x1_crop:x2_crop]

                    # Lưu hình ảnh vào thư mục vipham
                    violate_path = os.path.join(vipham_dir, f"violate_{id}.jpg")
                    cv2.imwrite(violate_path, violate_img)

    text_color = (255, 255, 255)
    red_color = (0, 0, 255)  # (B, G, R)

    # Vẽ đường từ các tọa độ
    cv2.line(frame, (x1_f, y1_f), (x2_f, y2_f), red_color, 3)

    # Hiển thị văn bản
    cv2.putText(frame, 'red line', (x1_f, y1_f), cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1, cv2.LINE_AA)

    wards = len(counter_violate)
    cv2.putText(frame, ('Vi pham - ') + str(wards), (60, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, red_color, 1, cv2.LINE_AA)

    cv2.imshow("frames", frame)

    output_video.write(frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
