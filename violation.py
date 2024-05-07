import cv2
import os
import pandas as pdD
from ultralytics import YOLO
from tracker import *
from detect import *

class TrafficViolationProcessor:
    def __init__(self, video_path, coordinate_file='toado.txt'):
        self.model = YOLO('yolov9e.pt')
        self.class_list = ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush']
        self.tracking_class = [2, 3, 5, 7, 9]  # car, motorcycle, bus, truck
        self.traffic_light_detector = TrafficLightDetector()
        self.tracker = Tracker()

        self.cap = cv2.VideoCapture(video_path)

        self.width = 1420
        self.height = 980
        self.conf_threshold = 0.5

        self.output_video = cv2.VideoWriter('output_video.avi', cv2.VideoWriter_fourcc(*'XVID'), 30, (self.width, self.height))

        self.vipham_dir = 'vipham'
        if not os.path.exists(self.vipham_dir):
            os.makedirs(self.vipham_dir)

        self.violate = {}
        self.traffic_light_colors = {}
        self.counter_violate = set()
        # Các phần khác của constructor
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)  # Lấy thông tin FPS của video
        self.count_frame = 0  # Thêm biến count để đếm số frame

        self.x1_f, self.y1_f, self.x2_f, self.y2_f = self.read_coordinates_from_file(coordinate_file)
        print("x1 =", self.x1_f)
        print("y1 =", self.y1_f)
        print("x2 =", self.x2_f)
        print("y2 =", self.y2_f)

    def read_coordinates_from_file(self, toado_file):
        x1_f, y1_f, x2_f, y2_f = 0, 0, 0, 0
        with open(toado_file, 'r') as file:
            lines = file.readlines()
            for line in lines:
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

    def process(self):
        violations = []  # Tạo danh sách để lưu trữ thông tin vi phạm
        count = 0
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            count += 1
            self.count_frame += 1
            second = self.count_frame / self.fps

            frame = cv2.resize(frame, (self.width, self.height))

            results = self.model.predict(frame, classes=[2, 3, 5, 7, 9], conf=self.conf_threshold)

            a = results[0].boxes.data
            a = a.detach().cpu().numpy()
            px = pd.DataFrame(a).astype("float")

            detections = []

            for index, row in px.iterrows():
                x1 = int(row[0])
                y1 = int(row[1])
                x2 = int(row[2])
                y2 = int(row[3])
                d = int(row[5])
                c = self.class_list[d]
                if d in self.tracking_class:
                    if d == 9:
                        frame, traffic_light_color = self.traffic_light_detector.detect_traffic_light_color(frame, (
                            x1, y1, x2 - x1, y2 - y1))
                        self.traffic_light_colors[(x1, y1, x2, y2)] = traffic_light_color
                    else:
                        detections.append([x1, y1, x2, y2])

            bbox_id = self.tracker.update(detections)
            if traffic_light_color in ['red', 'yellow']:
                for bbox in bbox_id:
                    x3, y3, x4, y4, id = bbox
                    cx = int(x3 + x4) // 2
                    cy = int(y3 + y4) // 2
                    cv2.rectangle(frame, (x3, y3), (x4, y4), (0, 255, 0), 2)  # Draw bounding box

                    y = self.y1_f
                    offset = 2

                    if y < (cy + offset) and y > (cy - offset):
                        self.violate[id] = cy
                        if id in self.violate:
                            cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)
                            cv2.putText(frame, str(id), (cx, cy), cv2.FONT_HERSHEY_COMPLEX, 0.8, (0, 255, 255), 2)
                            self.counter_violate.add(id)

                            padding = 50
                            x1_crop = max(0, x3 - padding)
                            y1_crop = max(0, y3 - padding)
                            x2_crop = min(frame.shape[1], x4 + padding)
                            y2_crop = min(frame.shape[0], y4 + padding)
                            violate_img = frame[y1_crop:y2_crop, x1_crop:x2_crop]

                            violation_info = f"Giây thứ {second:.2f} - Xe vượt đèn đỏ"
                            violations.append(violation_info)  # Thêm thông tin vi phạm vào danh sách

                            violate_path = os.path.join(self.vipham_dir, f"violate_{id}.jpg")
                            cv2.imwrite(violate_path, violate_img)

            text_color = (255, 255, 255)
            red_color = (0, 0, 255)  # (B, G, R)

            cv2.line(frame, (self.x1_f, self.y1_f), (self.x2_f, self.y2_f), red_color, 3)

            cv2.putText(frame, 'red line', (self.x1_f, self.y1_f), cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1,
                        cv2.LINE_AA)

            wards = len(self.counter_violate)
            cv2.putText(frame, ('Vi pham - ') + str(wards), (60, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, red_color, 1,
                        cv2.LINE_AA)

            cv2.imshow("frames", frame)

            self.output_video.write(frame)

            if cv2.waitKey(1) & 0xFF == 27:
                break

        self.cap.release()
        cv2.destroyAllWindows()

        for violation_info in violations:
            print(violation_info)  # In thông tin vi phạm ra console

        return violations
