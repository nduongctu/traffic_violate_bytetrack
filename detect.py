import cv2
import numpy as np

class TrafficLightDetector:
    def __init__(self):
        pass

    def detect_traffic_light_color(self, image, rect):
        # Trích xuất kích thước hình chữ nhật
        x, y, w, h = rect
        # Trích xuất vùng quan tâm (ROI) từ ảnh dựa trên hình chữ nhật
        roi = image[y:y + h, x:x + w]

        # Chuyển ROI sang không gian màu HSV
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        # Định nghĩa phạm vi HSV cho màu đỏ
        red_lower = np.array([0, 120, 70])
        red_upper = np.array([10, 255, 255])

        # Định nghĩa phạm vi HSV cho màu vàng
        yellow_lower = np.array([20, 100, 100])
        yellow_upper = np.array([30, 255, 255])

        # Tạo mask nhị phân để phát hiện màu đỏ và màu vàng trong ROI
        red_mask = cv2.inRange(hsv, red_lower, red_upper)
        yellow_mask = cv2.inRange(hsv, yellow_lower, yellow_upper)

        # Thông tin về font để đặt chữ lên ảnh
        font = cv2.FONT_HERSHEY_TRIPLEX
        font_scale = 1
        font_thickness = 2

        # Kiểm tra màu nào hiện diện dựa trên các mask
        if cv2.countNonZero(red_mask) > 0:
            text_color = (0, 0, 255)
            message = "Trang thai tin hieu: Do"
            color = 'red'
        elif cv2.countNonZero(yellow_mask) > 0:
            text_color = (0, 255, 255)
            message = "Trang thai tin hieu: Vang"
            color = 'yellow'
        else:
            text_color = (0, 255, 0)
            message = "Trang thai tin hieu : Xanh"
            color = 'green'

        # Chồng lớp trạng thái đè lên ảnh gốc
        cv2.putText(image, message, (15, 70), font, font_scale, text_color, font_thickness + 1, cv2.LINE_AA)
        # Trả về ảnh đã chỉnh sửa và màu được phát hiện
        return image, color