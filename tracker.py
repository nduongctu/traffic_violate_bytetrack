import math


class Tracker:
    def __init__(self):
        #lưu trữ các vị trí trung tâm của các đối tượng
        self.center_points = {}
        #giữ số lượng ID
        #mỗi khi ID đối tượng mới được phát hiện, số lượng sẽ tăng thêm một
        self.id_count = 0


    def update(self, objects_rect):
        #đối tượng boxes và id
        objects_bbs_ids = []

        #lấy điểm trung tâm của đối tượng mới
        for rect in objects_rect:
            x, y, w, h = rect
            cx = (x + x + w) // 2
            cy = (y + y + h) // 2

            #xem đối tượng đó đã được phát hiện chưa
            same_object_detected = False
            for id, pt in self.center_points.items():
                dist = math.hypot(cx - pt[0], cy - pt[1])

                if dist < 35:
                    self.center_points[id] = (cx, cy)
                    #print(self.center_points)
                    objects_bbs_ids.append([x, y, w, h, id])
                    same_object_detected = True
                    break

            #đối tượng mới được phát hiện gán ID cho đối tượng đó
            if same_object_detected is False:
                self.center_points[self.id_count] = (cx, cy)
                objects_bbs_ids.append([x, y, w, h, self.id_count])
                self.id_count += 1

        #làm sạch từ điển bằng các điểm trung tâm để loại bỏ ID không được sử dụng nữa
        new_center_points = {}
        for obj_bb_id in objects_bbs_ids:
            _, _, _, _, object_id = obj_bb_id
            center = self.center_points[object_id]
            new_center_points[object_id] = center

        #cập nhật từ điển với ID không được sử dụng bị xóa
        self.center_points = new_center_points.copy()
        return objects_bbs_ids